"""Emparejamiento de ofertas con el catálogo de referencia (D15).

Orden de evidencia, de más a menos fuerte:

1. **GTIN exacto** (validado por dígito de control) o **MPN exacto**: determinista, sin LLM.
2. **Recuperación densa**: embeddings del catálogo (solo del catálogo, en memoria) y los ``k`` más
   parecidos al título de la oferta, con un modelo multilingüe local (``multilingual-e5-small``).
3. **Confirmación del LLM**: elige entre esos candidatos el producto idéntico (misma variante) o
   responde ``null``. Una respuesta fuera de los candidatos también cuenta como abstención.

Los embeddings preseleccionan; no deciden. Variantes como un monitor de 32 GB frente al de 64 GB
quedan casi empatadas en similitud coseno, y solo la lectura atenta del LLM las separa.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

import numpy as np
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field

from comercio_agentico.corpus_b.catalogo import ProductoCatalogo
from comercio_agentico.esquema import Oferta, _todos_obligatorios
from comercio_agentico.modelos import invocar_estructurado

MODELO_EMBEDDINGS = "intfloat/multilingual-e5-small"  # MIT, 118 M parámetros, CPU


class Codificador(Protocol):
    def __call__(self, textos: list[str], *, consulta: bool) -> np.ndarray: ...


class CodificadorE5:
    """multilingual-e5 exige los prefijos ``query:`` y ``passage:`` (ficha del modelo)."""

    def __init__(self, nombre: str = MODELO_EMBEDDINGS) -> None:
        from sentence_transformers import SentenceTransformer

        self.modelo = SentenceTransformer(nombre, device="cpu")

    def __call__(self, textos: list[str], *, consulta: bool) -> np.ndarray:
        prefijo = "query: " if consulta else "passage: "
        return self.modelo.encode(
            [prefijo + t for t in textos], normalize_embeddings=True, show_progress_bar=False
        )


_CODIFICADOR: CodificadorE5 | None = None


def codificador_e5() -> CodificadorE5:
    """Carga perezosa y única: el modelo tarda unos segundos en subir a memoria."""
    global _CODIFICADOR
    if _CODIFICADOR is None:
        _CODIFICADOR = CodificadorE5()
    return _CODIFICADOR


def texto_producto(p: ProductoCatalogo) -> str:
    return f"{p.titulo} ({p.marca} {p.modelo}, {p.categoria})"


def texto_oferta(o: Oferta) -> str:
    partes = [o.titulo, o.marca or "", o.modelo or ""]
    return " ".join(p for p in partes if p)


# --------------------------------------------------------------------------------------------------
# Confirmación con LLM


class Decision(BaseModel):
    model_config = ConfigDict(json_schema_extra=_todos_obligatorios)

    oferta: int = Field(description="Número de la oferta.")
    producto_id: str | None = Field(
        description="ID del candidato que es exactamente el mismo producto, o null si ninguno."
    )


class Decisiones(BaseModel):
    model_config = ConfigDict(json_schema_extra=_todos_obligatorios)

    decisiones: list[Decision] = Field(default_factory=list)


INSTRUCCIONES_CONFIRMAR = """Emparejas ofertas de proveedores con un catálogo de referencia. Para \
cada oferta recibes sus candidatos más parecidos del catálogo. Elige el candidato que sea \
exactamente el mismo producto: misma marca, modelo y variante (memoria, capacidad, tamaño, \
generación). Las abreviaturas de los proveedores son normales ("16/512" = 16 GB de RAM y 512 GB \
de almacenamiento). Si ningún candidato es el mismo producto, o si dudas, responde null: un \
emparejamiento equivocado es peor que ninguno. Responde una decisión por oferta."""


def _bloque(i: int, texto: str, candidatos: Sequence[ProductoCatalogo]) -> str:
    lineas = [f"Oferta {i}: {texto}"]
    lineas += [f"  - {c.id}: {texto_producto(c)}" for c in candidatos]
    return "\n".join(lineas)


class Emparejador:
    def __init__(
        self,
        catalogo: Sequence[ProductoCatalogo],
        codificador: Codificador | None = None,
        k: int = 5,
    ) -> None:
        self.catalogo = list(catalogo)
        self.k = k
        self.codificar = codificador or codificador_e5()
        self.por_id = {p.id: p for p in self.catalogo}
        self.por_gtin = {p.gtin: p.id for p in self.catalogo}
        self.por_mpn = {p.mpn.strip().lower(): p.id for p in self.catalogo if p.mpn}
        # Índice vectorial en memoria, recalculado en cada ingesta (D15).
        self.matriz = self.codificar([texto_producto(p) for p in self.catalogo], consulta=False)

    def candidatos(self, textos: list[str]) -> list[list[ProductoCatalogo]]:
        if not textos:
            return []
        similitudes = self.codificar(textos, consulta=True) @ self.matriz.T
        return [[self.catalogo[j] for j in np.argsort(-fila)[: self.k]] for fila in similitudes]

    def por_identificador(self, gtin: str | None, mpn: str | None) -> str | None:
        if gtin and gtin in self.por_gtin:
            return self.por_gtin[gtin]
        if mpn and mpn.strip().lower() in self.por_mpn:
            return self.por_mpn[mpn.strip().lower()]
        return None

    async def emparejar(
        self, ofertas: list[Oferta], confirmador: Any, config: dict | None = None
    ) -> list[Oferta]:
        """Devuelve copias de las ofertas con ``producto_catalogo`` asignado (o None).

        ``confirmador`` es ``obtener_extractor(modelo, Decisiones)``: una sola llamada por lote.
        """
        asignado: dict[int, str | None] = {}
        pendientes: list[int] = []
        for i, o in enumerate(ofertas):
            directo = self.por_identificador(o.gtin, o.mpn)
            if directo:
                asignado[i] = directo
            else:
                pendientes.append(i)

        if pendientes:
            textos = [texto_oferta(ofertas[i]) for i in pendientes]
            listas = self.candidatos(textos)
            prompt = "\n\n".join(
                _bloque(n, t, c) for n, (t, c) in enumerate(zip(textos, listas, strict=True))
            )
            salida = await invocar_estructurado(
                confirmador, [SystemMessage(INSTRUCCIONES_CONFIRMAR), HumanMessage(prompt)], config
            )
            # Si la salida no parsea ni al reintentar, las ofertas quedan sin emparejar (y la
            # propuesta lo advierte con la alerta de emparejamiento dudoso).
            salida = Decisiones() if salida is None else salida
            decisiones = Decisiones.model_validate(salida) if isinstance(salida, dict) else salida
            for d in decisiones.decisiones:
                if 0 <= d.oferta < len(pendientes):
                    validos = {c.id for c in listas[d.oferta]}
                    asignado[pendientes[d.oferta]] = (
                        d.producto_id if d.producto_id in validos else None
                    )

        return [
            o.model_copy(update={"producto_catalogo": asignado.get(i)})
            for i, o in enumerate(ofertas)
        ]


if __name__ == "__main__":  # demostración sin LLM ni costo: `make candidatos`
    from comercio_agentico.corpus_b.catalogo import cargar_catalogo

    ejemplos = [
        "samsung smart m8 m80d 32 4k qled 32gb",  # P5: variante de 32 GB
        "MON SAMS SMART M8 M80D 32 4K QLED 64GB",  # P4: variante de 64 GB
        "PORT ASUS VIVOBOOK15 X1504 I5 16/512",  # P4
        "tengo ssd adata su650 512gb en 170 mil",  # P5
        "consola PlayStation 6 Pro",  # fuera del catálogo
    ]
    emparejador = Emparejador(cargar_catalogo())
    similitudes = emparejador.codificar(ejemplos, consulta=True) @ emparejador.matriz.T
    for texto, fila in zip(ejemplos, similitudes, strict=True):
        print(f"\n{texto}")
        for j in np.argsort(-fila)[:3]:
            p = emparejador.catalogo[j]
            print(f"  {fila[j]:.3f}  {p.id}  {p.titulo}")
