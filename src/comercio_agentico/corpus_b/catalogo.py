"""Catálogo de referencia del corpus B: ~40 productos de electrónica generados con un LLM barato.

El LLM propone productos verosímiles (marca, modelo, atributos, precio de referencia y la forma en
que cada tipo de proveedor los nombraría). El código hace lo que el LLM hace mal: asigna el GTIN-13
con su dígito de control y valida cada atributo contra el perfil de categoría. El resultado se
congela en ``catalogo.json`` y se versiona: regenerarlo es opcional y cuesta centavos.

Uso: ``uv run python -m comercio_agentico.corpus_b.catalogo [--modelo deepseek-flash]``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from comercio_agentico.corpus_b import RUTA_CATALOGO, RUTA_PERFIL
from comercio_agentico.esquema import (
    PerfilCategoria,
    ValorAtributo,
    cargar_perfil,
    gtin_valido,
)

Categoria = Literal["portatil", "monitor", "celular", "audifonos", "almacenamiento"]

# Atributos obligatorios por categoría, con su valor en la unidad canónica del perfil.
ATRIBUTOS_POR_CATEGORIA: dict[str, list[str]] = {
    "portatil": ["procesador", "memoria_ram", "almacenamiento", "tamano_pantalla", "peso"],
    "monitor": ["tamano_pantalla", "resolucion", "tipo_panel", "frecuencia_refresco"],
    "celular": ["memoria_ram", "almacenamiento", "tamano_pantalla", "bateria"],
    "audifonos": ["cancelacion_ruido", "inalambrico", "autonomia"],
    "almacenamiento": ["tipo_almacenamiento", "almacenamiento", "velocidad_lectura"],
}
PRODUCTOS_POR_CATEGORIA = 8

# Prefijo GS1 de circulación restringida (uso interno): no choca con productos reales.
PREFIJO_GTIN = "200"


class ProductoGenerado(BaseModel):
    """Lo que propone el LLM para un producto."""

    marca: str
    modelo: str = Field(description="Nombre de modelo comercial, p. ej. 'IdeaPad Slim 3 15IRH8'.")
    mpn: str = Field(description="Referencia del fabricante (part number) verosímil.")
    titulo: str = Field(description="Título completo como en una ficha técnica oficial.")
    precio_referencia_cop: int = Field(gt=0, description="Precio de lista en Colombia, en COP.")
    atributos: dict[str, ValorAtributo] = Field(
        description="Atributos técnicos en la unidad canónica indicada."
    )
    alias_comercial: str = Field(description="Nombre de vitrina, comercial, sin referencia exacta.")
    alias_pdf: str = Field(description="Descripción abreviada en mayúsculas de lista mayorista.")
    alias_mensaje: str = Field(description="Cómo lo escribiría un vendedor por WhatsApp.")


class LoteProductos(BaseModel):
    productos: list[ProductoGenerado]


class ProductoCatalogo(ProductoGenerado):
    """Producto validado del catálogo de referencia."""

    id: str = Field(pattern=r"^C\d{2}$")
    categoria: Categoria
    gtin: str

    @model_validator(mode="after")
    def _gtin(self) -> ProductoCatalogo:
        if not gtin_valido(self.gtin) or len(self.gtin) != 13:
            raise ValueError(f"GTIN-13 inválido en {self.id}: {self.gtin}")
        return self


def gtin13(numero: int) -> str:
    """GTIN-13 sintético: prefijo restringido + 9 dígitos + dígito de control."""
    cuerpo = f"{PREFIJO_GTIN}{numero:09d}"
    suma = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(cuerpo)))
    return cuerpo + str((10 - suma % 10) % 10)


def validar_producto(producto: ProductoCatalogo, perfil: PerfilCategoria) -> None:
    """Exige los atributos de la categoría y que cada uno se normalice sin cambiar de valor."""
    requeridos = set(ATRIBUTOS_POR_CATEGORIA[producto.categoria])
    faltan = requeridos - set(producto.atributos)
    if faltan:
        raise ValueError(f"{producto.id} sin atributos {sorted(faltan)}")
    for nombre, valor in producto.atributos.items():
        atributo = perfil.atributo(nombre)
        if atributo.nombre != nombre:
            raise ValueError(f"{producto.id}: use el nombre canónico {atributo.nombre!r}")
        normalizado = atributo.normalizar(valor)
        if atributo.tipo == "numero" and float(valor) != normalizado:
            raise ValueError(f"{producto.id}: {nombre}={valor} no está en la unidad canónica")
        if atributo.tipo == "categoria" and valor != normalizado:
            raise ValueError(f"{producto.id}: {nombre}={valor!r} debe ser {normalizado!r}")


def validar_catalogo(productos: list[ProductoCatalogo], perfil: PerfilCategoria) -> None:
    for p in productos:
        validar_producto(p, perfil)
    for campo in ("id", "gtin", "mpn", "titulo"):
        valores = [getattr(p, campo) for p in productos]
        if len(set(valores)) != len(valores):
            raise ValueError(f"Valores repetidos en el campo {campo!r} del catálogo")


def cargar_catalogo(ruta: Path = RUTA_CATALOGO) -> list[ProductoCatalogo]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return [ProductoCatalogo.model_validate(p) for p in datos["productos"]]


# --------------------------------------------------------------------------------------------------
# Generación con LLM


def _instrucciones(categoria: str, perfil: PerfilCategoria) -> str:
    lineas = []
    for nombre in ATRIBUTOS_POR_CATEGORIA[categoria]:
        a = perfil.atributo(nombre)
        if a.tipo == "numero":
            lineas.append(f"- {nombre}: número en {a.unidad}")
        elif a.tipo == "categoria":
            lineas.append(f"- {nombre}: uno de {list(a.valores)}")
        elif a.tipo == "booleano":
            lineas.append(f"- {nombre}: true o false")
        else:
            lineas.append(f"- {nombre}: texto")
    atributos = "\n".join(lineas)
    return f"""Genera {PRODUCTOS_POR_CATEGORIA} productos de la categoría "{categoria}" para un
catálogo de referencia de una tienda de electrónica en Colombia (noviembre de 2026).

Reglas:
- Marcas reales y modelos verosímiles; al menos 5 marcas distintas.
- Incluye exactamente un par de variantes del mismo modelo que difieran solo en memoria o
  capacidad (mismo nombre de modelo con sufijo distinto), para probar el emparejamiento.
- Rango de precios amplio: desde gama de entrada hasta gama alta. Precio en pesos colombianos,
  entero, IVA incluido.
- "atributos" debe tener exactamente estas claves, con el valor en la unidad indicada:
{atributos}
- alias_comercial: nombre de vitrina como en una tienda en línea pequeña (sin part number).
- alias_pdf: descripción abreviada en MAYÚSCULAS de lista de precios mayorista, máximo 45
  caracteres (p. ej. "PORT LEN IDEAPAD S3 R5 8/512 15.6").
- alias_mensaje: como lo escribiría un vendedor informal por WhatsApp, en minúsculas y con
  abreviaturas (p. ej. "lenovo ideapad ryzen5 8/512").
- Ningún título, mpn ni alias repetido."""


def reparar(producto: dict, categoria: str) -> dict:
    """Correcciones deterministas a lo que el LLM suele hacer mal.

    - Quita de ``atributos`` las claves que no pide la categoría (el LLM a veces copia ahí los
      alias).
    - Los fabricantes de discos usan TB decimales (1 TB = 1000 GB); el perfil convierte 1 TB a
      1024 GB, así que las capacidades múltiplo de 1000 se pasan a esa convención.
    """
    requeridos = ATRIBUTOS_POR_CATEGORIA[categoria]
    atributos = {k: v for k, v in producto["atributos"].items() if k in requeridos}
    capacidad = atributos.get("almacenamiento")
    if isinstance(capacidad, int | float) and capacidad >= 1000 and capacidad % 1000 == 0:
        atributos["almacenamiento"] = int(capacidad // 1000 * 1024)
    return {**producto, "atributos": atributos}


def _guardar(productos: list[ProductoCatalogo], ruta: Path, modelo: str, costo: float) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {
        "modelo_generador": modelo,
        "costo_usd": round(costo, 5),
        "productos": [p.model_dump() for p in productos],
    }
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generar(modelo: str = "deepseek-flash", ruta: Path = RUTA_CATALOGO) -> list[ProductoCatalogo]:
    from comercio_agentico.modelos import RegistroCosto, obtener_extractor

    perfil = cargar_perfil(RUTA_PERFIL)
    extractor = obtener_extractor(modelo, LoteProductos)
    registro = RegistroCosto(tope_usd=0.20)
    productos: list[ProductoCatalogo] = []
    for categoria in ATRIBUTOS_POR_CATEGORIA:
        lote: LoteProductos = extractor.invoke(
            _instrucciones(categoria, perfil), config={"callbacks": [registro]}
        )
        for generado in lote.productos[:PRODUCTOS_POR_CATEGORIA]:
            n = len(productos) + 1
            datos = reparar(generado.model_dump(), categoria)
            productos.append(
                ProductoCatalogo(**datos, id=f"C{n:02d}", categoria=categoria, gtin=gtin13(n))
            )
        print(f"{categoria}: {len(lote.productos)} productos")
    # Se guarda antes de validar para no perder la llamada pagada si algo falla.
    _guardar(productos, ruta, modelo, registro.costo_total)
    validar_catalogo(productos, perfil)
    print(f"{len(productos)} productos en {ruta} · costo US${registro.costo_total:.4f}")
    return productos


def reparar_archivo(ruta: Path = RUTA_CATALOGO) -> None:
    """Aplica ``reparar`` a un catálogo ya generado, sin volver a llamar al LLM."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    productos = [
        ProductoCatalogo.model_validate(reparar(p, p["categoria"])) for p in datos["productos"]
    ]
    validar_catalogo(productos, cargar_perfil(RUTA_PERFIL))
    _guardar(productos, ruta, datos["modelo_generador"], datos["costo_usd"])
    print(f"{len(productos)} productos reparados y validados en {ruta}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", default="deepseek-flash")
    parser.add_argument("--reparar", action="store_true", help="Solo repara y valida (US$0).")
    argumentos = parser.parse_args()
    if argumentos.reparar:
        reparar_archivo()
    else:
        generar(argumentos.modelo)
