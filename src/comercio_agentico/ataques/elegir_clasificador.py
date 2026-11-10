"""Elección del clasificador de inyección de C2 con evidencia (S06).

Mide, sobre fragmentos **limpios** del corpus B (texto comercial real en español, ninguna carga de
ataque), cuántos marca cada clasificador candidato como inyección —es decir, su tasa de falsos
positivos— y su latencia por ventana en CPU. Un clasificador que se dispara con texto limpio
destruiría la utilidad del agente en C2, así que esta es la métrica de selección.

La detección de ataques reales se mide después, con la suite de cargas (M5, S06-bis/S07); aquí solo
se descarta a los que no sirven por exceso de falsas alarmas o por lentitud.

Uso:
    uv run python -m comercio_agentico.ataques.elegir_clasificador   # US$0, descarga los modelos

Guarda los resultados en ``resultados/clasificadores/<fecha>_falsos_positivos.json`` y una tabla
Markdown. Los fragmentos limpios están congelados en ``ataques/fragmentos_limpios_b.jsonl`` (se
regeneran con ``--regenerar``, que sirve el corpus B y lo lee con el Lector real del agente).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import time
from pathlib import Path

from comercio_agentico.ataques import DIR_ATAQUES
from comercio_agentico.corpus_b import RAIZ

RUTA_FRAGMENTOS = DIR_ATAQUES / "fragmentos_limpios_b.jsonl"
DIR_RESULTADOS = RAIZ / "resultados" / "clasificadores"

# Candidatos sin acceso restringido en el Hub (cualquiera que clone el repo los descarga sin pedir
# permiso, requisito de C2, D16/D80) y con licencia permisiva. Verificado en el Hub el 10-nov-2026.
CANDIDATOS = [
    "Horizon-Labs/prompt-injection-guard-small",  # Apache-2.0, mmBERT, multilingüe (es)
    "patronus-studio/wolf-defender-prompt-injection",  # Apache-2.0, mmBERT, de/en (+ es informado)
    "protectai/deberta-v3-base-prompt-injection-v2",  # Apache-2.0, DeBERTa-v3, solo inglés
]


def cargar_fragmentos(ruta: Path = RUTA_FRAGMENTOS) -> list[dict]:
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines() if linea]


async def extraer_fragmentos_limpios(puerto: int = 8809) -> list[dict]:
    """Sirve el corpus B y lo lee con el Lector del agente, luego lo divide en ventanas (lo que C2
    clasifica). Solo P2–P5: P1 (MCP) es JSON, no texto comercial en español."""
    import functools
    import threading
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    from comercio_agentico.agente.defensa import ventanas
    from comercio_agentico.agente.fuentes import cargar_fuentes
    from comercio_agentico.agente.lectura import Lector
    from comercio_agentico.corpus_b import DIR_CORPUS

    manejador = functools.partial(SimpleHTTPRequestHandler, directory=str(DIR_CORPUS))
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), manejador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    registro = cargar_fuentes()
    for fuente in registro.fuentes:
        fuente.url = fuente.url.replace("8800", str(puerto))
    try:
        frags: list[dict] = []
        async with Lector(registro) as lector:
            for fuente in registro.fuentes:
                if fuente.herramienta == "consultar_mcp":
                    continue
                if fuente.herramienta == "abrir_pagina":
                    doc = await lector.abrir_pagina(fuente.url)
                    docs = [doc] + [await lector.abrir_pagina(e) for e in doc.enlaces]
                else:
                    docs = [await lector.leer_documento(fuente.url)]
                for d in docs:
                    frags += [{"proveedor": fuente.id, "origen": d.consulta, "texto": v}
                              for v in ventanas(d.texto)]  # fmt: skip
        return frags
    finally:
        servidor.shutdown()


def medir(modelo: str, textos: list[str], pasadas: int = 3) -> dict:
    """Puntúa cada fragmento (lote 1) y mide latencia. Los fragmentos son limpios, así que todo
    puntaje ≥ 0,5 es un falso positivo."""
    from comercio_agentico.agente.defensa import ClasificadorInyeccion

    t0 = time.perf_counter()
    clf = ClasificadorInyeccion(modelo, lote=1)
    clf._cargar()
    carga = time.perf_counter() - t0
    latencias: list[float] = []
    puntajes: list[float] = []
    for pasada in range(pasadas):
        for texto in textos:
            inicio = time.perf_counter()
            p = clf.puntuar([texto])[0]
            latencias.append((time.perf_counter() - inicio) * 1000)
            if pasada == 0:
                puntajes.append(p)
    fp = sum(p >= clf.umbral for p in puntajes)
    return {
        "modelo": modelo,
        "n": len(textos),
        "falsos_positivos": fp,
        "tasa_fp": round(fp / len(textos), 3),
        "puntaje_maximo": round(max(puntajes), 3),
        "carga_s": round(carga, 1),
        "latencia_p50_ms": round(statistics.median(latencias)),
        "latencia_p90_ms": round(sorted(latencias)[int(len(latencias) * 0.9)]),
    }


def tabla_markdown(resultados: list[dict]) -> str:
    cab = "| Clasificador | Falsos positivos | Tasa FP | Puntaje máx. | p50 (ms) | p90 (ms) |"
    sep = "|---|---|---|---|---|---|"
    filas = [
        f"| {r['modelo']} | {r['falsos_positivos']}/{r['n']} | {r['tasa_fp']:.1%} | "
        f"{r['puntaje_maximo']:.3f} | {r['latencia_p50_ms']} | {r['latencia_p90_ms']} |"
        for r in resultados
    ]
    return "\n".join([cab, sep, *filas])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regenerar", action="store_true", help="Reextrae los fragmentos limpios")
    parser.add_argument("--modelos", nargs="*", default=CANDIDATOS)
    args = parser.parse_args()

    if args.regenerar or not RUTA_FRAGMENTOS.exists():
        import asyncio

        frags = asyncio.run(extraer_fragmentos_limpios())
        RUTA_FRAGMENTOS.write_text(
            "\n".join(json.dumps(f, ensure_ascii=False) for f in frags), encoding="utf-8"
        )
    fragmentos = cargar_fragmentos()
    textos = [f["texto"] for f in fragmentos]
    print(f"{len(textos)} ventanas limpias del corpus B (P2–P5)\n")

    resultados = []
    for modelo in args.modelos:
        print(f"midiendo {modelo} …", flush=True)
        resultados.append(medir(modelo, textos))

    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
    fecha = dt.date.today().isoformat()
    salida = DIR_RESULTADOS / f"{fecha}_falsos_positivos.json"
    salida.write_text(
        json.dumps(
            {"fecha": fecha, "n_fragmentos": len(textos), "resultados": resultados},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    tabla = tabla_markdown(resultados)
    (DIR_RESULTADOS / f"{fecha}_falsos_positivos.md").write_text(tabla + "\n", encoding="utf-8")
    print("\n" + tabla)
    print(f"\nGuardado en {salida}")


if __name__ == "__main__":
    main()
