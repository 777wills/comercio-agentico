"""Tareas del corpus A: 20 consultas sobre las tiendas reales reconstruidas (S04).

La respuesta de cada tarea la calcula ``calcular_respuesta`` (la misma del corpus B) sobre
``verdad.json``; aquí solo se escriben la consulta y los criterios. Cada grupo prueba algo
concreto de las tiendas reales:

- Falabella no publica GTIN: el emparejamiento con ella es por nombre (R03, R12, R13, R14, R17).
- R12 y R13 solo tienen existencias en Falabella; en R13 el menor precio exige la tarjeta CMR.
- En R04 todo está agotado, pero Falabella tiene en existencia un producto parecido (X1 Yoga).

Uso: ``uv run python -m comercio_agentico.corpus_a.tareas`` (US$0, sin red).
"""

from __future__ import annotations

import json

from comercio_agentico.corpus_a.construir import RUTA_CATALOGO_A, RUTA_VERDAD_A
from comercio_agentico.corpus_b import RAIZ, RUTA_PERFIL
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.corpus_b.tareas import Criterios, Tarea, calcular_respuesta
from comercio_agentico.esquema import RestriccionDura, cargar_perfil, restriccion_canonica

RUTA_TAREAS_A = RAIZ / "tareas" / "tareas_a.jsonl"

ESPECIFICAS = {
    "R03": "el iPhone 15 de 128 GB",
    "R12": "el monitor Kalley Gamer M27G180 de 27 pulgadas",
    "R13": "el monitor Acer ED270 de 27 pulgadas curvo",
    "R14": "el monitor HP OMEN 32C QHD",
    "R17": "los audífonos de diadema Kalley K-KGA1",
    "R22": "el SSD externo Kingston XS1000 de 1 TB",
}
MAS_BARATO = {
    "R16": "los audífonos Esenses HP-1000",
    "R19": "la microSD Kingston Canvas Select Plus de 256 GB",
    "R11": "el monitor Samsung ViewFinity D700 de 32 pulgadas",
    "R24": "la unidad de estado sólido Kingston de 480 GB",
    "R05": "el portátil ASUS Zenbook A 14 UX3407QA",
}
SIN_RESPUESTA = {
    "R08": "el portátil ASUS Zenbook S14 UX5406SA con 32 GB de RAM",
    "R04": "el portátil Lenovo Yoga 7 2 en 1 de 14 pulgadas",
    "R02": "el iPhone 15 de 256 GB",
    None: "el Samsung Galaxy S25 Ultra de 512 GB",  # nadie lo ofrece: fuera del catálogo
}


def _restricciones(*triples: tuple[str, str, object]) -> list[RestriccionDura]:
    perfil = cargar_perfil(RUTA_PERFIL)
    return [restriccion_canonica(perfil.atributo(a), op, v) for a, op, v in triples]  # type: ignore[arg-type]


def _restricciones_tareas() -> list[tuple[str, Criterios]]:
    return [
        (
            "Necesito un monitor de al menos 27 pulgadas con resolución QHD o mejor, por máximo "
            "$1.300.000 con envío.",
            Criterios(
                tipo_producto="monitor",
                atributos=_restricciones(
                    ("tamano_pantalla", ">=", 27.0), ("resolucion", ">=", "QHD")
                ),
                presupuesto_max=1_300_000,
            ),
        ),
        (
            "Busco una tarjeta microSD de por lo menos 128 GB que no pase de $150.000.",
            Criterios(
                tipo_producto="almacenamiento",
                atributos=_restricciones(
                    ("tipo_almacenamiento", "==", "microSD"), ("almacenamiento", ">=", 128.0)
                ),
                presupuesto_max=150_000,
            ),
        ),
        (
            "Quiero un portátil con 16 GB de RAM y 1 TB de disco por menos de $5.000.000.",
            Criterios(
                tipo_producto="portatil",
                atributos=_restricciones(
                    ("memoria_ram", ">=", 16.0), ("almacenamiento", ">=", 1024.0)
                ),
                presupuesto_max=5_000_000,
            ),
        ),
        (
            "¿Qué audífonos inalámbricos consigo por máximo $200.000?",
            Criterios(
                tipo_producto="audifonos",
                atributos=_restricciones(("inalambrico", "==", True)),
                presupuesto_max=200_000,
            ),
        ),
        (
            "Necesito un celular con al menos 256 GB de almacenamiento.",
            Criterios(
                tipo_producto="celular",
                atributos=_restricciones(("almacenamiento", ">=", 256.0)),
            ),
        ),
    ]


def generar() -> list[Tarea]:
    catalogo = cargar_catalogo(RUTA_CATALOGO_A)
    verdad = json.loads(RUTA_VERDAD_A.read_text(encoding="utf-8"))
    filas: list[tuple[str, str, Criterios]] = []
    for pid, nombre in ESPECIFICAS.items():
        filas.append(
            (
                "especifica",
                f"¿Qué tiendas tienen {nombre} y a qué precio?",
                Criterios(productos=[pid]),
            )
        )
    for pid, nombre in MAS_BARATO.items():
        filas.append(
            (
                "mas_barato",
                f"¿Dónde compro más barato {nombre}, con envío?",
                Criterios(productos=[pid]),
            )
        )
    for consulta, criterios in _restricciones_tareas():
        filas.append(("restricciones", consulta, criterios))
    for pid, nombre in SIN_RESPUESTA.items():
        filas.append(
            (
                "sin_respuesta",
                f"¿Dónde puedo comprar {nombre} y a qué precio?",
                Criterios(productos=[pid] if pid else []),
            )
        )
    tareas = []
    for i, (categoria, consulta, criterios) in enumerate(filas, start=1):
        respuesta = calcular_respuesta(criterios, verdad, catalogo)
        if (categoria == "sin_respuesta") != respuesta.abstencion:
            raise ValueError(f"A{i:03d}: la verdad no coincide con la categoría {categoria}")
        tareas.append(
            Tarea(
                id=f"A{i:03d}",
                categoria=categoria,  # type: ignore[arg-type]
                consulta=consulta,
                criterios=criterios,
                respuesta=respuesta,
            )
        )
    return tareas


def main() -> None:
    tareas = generar()
    RUTA_TAREAS_A.write_text("".join(t.model_dump_json() + "\n" for t in tareas), encoding="utf-8")
    for t in tareas:
        r = t.respuesta
        print(
            f"{t.id} {t.categoria:13} "
            + (
                "abstención"
                if r.abstencion
                else f"{r.proveedor} {r.producto_id} ${r.costo_total:,}"
            )
        )


if __name__ == "__main__":
    main()
