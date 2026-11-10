"""E1: aporte de la verificación N3, por reproducción pareada (D99–D104).

    uv run python -m comercio_agentico.arnes.e1                  # requiere corpus B y A servidos
    uv run python -m comercio_agentico.arnes.e1 --solo-analisis  # con las lecturas guardadas (US$0)

Toma las corridas C1 de la calibración v3 (corpus B) y del corpus A v1. Para cada oferta registrada
regenera su fragmento leyendo el corpus congelado (sin LLM), lo compara con el SHA-256 de su
procedencia (D103) y lo lee por la segunda ruta de N3 (parser o Haiku; una vez por fragmento, con
reanudación). Luego decide cada ejecución tres veces con ``proponer`` (determinista): sin N3, con N3
y abstención (principal) y con N3 y exclusión (secundaria). Escribe en ``resultados/informes/e1/``
la tabla de predicción selectiva (M2, M4), M1 por estado de verificación, la calidad de N3 como
detector de errores de extracción y su costo y latencia (M6).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import statistics
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from comercio_agentico.agente.fuentes import cargar_fuentes
from comercio_agentico.agente.grafo import proponer, proponer_con_n3
from comercio_agentico.agente.interpretacion import Necesidad
from comercio_agentico.agente.lectura import Lector
from comercio_agentico.arnes.correr import recursos_corpus
from comercio_agentico.arnes.metricas import (
    CAMPOS_SIEMPRE,
    DIR_INFORMES,
    _igual,
    cargar_corrida,
    m1_extraccion,
    m4_abstencion,
    misma_ubicacion,
    wilson,
)
from comercio_agentico.corpus_b import RAIZ, RUTA_PERFIL
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.corpus_b.tareas import cargar_tareas
from comercio_agentico.esquema import ListaOfertas, Oferta, cargar_perfil, suma_verificacion
from comercio_agentico.modelos import RegistroCosto, obtener_extractor
from comercio_agentico.preguntar import evaluar
from comercio_agentico.verificacion import (
    MODELO_VERIFICADOR,
    Contraparte,
    segunda_lectura,
    verificar_oferta,
)

log = logging.getLogger("comercio_agentico.e1")
DIR_CORRIDAS = RAIZ / "resultados" / "corridas"
CORRIDAS = {
    "b": DIR_CORRIDAS / "2026-11-09_calibracion_flash_v3.jsonl.gz",
    "a": DIR_CORRIDAS / "2026-11-09_corpus_a_flash_v1.jsonl.gz",
}
DIR_E1 = DIR_INFORMES / "e1"
RUTA_LECTURAS = RAIZ / "resultados" / "e1" / "segundas_lecturas.jsonl"
TOPE_USD = 1.0  # D103: Anthropic
POLITICAS = ("sin_n3", "abstener", "excluir")


# --------------------------------------------------------------------------------------------------
# Regeneración de fragmentos y segundas lecturas


async def regenerar(corpus: str, consultas: set[str]) -> dict[str, str]:
    """Texto de cada consulta registrada, leído de nuevo del corpus congelado (US$0)."""
    registro = cargar_fuentes(recursos_corpus(corpus)["fuentes"])
    textos: dict[str, str] = {}
    async with Lector(registro) as lector:
        for consulta in sorted(consultas):
            if consulta.startswith("mcp://"):
                args = json.loads(consulta.split("?", 1)[1])
                doc = await lector.consultar_mcp(args.get("texto", ""), args.get("familia"))
            else:
                fuente = registro.por_url(consulta)
                if fuente is not None and fuente.herramienta == "leer_documento":
                    doc = await lector.leer_documento(consulta)
                else:
                    doc = await lector.abrir_pagina(consulta)
            textos[consulta] = doc.texto
    return textos


def cargar_lecturas(ruta: Path = RUTA_LECTURAS) -> dict[str, dict]:
    if not ruta.exists():
        return {}
    filas = [json.loads(x) for x in ruta.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {f["suma"]: f for f in filas if f.get("error") is None}


async def segundas_lecturas(
    fragmentos: dict[str, tuple[str, str]], ruta: Path = RUTA_LECTURAS, concurrencia: int = 4
) -> dict[str, dict]:
    """``fragmentos``: suma → (texto, tipo_fuente). Lee los que falten y los anexa a ``ruta``."""
    hechas = cargar_lecturas(ruta)
    pendientes = {s: f for s, f in fragmentos.items() if s not in hechas}
    gastado = sum(f["costo_usd"] for f in hechas.values())
    log.info("segundas lecturas: %d hechas, %d pendientes", len(hechas), len(pendientes))
    if not pendientes:
        return hechas
    verificador = obtener_extractor(MODELO_VERIFICADOR, ListaOfertas, include_raw=True)
    semaforo = asyncio.Semaphore(concurrencia)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    async def una(suma: str, texto: str, tipo: str) -> None:
        nonlocal gastado
        async with semaforo:
            if gastado > 0.9 * TOPE_USD:
                raise RuntimeError(f"Gasto de N3 cerca del tope (US${gastado:.4f}); se detiene")
            costo = RegistroCosto(TOPE_USD)
            inicio = time.perf_counter()
            fila: dict[str, Any] = {"suma": suma, "tipo_fuente": tipo, "error": None}
            try:
                ruta_n3, contrapartes = await segunda_lectura(
                    texto, tipo, verificador, {"callbacks": [costo]}
                )
                fila |= {"ruta": ruta_n3, "contrapartes": [_a_dict(c) for c in contrapartes]}
            except Exception as error:  # se registra y se reintenta en la próxima pasada
                fila["error"] = f"{type(error).__name__}: {str(error)[:300]}"
            fila |= {
                "costo_usd": round(costo.costo_total, 6),
                "segundos": round(time.perf_counter() - inicio, 2),
            }
            gastado += costo.costo_total
            with ruta.open("a", encoding="utf-8") as f:
                f.write(json.dumps(fila, ensure_ascii=False) + "\n")
            if fila["error"] is None:
                hechas[suma] = fila
            log.info(
                "  %s %s %s US$%.4f", tipo, fila.get("ruta"), fila["error"] or "", fila["costo_usd"]
            )

    await asyncio.gather(*(una(s, t, tipo) for s, (t, tipo) in pendientes.items()))
    return hechas


def _a_dict(c: Contraparte) -> dict:
    return {**asdict(c), "publicados": sorted(c.publicados)}


def _de_dict(d: dict) -> Contraparte:
    return Contraparte(**{**d, "publicados": frozenset(d["publicados"])})


# --------------------------------------------------------------------------------------------------
# Reproducción pareada


def _ofertas(fila: dict, textos: dict[str, str]) -> tuple[list[Oferta], list[bool]]:
    ofertas, coinciden = [], []
    for o in fila.get("ofertas_todas", []):
        p = o["procedencia"]
        texto = textos[p["consulta"]]
        coinciden.append(suma_verificacion(texto) == p["suma_verificacion"])
        procedencia = {**p, "fragmento_original": texto, "suma_verificacion": ""}
        ofertas.append(Oferta.model_validate({**o, "procedencia": procedencia}))
    return ofertas, coinciden


def reproducir(
    corpus: str, filas: list[dict], textos: dict[str, str], lecturas: dict[str, dict]
) -> tuple[dict[str, list[dict]], list[dict]]:
    """Filas sintéticas por política y una fila por oferta con su verificación."""
    rec = recursos_corpus(corpus)
    tareas = {t.id: t for t in cargar_tareas(rec["tareas"])}
    productos = {p.id: p for p in cargar_catalogo(rec["catalogo"])}
    perfil = cargar_perfil(RUTA_PERFIL)
    por_politica: dict[str, list[dict]] = {p: [] for p in POLITICAS}
    por_oferta: list[dict] = []

    for fila in filas:
        tarea = tareas[fila["tarea"]]
        base = {k: fila[k] for k in ("tarea", "categoria", "repeticion")} | {"corpus": corpus}
        if fila.get("error") or not fila.get("necesidad"):
            for p in POLITICAS:
                por_politica[p].append({**base, **_sin_reproduccion(fila)})
            continue
        ofertas, coinciden = _ofertas(fila, textos)
        for o, coincide in zip(ofertas, coinciden, strict=True):
            lectura = lecturas[o.procedencia.suma_verificacion]
            v = verificar_oferta(o, lectura["ruta"], [_de_dict(c) for c in lectura["contrapartes"]])
            o.verificacion = v.estado
            por_oferta.append(
                {
                    **base,
                    "proveedor": o.proveedor,
                    "tipo_fuente": o.procedencia.tipo_fuente,
                    "producto_catalogo": o.producto_catalogo,
                    "estado": v.estado,
                    "ruta": v.ruta,
                    "campos": v.campos,
                    "coincide_sha": coincide,
                    "oferta": o.model_dump(
                        mode="json", exclude={"procedencia": {"fragmento_original"}}
                    ),
                }
            )
        necesidad = Necesidad.model_validate(fila["necesidad"])
        alertas = (fila.get("propuesta") or {}).get("alertas") or []
        errores = [a["mensaje"] for a in alertas if a["tipo"] == "fuente_no_disponible"]
        args = (fila["propuesta"]["consulta"], necesidad, ofertas, perfil, productos, errores)
        costo = fila.get("costo_usd") or 0.0
        propuestas = {
            "sin_n3": proponer(*args, fila.get("modelo") or "", costo),
            "abstener": proponer_con_n3(*args, "", costo, politica="abstener"),
            "excluir": proponer_con_n3(*args, "", costo, politica="excluir"),
        }
        todas = [
            o.model_dump(mode="json", exclude={"procedencia": {"fragmento_original"}})
            for o in ofertas
        ]
        for p, propuesta in propuestas.items():
            ev = evaluar(tarea, SimpleNamespace(propuesta=propuesta))  # type: ignore[arg-type]
            ganadora = None
            if p == "sin_n3" and propuesta.recomendada is not None:
                g = propuesta.ofertas[propuesta.recomendada]
                ruta_g = lecturas[g.procedencia.suma_verificacion]["ruta"]
                ganadora = f"{g.procedencia.tipo_fuente}/{ruta_g}/{g.verificacion}"
            por_politica[p].append(
                {
                    **base,
                    "evaluacion": ev,
                    "propuesta": {"abstencion": propuesta.abstencion},
                    "ofertas_todas": todas,
                    "acierto_original": fila["evaluacion"]["acierto"],
                    "coincide_sha": all(coinciden),
                    "ganadora": ganadora,
                }
            )
    return por_politica, por_oferta


def _sin_reproduccion(fila: dict) -> dict:
    """Ejecución con error o sin necesidad: se conserva tal cual en las tres políticas."""
    return {
        "evaluacion": fila["evaluacion"],
        "propuesta": {"abstencion": bool((fila.get("propuesta") or {}).get("abstencion", True))},
        "ofertas_todas": [],
        "acierto_original": fila["evaluacion"]["acierto"],
        "coincide_sha": True,
        "ganadora": None,
    }


# --------------------------------------------------------------------------------------------------
# Métricas


def campos_erroneos(oferta: dict, verdad: dict) -> list[str] | None:
    """Campos de la primera ruta que no coinciden con la verdad (reglas de M1); None si la oferta
    no tiene oferta verdadera con la que compararse."""
    clave = (oferta["procedencia"]["fuente"], oferta.get("producto_catalogo"))
    indice = {(o["proveedor"], o["producto_id"]): o for o in verdad["ofertas"]}
    if clave not in indice:
        return None
    v = indice[clave]
    de_listado = not misma_ubicacion(oferta, v["ubicacion"])
    errores = []
    for campo in [*CAMPOS_SIEMPRE, "gtin"]:
        extraido, verdadero = oferta.get(campo), v["oferta"].get(campo)
        if de_listado and campo != "precio":
            if extraido not in (None, "desconocida"):
                errores.append(campo)  # dato que el listado no publica: invención
            continue
        if campo == "gtin" and verdadero is None and extraido is None:
            continue
        if not _igual(campo, extraido, verdadero):
            errores.append(campo)
    return errores


def detector(
    por_oferta: list[dict], verdad: dict, solo_no_agotadas: bool = False
) -> dict[str, Any]:
    """N3 como detector de errores de extracción: marcada (no verificada) frente a error real.

    ``solo_no_agotadas``: solo ofertas que la verdad da por disponibles o a pedido, las únicas que
    pueden ganar (lectura *post hoc*)."""
    indice = {(o["proveedor"], o["producto_id"]): o["oferta"] for o in verdad["ofertas"]}
    vp = fp = fn = vn = sin_verdad = 0
    for fila in por_oferta:
        errores = campos_erroneos(fila["oferta"], verdad)
        if errores is None:
            sin_verdad += 1
            continue
        clave = (fila["oferta"]["procedencia"]["fuente"], fila["oferta"].get("producto_catalogo"))
        if solo_no_agotadas and indice[clave]["disponibilidad"] == "agotado":
            continue
        marcada, error = fila["estado"] != "verificada", bool(errores)
        vp += marcada and error
        fp += marcada and not error
        fn += error and not marcada
        vn += not marcada and not error
    return {
        "vp": vp,
        "fp": fp,
        "fn": fn,
        "vn": vn,
        "sin_verdad": sin_verdad,
        "precision": wilson(vp, vp + fp),
        "sensibilidad": wilson(vp, vp + fn),
        "tasa_error": wilson(vp + fn, vp + fp + fn + vn),
        "tasa_marcadas": wilson(vp + fp, vp + fp + fn + vn),
    }


def calcular(
    por_politica: dict[str, list[dict]],
    por_oferta: list[dict],
    lecturas: dict[str, dict],
    corpus: str,
) -> dict[str, Any]:
    rec = recursos_corpus(corpus)
    tareas = {t.id: t for t in cargar_tareas(rec["tareas"])}
    verdad = json.loads(Path(rec["verdad"]).read_text(encoding="utf-8"))
    filas = por_politica["sin_n3"]
    tabla = {}
    for p, fs in por_politica.items():
        m4 = m4_abstencion(fs, tareas)
        tabla[p] = {
            "m2": wilson(sum(f["evaluacion"]["acierto"] for f in fs), len(fs)),
            "cobertura": m4["cobertura"],
            "exactitud_cubierta": m4["exactitud_cubierta"],
            "abstencion_correcta": m4["abstencion_correcta"],
            "abstencion_indebida": m4["abstencion_indebida"],
            "m2_sha_coincidente": wilson(
                sum(f["evaluacion"]["acierto"] for f in fs if f["coincide_sha"]),
                sum(f["coincide_sha"] for f in fs),
            ),
        }
    estados: dict[str, dict[str, int]] = {}
    for f in por_oferta:
        clave = f"{f['tipo_fuente']}/{f['ruta']}"
        estados.setdefault(clave, {"verificada": 0, "discrepancia": 0, "sin_contraparte": 0})
        estados[clave][f["estado"]] += 1
    campos: dict[str, int] = {}
    for f in por_oferta:
        for c in f["campos"]:
            campos[c] = campos.get(c, 0) + 1

    def m1_de(estado_ok: bool) -> dict:
        subfilas = [
            {
                **fl,
                "ofertas_todas": [
                    o
                    for o in fl["ofertas_todas"]
                    if (o.get("verificacion") == "verificada") == estado_ok
                ],
            }
            for fl in filas
        ]
        return m1_extraccion(subfilas, verdad, tareas)["global"]

    sumas = {f["oferta"]["procedencia"]["suma_verificacion"] for f in por_oferta}
    usadas = [lecturas[s] for s in sumas if s in lecturas]
    costo_tarea = []
    for fl in filas:
        propias = {o["procedencia"]["suma_verificacion"] for o in fl["ofertas_todas"]}
        costo_tarea.append(sum(lecturas[s]["costo_usd"] for s in propias if s in lecturas))
    llm = [u for u in usadas if u["ruta"] == "reextraccion"]
    return {
        "corpus": corpus,
        "corrida": CORRIDAS[corpus].name,
        "ejecuciones": len(filas),
        "control_reproduccion": wilson(
            sum(f["evaluacion"]["acierto"] == f["acierto_original"] for f in filas), len(filas)
        ),
        "politicas": tabla,
        "ofertas": len(por_oferta),
        "coincidencia_sha_ofertas": wilson(
            sum(f["coincide_sha"] for f in por_oferta), len(por_oferta)
        ),
        "estados_por_fuente_y_ruta": estados,
        "campos_en_discrepancia": campos,
        "m1_verificadas": m1_de(True),
        "m1_no_verificadas": m1_de(False),
        "detector": detector(por_oferta, verdad),
        "detector_no_agotadas": detector(por_oferta, verdad, solo_no_agotadas=True),
        "ofertas_distintas": len(
            {
                (f["oferta"]["procedencia"]["suma_verificacion"], f["producto_catalogo"])
                for f in por_oferta
            }
        ),
        "ganadoras": dict(Counter(f["ganadora"] for f in filas if f.get("ganadora"))),
        "m6": {
            "fragmentos": len(usadas),
            "fragmentos_llm": len(llm),
            "costo_total_usd": round(sum(u["costo_usd"] for u in usadas), 6),
            "costo_por_tarea_sin_cache_usd": round(statistics.mean(costo_tarea), 6)
            if costo_tarea
            else None,
            "latencia_llm_p50_s": statistics.median([u["segundos"] for u in llm]) if llm else None,
            "latencia_llm_max_s": max((u["segundos"] for u in llm), default=None),
        },
    }


# --------------------------------------------------------------------------------------------------
# Informe


def _pct(w: dict) -> str:
    if not w.get("n"):
        return "—"
    return (
        f"{100 * w['p']:.1f} % ({w['k']}/{w['n']}) [{100 * w['bajo']:.1f}; {100 * w['alto']:.1f}]"
    )


NOMBRES = {
    "sin_n3": "Sin N3",
    "abstener": "Con N3, abstención (principal)",
    "excluir": "Con N3, exclusión (secundaria)",
}


def a_markdown(resultados: list[dict]) -> str:
    lineas = ["# E1 — Aporte de la verificación N3 (reproducción pareada, D99–D104)", ""]
    for m in resultados:
        control, sha = _pct(m["control_reproduccion"]), _pct(m["coincidencia_sha_ofertas"])
        m6 = m["m6"]
        lineas += [
            f"## Corpus {m['corpus'].upper()} — `{m['corrida']}` ({m['ejecuciones']} ejecuciones)",
            "",
            f"Control de reproducción (sin N3 = acierto original): {control}. "
            f"Fragmentos que reproducen su SHA-256 (por oferta): {sha}.",
            "",
            "| Política | M2 | Cobertura | Exactitud sobre lo cubierto | Abstención correcta | "
            "Abstención indebida |",
            "|---|---|---|---|---|---|",
        ]
        for p, t in m["politicas"].items():
            lineas.append(
                f"| {NOMBRES[p]} | {_pct(t['m2'])} | {_pct(t['cobertura'])} | "
                f"{_pct(t['exactitud_cubierta'])} | {_pct(t['abstencion_correcta'])} | "
                f"{_pct(t['abstencion_indebida'])} |"
            )
        d = m["detector"]
        dn = m["detector_no_agotadas"]
        lineas += [
            "",
            f"**Ofertas verificadas por N3** ({m['ofertas']} ofertas):",
            "",
            "| Fuente / ruta | Verificada | Discrepancia | Sin contraparte |",
            "|---|---|---|---|",
        ]
        for clave, e in sorted(m["estados_por_fuente_y_ruta"].items()):
            lineas.append(
                f"| {clave} | {e['verificada']} | {e['discrepancia']} | {e['sin_contraparte']} |"
            )
        lineas += [
            "",
            f"Campos en discrepancia: {m['campos_en_discrepancia'] or 'ninguno'}.",
            "",
            f"M1 (campo a campo frente a la verdad): verificadas {_pct(m['m1_verificadas'])}; "
            f"no verificadas {_pct(m['m1_no_verificadas'])}.",
            "",
            f"N3 como detector de errores de extracción (VP {d['vp']}, FP {d['fp']}, "
            f"FN {d['fn']}, VN {d['vn']}; {d['sin_verdad']} ofertas sin verdad): "
            f"precisión {_pct(d['precision'])}, "
            f"sensibilidad {_pct(d['sensibilidad'])}; ofertas con error {_pct(d['tasa_error'])}; "
            f"marcadas {_pct(d['tasa_marcadas'])}.",
            "",
            f"*Post hoc.* Solo ofertas no agotadas según la verdad (las que pueden ganar): "
            f"VP {dn['vp']}, FP {dn['fp']}, FN {dn['fn']}, VN {dn['vn']}; "
            f"precisión {_pct(dn['precision'])}, sensibilidad {_pct(dn['sensibilidad'])}. "
            f"Las {m['ofertas']} ofertas corresponden a {m['ofertas_distintas']} pares distintos "
            f"(fragmento, producto): los intervalos por oferta suponen independencia y son "
            f"optimistas. Ganadoras sin N3 por fuente/ruta/estado: {m['ganadoras']}.",
            "",
            f"M6 de N3: {m6['fragmentos']} fragmentos ({m6['fragmentos_llm']} con Haiku), "
            f"US${m6['costo_total_usd']:.4f} en total con caché; "
            f"US${(m6['costo_por_tarea_sin_cache_usd'] or 0):.4f} por tarea sin caché; "
            f"latencia de Haiku p50 {m6['latencia_llm_p50_s']} s, "
            f"máx. {m6['latencia_llm_max_s']} s.",
            "",
        ]
    return "\n".join(lineas)


def grafico(resultados: list[dict], ruta: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4.2))
    marcas = {"sin_n3": "o", "abstener": "s", "excluir": "^"}
    for m in resultados:
        for p, t in m["politicas"].items():
            c, e = t["cobertura"], t["exactitud_cubierta"]
            ax.errorbar(
                c["p"],
                e["p"],
                xerr=[[c["p"] - c["bajo"]], [c["alto"] - c["p"]]],
                yerr=[[e["p"] - e["bajo"]], [e["alto"] - e["p"]]],
                marker=marcas[p],
                capsize=3,
                label=f"Corpus {m['corpus'].upper()} · {NOMBRES[p]}",
            )
    ax.set_xlabel("Cobertura (tareas con respuesta que no se abstienen)")
    ax.set_ylabel("Exactitud sobre lo cubierto")
    ax.set_title("E1: predicción selectiva con N3 (IC 95 % de Wilson)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="lower left")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------------------------------
# Punto de entrada


async def principal(solo_analisis: bool) -> Path:
    resultados = []
    DIR_E1.mkdir(parents=True, exist_ok=True)
    detalle: list[dict] = []
    for corpus, ruta in CORRIDAS.items():
        filas = cargar_corrida(ruta)
        consultas = {
            o["procedencia"]["consulta"] for f in filas for o in f.get("ofertas_todas", [])
        }
        tipos = {
            o["procedencia"]["consulta"]: o["procedencia"]["tipo_fuente"]
            for f in filas
            for o in f.get("ofertas_todas", [])
        }
        log.info(
            "corpus %s: %d ejecuciones, %d fragmentos distintos", corpus, len(filas), len(consultas)
        )
        textos = await regenerar(corpus, consultas)
        fragmentos = {suma_verificacion(t): (t, tipos[c]) for c, t in textos.items()}
        if solo_analisis:
            lecturas = cargar_lecturas()
            faltan = set(fragmentos) - set(lecturas)
            if faltan:
                raise SystemExit(
                    f"Faltan {len(faltan)} segundas lecturas; corra sin --solo-analisis"
                )
        else:
            lecturas = await segundas_lecturas(fragmentos)
        por_politica, por_oferta = reproducir(corpus, filas, textos, lecturas)
        resultados.append(calcular(por_politica, por_oferta, lecturas, corpus))
        detalle += [{k: v for k, v in f.items() if k != "oferta"} for f in por_oferta]

    (DIR_E1 / "e1.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    with (DIR_E1 / "verificaciones.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(d, ensure_ascii=False) + "\n" for d in detalle)
    texto = a_markdown(resultados)
    (DIR_E1 / "e1.md").write_text(texto, encoding="utf-8")
    grafico(resultados, DIR_E1 / "e1_seleccion.png")
    print(texto)
    print(f"Informe en {DIR_E1}")
    return DIR_E1


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--solo-analisis", action="store_true", help="No llama a Haiku (US$0)")
    args = parser.parse_args()
    logging.basicConfig(format="%(message)s")
    logging.getLogger("comercio_agentico").setLevel(logging.INFO)
    asyncio.run(principal(args.solo_analisis))


if __name__ == "__main__":
    main()
