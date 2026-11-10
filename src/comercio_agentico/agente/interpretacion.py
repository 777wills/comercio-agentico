"""Interpretación: consulta en lenguaje natural → ``Necesidad`` formal (salida estructurada).

Una sola llamada al LLM resuelve dos cosas: los criterios (tipo de producto, especificaciones
mínimas, presupuesto, plazo) y, si el comprador nombra un producto concreto, cuál del catálogo es.
Para eso el modelo recibe los candidatos que recupera el índice de embeddings. Un GTIN o un MPN
escrito en la consulta se resuelve de forma determinista y prevalece sobre el modelo.

La consulta es del comprador (plano de control): es la única entrada de confianza del sistema.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator

from comercio_agentico.emparejamiento import Emparejador, texto_producto
from comercio_agentico.esquema import (
    AtributoComparable,
    PerfilCategoria,
    RestriccionDura,
    _todos_obligatorios,
    restriccion_canonica,
)
from comercio_agentico.modelos import invocar_estructurado

VERDADEROS = {"sí", "si", "true", "verdadero", "activa", "activo", "yes", "1", "con"}
FALSOS = {"no", "false", "falso", "inactiva", "inactivo", "desactivada", "0", "sin"}


class RestriccionAtributo(BaseModel):
    model_config = ConfigDict(json_schema_extra=_todos_obligatorios)

    atributo: str = Field(description="Nombre canónico del atributo del perfil.")
    operador: Literal[">=", "<=", "=="]
    valor: str = Field(description="Número en la unidad canónica, o la categoría (p. ej. 4K).")

    @field_validator("valor", mode="before")
    @classmethod
    def _a_texto(cls, valor: object) -> object:
        return str(valor).lower() if isinstance(valor, bool) else str(valor)

    def valor_canonico(self, atributo: AtributoComparable) -> float | str | bool:
        """Número con unidad ("16 GB", "1 TB", "27 pulgadas") → unidad canónica del perfil.

        Tolerante a la basura que escriben los modelos baratos (D75): el número es la primera
        cifra del texto (``'،27'`` → 27, ``'، 1000'`` → 1000, ``'1.000 GB'`` → 1000) y la unidad, la
        palabra que la sigue (``MB/s`` incluido). Un booleano es verdadero si el texto dice «sí»,
        «true» o «activa», falso si dice «no» o «false», y se rechaza si no dice ninguna de las dos
        cosas o dice ambas («no activa»).
        """
        texto = self.valor.strip()
        if atributo.tipo == "numero":
            numero = re.search(r"\d{1,3}(?:\.\d{3})+(?![\d.,])|\d+(?:[.,]\d+)?", texto)
            if not numero:
                raise ValueError(f"Valor no numérico para {atributo.nombre}: {texto!r}")
            cifra = numero.group(0)
            cifra = cifra.replace(".", "") if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", cifra) else cifra
            unidad = re.match(r"\s*([^\W\d_]+(?:/[^\W\d_]+)?|\")", texto[numero.end() :])
            return atributo.normalizar(
                float(cifra.replace(",", ".")), unidad.group(1) if unidad else None
            )
        if atributo.tipo == "booleano":
            palabras = set(re.findall(r"[^\W\d_]+|\d+", texto.lower()))
            si, no = bool(palabras & VERDADEROS), bool(palabras & FALSOS)
            if si != no:
                return si
            raise ValueError(f"Valor no booleano para {atributo.nombre}: {texto!r}")
        return atributo.normalizar(texto)


class Necesidad(BaseModel):
    """Campos en el orden en que el modelo debe pensarlos: primero los criterios, al final la
    identificación del producto (un esquema corto y plano lo siguen mejor los modelos baratos).
    Todos los campos son obligatorios en el esquema que ve el modelo (D69)."""

    model_config = ConfigDict(json_schema_extra=_todos_obligatorios)
    # Fuera del esquema: la interpretación falló y esta necesidad es la mínima (D69).
    _degradada: bool = PrivateAttr(default=False)

    tipo_producto: str | None = Field(default=None, description="Una de las categorías del perfil.")
    marca: str | None = None
    restricciones: list[RestriccionAtributo] = Field(
        default_factory=list, description="Especificaciones mínimas o máximas que pide la consulta."
    )
    presupuesto_max: float | None = Field(
        default=None, description="Tope en COP sobre precio + envío; null si no lo da."
    )
    plazo_max_dias: int | None = Field(default=None, description="null si no da un plazo.")
    producto_mencionado: str | None = Field(
        default=None,
        description="Producto concreto (marca y modelo) que nombra el comprador; null si describe "
        "una necesidad general.",
    )
    producto_id: str | None = Field(
        default=None,
        description="ID del candidato que es exactamente el producto mencionado; null si no hay.",
    )

    @field_validator("presupuesto_max", "plazo_max_dias")
    @classmethod
    def _cero_es_nulo(cls, valor: float | None) -> float | None:
        return valor if valor else None

    @property
    def degradada(self) -> bool:
        return self._degradada

    def restricciones_duras(self, perfil: PerfilCategoria) -> list[RestriccionDura]:
        """Lleva cada restricción al nombre y la unidad canónicos del perfil; descarta las que no
        reconoce."""
        duras = []
        for r in self.restricciones:
            try:
                atributo = perfil.atributo(r.atributo)
                valor = r.valor_canonico(atributo)
            except (KeyError, ValueError):
                continue
            duras.append(restriccion_canonica(atributo, r.operador, valor))
        return duras


INSTRUCCIONES = """Formalizas la consulta de un comprador de electrónica en Colombia.

Categorías (tipo_producto): {categorias}.
Atributos comparables (nombre canónico y unidad): {atributos}.

Reglas:
- Toda especificación mínima o máxima de la consulta va en restricciones, con el nombre y la \
unidad canónicos. Una necesidad sin cifras se traduce a una cifra razonable ("liviano" en un \
portátil → peso <= 1.6). No inventes restricciones que la consulta no sugiere.
- presupuesto_max: el tope de dinero en pesos, si lo hay. plazo_max_dias: si pide un plazo.
- Si nombra un producto concreto (marca y modelo), cópialo en producto_mencionado y elige en \
producto_id el candidato que sea exactamente ese producto, con la misma variante de memoria, \
capacidad o tamaño. Si ningún candidato lo es, producto_id = null.

Ejemplos:
- "¿Dónde compro más barato el Samsung Galaxy A56 5G 8/256?" → tipo_producto celular, marca \
Samsung, producto_mencionado "Samsung Galaxy A56 5G 8/256", producto_id del candidato idéntico.
- "Busco un monitor de al menos 27 pulgadas, máximo $1.500.000 con envío, que llegue en 5 días" → \
tipo_producto monitor, restricciones [tamano_pantalla >= 27], presupuesto_max 1500000, \
plazo_max_dias 5, producto_mencionado null."""


def _formato_perfil(perfil: PerfilCategoria) -> tuple[str, str]:
    tipo = perfil.atributo("tipo_producto")
    categorias = ", ".join(tipo.valores)
    atributos = ", ".join(
        f"{a.nombre} ({a.unidad})" if a.unidad else a.nombre
        for a in perfil.atributos
        if a.nombre != "tipo_producto"
    )
    return categorias, atributos


async def interpretar(
    consulta: str,
    estructurado: Any,
    emparejador: Emparejador,
    perfil: PerfilCategoria,
    config: dict | None = None,
) -> Necesidad:
    """``estructurado`` es ``obtener_extractor(modelo, Necesidad)``. Nunca falla por una salida
    inválida del modelo: reintenta una vez y, si no, devuelve una necesidad mínima marcada."""
    candidatos = emparejador.candidatos([consulta])[0]
    categorias, atributos = _formato_perfil(perfil)
    lista = "\n".join(f"- {c.id}: {texto_producto(c)}" for c in candidatos)
    mensajes = [
        SystemMessage(INSTRUCCIONES.format(categorias=categorias, atributos=atributos)),
        HumanMessage(f"Consulta: {consulta}\n\nCandidatos del catálogo:\n{lista}"),
    ]
    salida = await invocar_estructurado(estructurado, mensajes, config)
    if salida is None:
        # Degradación controlada: sin criterios, pero los identificadores escritos en la consulta
        # todavía se resuelven abajo; la propuesta advierte que la necesidad está incompleta.
        necesidad = Necesidad()
        necesidad._degradada = True
    else:
        necesidad = Necesidad.model_validate(salida) if isinstance(salida, dict) else salida

    validos = {c.id for c in candidatos}
    if necesidad.producto_id not in validos:
        necesidad.producto_id = None
    # Un identificador escrito por el comprador es evidencia más fuerte que el modelo.
    gtins = re.findall(r"\b\d{8,14}\b", consulta)
    mpns = [m for m in emparejador.por_mpn if m and m in consulta.lower()]
    for gtin in gtins:
        if directo := emparejador.por_identificador(gtin, None):
            necesidad.producto_id = directo
            break
    else:
        for mpn in mpns:
            if directo := emparejador.por_identificador(None, mpn):
                necesidad.producto_id = directo
                break
    if necesidad.producto_id and not necesidad.producto_mencionado:
        necesidad.producto_mencionado = emparejador.por_id[necesidad.producto_id].titulo
    if necesidad.tipo_producto:
        try:
            necesidad.tipo_producto = str(
                perfil.atributo("tipo_producto").normalizar(necesidad.tipo_producto)
            )
        except ValueError:
            necesidad.tipo_producto = None
    return necesidad
