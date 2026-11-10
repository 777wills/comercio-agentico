"""Esquema canónico: el contrato único de fuente con procedencia obligatoria (D10).

- ``OfertaExtraida``: lo que el LLM devuelve con salida estructurada. Inspirada en schema.org
  ``Product`` + ``Offer``.
- ``Procedencia``: la escribe el código, nunca el modelo; ata cada oferta al fragmento original del
  que salió.
- ``Oferta``: ``OfertaExtraida`` + ``Procedencia``. Es lo único que circula aguas abajo.
- ``PerfilCategoria``: atributos comparables, restricciones duras, normalización de unidades e
  identificador de emparejamiento, declarados en YAML (``perfiles/*.yaml``) para que cambiar de
  dominio no toque código.
- ``PropuestaCompra``: salida final del agente; trazable y con abstención explícita. No ejecuta
  pagos.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# --------------------------------------------------------------------------------------------------
# Identificadores


def gtin_valido(codigo: str) -> bool:
    """Valida un GTIN-8/12/13/14 por su dígito de control (módulo 10 de GS1)."""
    if not codigo.isdigit() or len(codigo) not in (8, 12, 13, 14):
        return False
    *cuerpo, control = (int(d) for d in codigo)
    suma = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(cuerpo)))
    return (10 - suma % 10) % 10 == control


def suma_verificacion(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------------------
# Oferta y procedencia

TipoFuente = Literal["mcp", "web_schema", "web_plana", "pdf", "mensaje", "api"]
RutaExtraccion = Literal["determinista", "llm", "reextraccion"]
Disponibilidad = Literal["en_stock", "bajo_pedido", "agotado", "desconocida"]
ValorAtributo = str | float | int | bool


def _todos_obligatorios(esquema: dict) -> None:
    """En el JSON Schema que recibe el LLM, todo campo es obligatorio (anulable si su tipo lo
    admite). Sin esto, un modelo puede omitir los opcionales aunque la fuente los publique: DeepSeek
    Flash omitía GTIN, MPN y marca en el 100 % de las ofertas (S03). La validación de Pydantic no
    cambia: los valores por defecto siguen valiendo al construir ofertas en el código."""
    esquema["required"] = list(esquema.get("properties", {}))


class OfertaExtraida(BaseModel):
    """Oferta tal como la extrae el modelo de un fragmento (la procedencia la pone el código)."""

    model_config = ConfigDict(str_strip_whitespace=True, json_schema_extra=_todos_obligatorios)

    titulo: str = Field(
        min_length=1, description="Nombre del producto tal como aparece en la fuente."
    )
    precio: float = Field(gt=0, description="Precio final por unidad, sin separadores de miles.")
    moneda: str = Field(default="COP", pattern=r"^[A-Z]{3}$", description="Código ISO 4217.")
    gtin: str | None = Field(
        default=None, description="GTIN/EAN si aparece en la fuente; si no, null."
    )
    mpn: str | None = Field(default=None, description="Referencia del fabricante, si aparece.")
    marca: str | None = None
    modelo: str | None = None
    disponibilidad: Disponibilidad = "desconocida"
    costo_envio: float | None = Field(
        default=None, ge=0, description="null si la fuente no lo indica."
    )
    plazo_entrega_dias: int | None = Field(default=None, ge=0)
    condiciones_entrega: str | None = None
    atributos: dict[str, ValorAtributo] = Field(
        default_factory=dict,
        description="Atributos técnicos con su valor y unidad tal como aparecen en la fuente.",
    )
    url_detalle: str | None = Field(
        default=None, description="Enlace a la ficha del producto, si aparece en el fragmento."
    )

    @field_validator("gtin", mode="before")
    @classmethod
    def _limpiar_gtin(cls, valor: object) -> object:
        if isinstance(valor, str):
            valor = valor.replace(" ", "").replace("-", "") or None
        return valor

    @field_validator("gtin")
    @classmethod
    def _validar_gtin(cls, valor: str | None) -> str | None:
        if valor is not None and not gtin_valido(valor):
            raise ValueError(f"GTIN inválido (dígito de control): {valor}")
        return valor


class ListaOfertas(BaseModel):
    """Salida estructurada: un fragmento puede contener varias ofertas o ninguna."""

    ofertas: list[OfertaExtraida] = Field(default_factory=list)


class Procedencia(BaseModel):
    """De dónde salió una oferta. Permite re-extraer (N3) y auditar cualquier cifra."""

    fuente: str = Field(description="Identificador del proveedor o URL.")
    tipo_fuente: TipoFuente
    consulta: str = Field(description="Consulta o herramienta que produjo el fragmento.")
    marca_tiempo: datetime = Field(default_factory=lambda: datetime.now(UTC))
    fragmento_original: str = Field(min_length=1)
    ruta_extraccion: RutaExtraccion
    modelo_extraccion: str | None = Field(
        default=None, description="Nombre corto del LLM, si hubo."
    )
    suma_verificacion: str = Field(default="", description="SHA-256 del fragmento original.")

    @model_validator(mode="after")
    def _sellar(self) -> Self:
        esperada = suma_verificacion(self.fragmento_original)
        if not self.suma_verificacion:
            self.suma_verificacion = esperada
        elif self.suma_verificacion != esperada:
            raise ValueError("La suma de verificación no corresponde al fragmento original")
        if self.ruta_extraccion != "determinista" and not self.modelo_extraccion:
            raise ValueError("Una extracción con LLM debe registrar el modelo")
        return self


class Oferta(OfertaExtraida):
    procedencia: Procedencia
    producto_catalogo: str | None = Field(
        default=None,
        description="ID del catálogo de referencia; lo escribe el emparejamiento, nunca el LLM.",
    )
    verificacion: Literal["verificada", "discrepancia", "sin_contraparte"] | None = Field(
        default=None, description="Resultado de N3; null si no se verificó."
    )

    @property
    def proveedor(self) -> str:
        return self.procedencia.fuente

    @property
    def costo_total(self) -> float:
        return self.precio + (self.costo_envio or 0.0)


# --------------------------------------------------------------------------------------------------
# Perfil de categoría

TipoAtributo = Literal["numero", "texto", "categoria", "booleano"]
Operador = Literal["==", "!=", ">=", "<=", "en"]


class AtributoComparable(BaseModel):
    nombre: str
    tipo: TipoAtributo
    unidad: str | None = Field(
        default=None, description="Unidad canónica (solo atributos numéricos)."
    )
    conversiones: dict[str, float] = Field(
        default_factory=dict, description="Factor para llevar cada unidad a la canónica."
    )
    sinonimos: list[str] = Field(default_factory=list, description="Otros nombres del atributo.")
    valores: dict[str, list[str]] = Field(
        default_factory=dict, description="Categorías canónicas y sus variantes de escritura."
    )
    mayor_es_mejor: bool | None = None

    @model_validator(mode="after")
    def _coherente(self) -> Self:
        if self.tipo == "numero" and not self.unidad:
            raise ValueError(f"El atributo numérico {self.nombre!r} necesita unidad canónica")
        if self.tipo != "numero" and self.conversiones:
            raise ValueError(f"Solo los atributos numéricos llevan conversiones ({self.nombre!r})")
        return self

    def normalizar(self, valor: ValorAtributo, unidad: str | None = None) -> ValorAtributo:
        """Lleva un valor a la unidad o categoría canónica; error si no se reconoce."""
        if self.tipo == "numero":
            unidad = (unidad or self.unidad or "").strip().lower()
            canonica = (self.unidad or "").lower()
            factor = 1.0 if unidad == canonica else self.conversiones.get(unidad)
            if factor is None:
                raise ValueError(f"Unidad {unidad!r} no reconocida para {self.nombre!r}")
            return round(float(valor) * factor, 4)
        if self.tipo == "categoria":
            texto = str(valor).strip().lower()
            for canonico, variantes in self.valores.items():
                if texto == canonico.lower() or texto in (v.lower() for v in variantes):
                    return canonico
            raise ValueError(f"Valor {valor!r} no reconocido para {self.nombre!r}")
        if self.tipo == "booleano":
            if isinstance(valor, bool):
                return valor
            return str(valor).strip().lower() in {"sí", "si", "true", "1", "yes"}
        return str(valor).strip()


def restriccion_canonica(
    atributo: AtributoComparable, operador: Operador, valor: ValorAtributo
) -> RestriccionDura:
    """En una categoría ordenada (``mayor_es_mejor`` con los valores de menor a mayor), ">= 4K" es
    "en [4K, 8K]"; en una categoría sin orden, un >= o <= se lee como igualdad."""
    if atributo.tipo == "categoria" and operador in (">=", "<="):
        orden = list(atributo.valores)
        if atributo.mayor_es_mejor is not None and valor in orden:
            i = orden.index(valor)
            tramo = orden[i:] if operador == ">=" else orden[: i + 1]
            return RestriccionDura(atributo=atributo.nombre, operador="en", valor=tramo)
        operador = "=="
    return RestriccionDura(atributo=atributo.nombre, operador=operador, valor=valor)


class RestriccionDura(BaseModel):
    atributo: str
    operador: Operador
    valor: ValorAtributo | list[ValorAtributo]

    def cumple(self, valor: ValorAtributo | None) -> bool:
        if valor is None:
            return False
        objetivo = self.valor
        match self.operador:
            case "==":
                return valor == objetivo
            case "!=":
                return valor != objetivo
            case ">=" | "<=":
                try:
                    a, b = float(valor), float(objetivo)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    return False  # un orden entre textos no se puede verificar
                return a >= b if self.operador == ">=" else a <= b
            case "en":
                return valor in (objetivo if isinstance(objetivo, list) else [objetivo])
        return False


class PerfilCategoria(BaseModel):
    nombre: str
    descripcion: str = ""
    identificador_emparejamiento: list[Literal["gtin", "mpn", "marca_modelo"]] = Field(min_length=1)
    atributos: list[AtributoComparable] = Field(min_length=1)
    restricciones_duras: list[RestriccionDura] = Field(default_factory=list)

    @model_validator(mode="after")
    def _referencias(self) -> Self:
        nombres = [a.nombre for a in self.atributos]
        if len(set(nombres)) != len(nombres):
            raise ValueError("Atributos repetidos en el perfil")
        campos_oferta = set(OfertaExtraida.model_fields)
        for r in self.restricciones_duras:
            if r.atributo not in nombres and r.atributo not in campos_oferta:
                raise ValueError(f"La restricción usa un atributo inexistente: {r.atributo!r}")
        return self

    def atributo(self, nombre: str) -> AtributoComparable:
        """Busca un atributo por nombre canónico o sinónimo, sin distinguir mayúsculas."""
        clave = nombre.strip().lower()
        for a in self.atributos:
            if clave == a.nombre.lower() or clave in (s.lower() for s in a.sinonimos):
                return a
        raise KeyError(f"Atributo no definido en el perfil {self.nombre!r}: {nombre!r}")


def cargar_perfil(ruta: str | Path) -> PerfilCategoria:
    with Path(ruta).open(encoding="utf-8") as archivo:
        return PerfilCategoria.model_validate(yaml.safe_load(archivo))


# --------------------------------------------------------------------------------------------------
# Propuesta de compra

TipoAlerta = Literal[
    "posible_inyeccion",
    "precio_atipico",
    "sin_verificar",
    "emparejamiento_dudoso",
    "restriccion_incumplida",
    "fuente_no_disponible",
    "interpretacion_incompleta",
]


class Alerta(BaseModel):
    tipo: TipoAlerta
    mensaje: str
    oferta: int | None = Field(default=None, description="Índice de la oferta afectada, si aplica.")


class PropuestaCompra(BaseModel):
    """Cuadro comparativo con procedencia, una recomendación (o abstención) y alertas."""

    consulta: str
    perfil: str
    ofertas: list[Oferta] = Field(default_factory=list)
    recomendada: int | None = Field(
        default=None, description="Índice en `ofertas`; null si se abstiene."
    )
    justificacion: str = ""
    abstencion: bool = False
    motivo_abstencion: str | None = None
    alertas: list[Alerta] = Field(default_factory=list)
    modelo: str | None = None
    costo_usd: float = Field(default=0.0, ge=0)
    marca_tiempo: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def _coherente(self) -> Self:
        if self.abstencion:
            if self.recomendada is not None:
                raise ValueError("Una abstención no puede recomendar una oferta")
            if not self.motivo_abstencion:
                raise ValueError("La abstención debe explicar su motivo")
        elif self.recomendada is None:
            raise ValueError("Sin abstención debe haber una oferta recomendada")
        indices = [self.recomendada] + [a.oferta for a in self.alertas]
        for i in indices:
            if i is not None and not 0 <= i < len(self.ofertas):
                raise ValueError(f"Índice de oferta fuera de rango: {i}")
        return self
