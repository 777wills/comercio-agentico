"""Métricas de una corrida del arnés, sin juicio humano ni LLM juez (D45).

    uv run python -m comercio_agentico.arnes.metricas resultados/corridas/<corrida>.jsonl

- **M1 exactitud de extracción por ruta:** cada oferta recolectada y emparejada se compara campo a
  campo con su oferta en ``verdad.json`` (mismo proveedor y producto). Se informa por tipo de fuente
  (MCP, HTML con JSON-LD, HTML plano, PDF, mensaje), junto con las ofertas sin correspondencia en la
  verdad (emparejamiento erróneo o invención) y la **recolección**: qué fracción de las ofertas
  válidas de la tarea llegó al cuadro.
- **M2 éxito por categoría de tarea:** acierto de la recomendación (o de la abstención).
- **M3 acuerdo entre ejecuciones:** fracción de tareas con la misma decisión en todas las
  repeticiones y dispersión de M2 entre repeticiones (insumo de la regla de parada de E3, D42).
- **M4 abstención:** sensibilidad (se abstiene cuando debe), abstención indebida, cobertura y
  exactitud sobre lo cubierto (exactitud selectiva).
- **M6 costo y latencia:** costo por tarea (media, p50, p90) y latencia p50/p90.

Proporciones con intervalo de Wilson al 95 %; medias y percentiles con bootstrap percentil
(semilla fija). La unidad de M1 es la observación de extracción: la misma página extraída en
varias tareas cuenta varias veces, así que su intervalo es optimista.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from comercio_agentico.corpus_b import RAIZ
from comercio_agentico.corpus_b.generar import cargar_verdad
from comercio_agentico.corpus_b.tareas import Tarea, cargar_tareas

DIR_INFORMES = RAIZ / "resultados" / "informes"
SEMILLA = 20261112
CATEGORIAS = ["especifica", "mas_barato", "restricciones", "vaga", "sin_respuesta"]
FUENTES = ["mcp", "web_schema", "web_plana", "pdf", "mensaje"]
NOMBRE_FUENTE = {
    "mcp": "P1 MCP",
    "web_schema": "P2 HTML + JSON-LD",
    "web_plana": "P3 HTML plano",
    "pdf": "P4 PDF",
    "mensaje": "P5 mensaje",
}
CAMPOS_SIEMPRE = ["precio", "costo_envio", "disponibilidad", "plazo_entrega_dias"]
# Se comparan si la fuente los publica; un GTIN o MPN que la fuente no publica cuenta como
# invención. La marca solo se compara donde la fuente la publica (inferirla del título es válido).
CAMPOS_SI_PUBLICADOS = ["gtin", "mpn", "marca"]


# --------------------------------------------------------------------------------------------------
# Estadística


def wilson(k: int, n: int) -> dict[str, float | int | None]:
    if n == 0:
        return {"k": 0, "n": 0, "p": None, "bajo": None, "alto": None}
    ic = stats.binomtest(k, n).proportion_ci(method="wilson")
    return {"k": k, "n": n, "p": k / n, "bajo": float(ic.low), "alto": float(ic.high)}


def _percentil(q: float):
    def f(x: np.ndarray, axis: int = -1) -> np.ndarray:
        return np.percentile(x, q, axis=axis)

    return f


def bootstrap(valores: list[float], estadistico: Any = np.mean) -> dict[str, float | None]:
    x = np.asarray(valores, dtype=float)
    if len(x) == 0:
        return {"valor": None, "bajo": None, "alto": None}
    valor = float(estadistico(x, axis=-1))
    if len(x) < 2 or np.all(x == x[0]):
        return {"valor": valor, "bajo": valor, "alto": valor}
    r = stats.bootstrap(
        (x,),
        estadistico,
        n_resamples=5000,
        method="percentile",
        rng=np.random.default_rng(SEMILLA),
    )
    return {
        "valor": valor,
        "bajo": float(r.confidence_interval.low),
        "alto": float(r.confidence_interval.high),
    }


# --------------------------------------------------------------------------------------------------
# M1


def _documento(url: str) -> str:
    """Último segmento de la ruta, sin consulta ni ancla: ``.../c01.html#x`` → ``c01.html``."""
    return url.split("?")[0].split("#")[0].rstrip("/").rsplit("/", 1)[-1]


def misma_ubicacion(oferta: dict, ubicacion_verdad: str) -> bool:
    """¿La oferta se leyó del documento donde la verdad la publica completa?

    Si no (p. ej., el índice de P2, que solo muestra título y precio), la oferta viene de un
    listado y M1 solo compara el precio: no extraer un envío que el listado no muestra es correcto.
    En P1 la búsqueda devuelve la ficha completa, así que cuenta como el mismo documento.
    """
    if oferta["procedencia"]["tipo_fuente"] == "mcp":
        return True
    return _documento(oferta["procedencia"]["consulta"]) == _documento(ubicacion_verdad)


def _igual(campo: str, extraido: Any, verdadero: Any) -> bool:
    if extraido is None or verdadero is None:
        return extraido is verdadero
    if campo in ("precio", "costo_envio", "plazo_entrega_dias"):
        return abs(float(extraido) - float(verdadero)) < 0.5
    if campo in ("mpn", "marca"):
        return str(extraido).strip().casefold() == str(verdadero).strip().casefold()
    return extraido == verdadero


def m1_extraccion(filas: list[dict], verdad: dict, tareas: dict[str, Tarea]) -> dict[str, Any]:
    indice = {(o["proveedor"], o["producto_id"]): o["oferta"] for o in verdad["ofertas"]}
    verdad_ubic = {(o["proveedor"], o["producto_id"]): o["ubicacion"] for o in verdad["ofertas"]}
    listados = Counter()
    aciertos: dict[str, Counter] = defaultdict(Counter)  # fuente → campo → aciertos
    totales: dict[str, Counter] = defaultdict(Counter)
    ofertas, sin_correspondencia = Counter(), Counter()
    recogidas = esperadas = 0

    for fila in filas:
        for o in fila.get("ofertas_todas", []):
            fuente = o["procedencia"]["tipo_fuente"]
            ofertas[fuente] += 1
            v = indice.get((o["procedencia"]["fuente"], o.get("producto_catalogo")))
            if v is None:
                sin_correspondencia[fuente] += 1
                continue
            de_listado = not misma_ubicacion(
                o, verdad_ubic[(o["procedencia"]["fuente"], o.get("producto_catalogo"))]
            )
            listados[fuente] += de_listado
            for campo in CAMPOS_SIEMPRE + CAMPOS_SI_PUBLICADOS:
                if de_listado and campo != "precio":
                    if o.get(campo) in (None, "desconocida") or campo == "marca":
                        continue  # el listado no lo publica: no extraerlo es lo correcto
                    totales[fuente][campo] += 1  # dato que el listado no publica: invención
                    continue
                # La marca se puede inferir del título; un GTIN o MPN no publicado es invención.
                if (
                    campo in CAMPOS_SI_PUBLICADOS
                    and v.get(campo) is None
                    and (campo == "marca" or o.get(campo) is None)
                ):
                    continue

                totales[fuente][campo] += 1
                aciertos[fuente][campo] += _igual(campo, o.get(campo), v.get(campo))
        tarea = tareas.get(fila["tarea"])
        if tarea and not tarea.respuesta.abstencion:
            validas = {tuple(x) for x in tarea.respuesta.ofertas_validas}
            vistas = {
                (o["procedencia"]["fuente"], o.get("producto_catalogo"))
                for o in fila.get("ofertas_todas", [])
            }
            esperadas += len(validas)
            recogidas += len(validas & vistas)

    por_fuente = {}
    for fuente in FUENTES:
        if not ofertas[fuente]:
            continue
        campos = {c: wilson(aciertos[fuente][c], totales[fuente][c]) for c in totales[fuente]}
        por_fuente[fuente] = {
            "ofertas": ofertas[fuente],
            "de_listado": listados[fuente],
            "sin_correspondencia": wilson(sin_correspondencia[fuente], ofertas[fuente]),
            "campos": campos,
            "global": wilson(sum(aciertos[fuente].values()), sum(totales[fuente].values())),
        }
    todos_a = sum(sum(c.values()) for c in aciertos.values())
    todos_t = sum(sum(c.values()) for c in totales.values())
    return {
        "por_fuente": por_fuente,
        "global": wilson(todos_a, todos_t),
        "sin_correspondencia": wilson(sum(sin_correspondencia.values()), sum(ofertas.values())),
        "recoleccion": wilson(recogidas, esperadas),
    }


# --------------------------------------------------------------------------------------------------
# M2, M3, M4, M6


def m2_exito(filas: list[dict]) -> dict[str, Any]:
    por_cat = {
        c: wilson(
            sum(f["evaluacion"]["acierto"] for f in filas if f["categoria"] == c),
            sum(f["categoria"] == c for f in filas),
        )
        for c in CATEGORIAS
        if any(f["categoria"] == c for f in filas)
    }
    return {
        "por_categoria": por_cat,
        "global": wilson(sum(f["evaluacion"]["acierto"] for f in filas), len(filas)),
        "procedencia_completa": wilson(
            sum(bool(f["evaluacion"].get("procedencia_completa")) for f in filas), len(filas)
        ),
        "errores": sum(f.get("error") is not None for f in filas),
    }


def decision(fila: dict) -> str:
    """Decisión comparable entre repeticiones: oferta elegida, abstención o error."""
    if fila.get("error"):
        return "ERROR"
    if fila["propuesta"]["abstencion"]:
        return "ABSTENCION"
    elegida = fila["evaluacion"]["elegida"]
    return "/".join(elegida) if elegida else "SIN_ELECCION"


def m3_acuerdo(filas: list[dict]) -> dict[str, Any]:
    reps = sorted({f["repeticion"] for f in filas})
    if len(reps) < 2:
        return {"aplica": False, "repeticiones": len(reps)}
    por_tarea: dict[str, list[str]] = defaultdict(list)
    for f in filas:
        por_tarea[f["tarea"]].append(decision(f))
    completas = {t: d for t, d in por_tarea.items() if len(d) == len(reps)}
    unanimes = sum(len(set(d)) == 1 for d in completas.values())
    m2_rep = [
        float(np.mean([f["evaluacion"]["acierto"] for f in filas if f["repeticion"] == r]))
        for r in reps
    ]
    return {
        "aplica": True,
        "repeticiones": len(reps),
        "acuerdo_total": wilson(unanimes, len(completas)),
        "m2_por_repeticion": m2_rep,
        "m2_rango": max(m2_rep) - min(m2_rep),
        "m2_desviacion": float(np.std(m2_rep, ddof=1)),
    }


def m4_abstencion(filas: list[dict], tareas: dict[str, Tarea]) -> dict[str, Any]:
    def se_abstuvo(f: dict) -> bool:
        return bool(f.get("propuesta") and f["propuesta"]["abstencion"])

    debe = [f for f in filas if tareas[f["tarea"]].respuesta.abstencion]
    no_debe = [f for f in filas if not tareas[f["tarea"]].respuesta.abstencion]
    cubiertas = [f for f in filas if not se_abstuvo(f)]
    return {
        "abstencion_correcta": wilson(sum(se_abstuvo(f) for f in debe), len(debe)),
        "abstencion_indebida": wilson(sum(se_abstuvo(f) for f in no_debe), len(no_debe)),
        "cobertura": wilson(sum(not se_abstuvo(f) for f in no_debe), len(no_debe)),
        "exactitud_cubierta": wilson(
            sum(f["evaluacion"]["acierto"] for f in cubiertas), len(cubiertas)
        ),
    }


def m6_costo_latencia(filas: list[dict]) -> dict[str, Any]:
    costos = [f["costo_usd"] for f in filas if f.get("costo_usd") is not None]
    segundos = [f["segundos"] for f in filas if f.get("segundos") is not None]
    con_tokens = [f for f in filas if f.get("tokens")]
    return {
        "ejecuciones": len(filas),
        "costo_total": float(sum(costos)),
        "costo_medio": bootstrap(costos),
        "costo_p50": bootstrap(costos, _percentil(50)),
        "costo_p90": bootstrap(costos, _percentil(90)),
        "latencia_p50": bootstrap(segundos, _percentil(50)),
        "latencia_p90": bootstrap(segundos, _percentil(90)),
        "tokens_entrada_medio": float(np.mean([f["tokens"][0] for f in con_tokens]))
        if con_tokens
        else None,
        "tokens_salida_medio": float(np.mean([f["tokens"][1] for f in con_tokens]))
        if con_tokens
        else None,
        "llamadas_llm_medio": float(np.mean([f["llamadas_llm"] for f in con_tokens]))
        if con_tokens
        else None,
        "herramientas_medio": float(np.mean([f["llamadas_herramientas"] for f in con_tokens]))
        if con_tokens
        else None,
    }


def calcular(
    filas: list[dict], tareas: list[Tarea] | None = None, verdad: dict | None = None
) -> dict[str, Any]:
    tareas_por_id = {t.id: t for t in (tareas or cargar_tareas())}
    verdad = verdad or cargar_verdad()
    meta = {k: filas[0].get(k) for k in ("corrida", "modelo", "version_prompt", "hash_corpus")}
    meta["commit"] = sorted({f.get("commit") for f in filas if f.get("commit")})
    cfg = filas[0].get("config") or {}
    meta["separacion_planos"] = cfg.get("separacion_planos")
    meta["configuracion"] = cfg.get("configuracion")
    return {
        "meta": meta,
        "M1": m1_extraccion(filas, verdad, tareas_por_id),
        "M2": m2_exito(filas),
        "M3": m3_acuerdo(filas),
        "M4": m4_abstencion(filas, tareas_por_id),
        "M6": m6_costo_latencia(filas),
    }


# --------------------------------------------------------------------------------------------------
# Presentación


def _pct(w: dict) -> str:
    if w.get("p") is None:
        return "—"
    return f"{100 * w['p']:.1f} % [{100 * w['bajo']:.1f}–{100 * w['alto']:.1f}] ({w['k']}/{w['n']})"


def _num(b: dict, formato: str) -> str:
    if b.get("valor") is None:
        return "—"
    return f"{b['valor']:{formato}} [{b['bajo']:{formato}}–{b['alto']:{formato}}]"


def a_markdown(m: dict[str, Any]) -> str:
    me, m1, m2, m3, m4, m6 = m["meta"], m["M1"], m["M2"], m["M3"], m["M4"], m["M6"]
    plano = me.get("configuracion") or {True: "C1", False: "C0"}.get(me["separacion_planos"], "?")
    lineas = [
        f"# Métricas de la corrida `{me['corrida']}`",
        "",
        f"Modelo `{me['modelo']}` · {plano} · prompt `{me['version_prompt']}` · "
        f"corpus `{me['hash_corpus']}` · commit {', '.join(me['commit'])} · "
        f"{m6['ejecuciones']} ejecuciones · {m2['errores']} con error.",
        "",
        "Proporciones: valor [IC 95 % de Wilson] (aciertos/total). Costo y latencia: valor "
        "[IC 95 % bootstrap].",
        "",
        "## M2 Éxito por categoría de tarea",
        "",
        "| Categoría | Éxito |",
        "|---|---|",
        *[f"| {c} | {_pct(w)} |" for c, w in m2["por_categoria"].items()],
        f"| **Global** | **{_pct(m2['global'])}** |",
        "",
        f"Procedencia completa en el cuadro: {_pct(m2['procedencia_completa'])}.",
        "",
        "## M1 Exactitud de extracción por ruta",
        "",
        "| Fuente | Ofertas (de listado) | Exactitud por campo | Sin correspondencia |",
        "|---|---|---|---|",
    ]
    for fuente, d in m1["por_fuente"].items():
        lineas.append(
            f"| {NOMBRE_FUENTE[fuente]} | {d['ofertas']} ({d['de_listado']}) | "
            f"{_pct(d['global'])} | {_pct(d['sin_correspondencia'])} |"
        )
    lineas += [
        f"| **Todas** | | **{_pct(m1['global'])}** | {_pct(m1['sin_correspondencia'])} |",
        "",
        f"Recolección (ofertas válidas de la tarea que llegaron al cuadro): "
        f"{_pct(m1['recoleccion'])}.",
        "",
        "Exactitud por campo y fuente:",
        "",
        "| Campo | " + " | ".join(NOMBRE_FUENTE[f] for f in m1["por_fuente"]) + " |",
        "|---|" + "---|" * len(m1["por_fuente"]),
    ]
    for campo in CAMPOS_SIEMPRE + CAMPOS_SI_PUBLICADOS:
        celdas = []
        for d in m1["por_fuente"].values():
            w = d["campos"].get(campo)
            celdas.append(f"{100 * w['p']:.0f} % ({w['k']}/{w['n']})" if w and w["n"] else "—")
        lineas.append(f"| {campo} | " + " | ".join(celdas) + " |")
    lineas += ["", "## M3 Acuerdo entre ejecuciones", ""]
    if m3["aplica"]:
        lineas += [
            f"{m3['repeticiones']} repeticiones. "
            f"Misma decisión en todas: {_pct(m3['acuerdo_total'])}.",
            f"M2 por repetición: {', '.join(f'{100 * x:.1f} %' for x in m3['m2_por_repeticion'])} "
            f"(rango {100 * m3['m2_rango']:.1f} puntos, "
            f"desviación {100 * m3['m2_desviacion']:.1f}).",
        ]
    else:
        lineas.append("No aplica: la corrida tiene una sola repetición.")
    lineas += [
        "",
        "## M4 Abstención",
        "",
        f"- Abstención correcta (se abstiene cuando debe): {_pct(m4['abstencion_correcta'])}",
        "- Abstención indebida (se abstiene habiendo respuesta): "
        f"{_pct(m4['abstencion_indebida'])}",
        f"- Cobertura (responde cuando hay respuesta): {_pct(m4['cobertura'])}",
        f"- Exactitud sobre lo cubierto: {_pct(m4['exactitud_cubierta'])}",
        "",
        "## M6 Costo y latencia",
        "",
        f"- Costo total: US${m6['costo_total']:.4f}",
        f"- Costo por tarea: media US${_num(m6['costo_medio'], '.4f')}; "
        f"p50 US${_num(m6['costo_p50'], '.4f')}; p90 US${_num(m6['costo_p90'], '.4f')}",
        f"- Latencia: p50 {_num(m6['latencia_p50'], '.0f')} s; "
        f"p90 {_num(m6['latencia_p90'], '.0f')} s",
    ]
    if m6["tokens_entrada_medio"] is not None:
        lineas.append(
            f"- Por tarea: {m6['tokens_entrada_medio']:.0f} tokens de entrada, "
            f"{m6['tokens_salida_medio']:.0f} de salida, {m6['llamadas_llm_medio']:.1f} llamadas "
            f"al LLM, {m6['herramientas_medio']:.1f} herramientas"
        )
    return re.sub(r"(\d)\.(\d)", r"\1,\2", "\n".join(lineas) + "\n")  # coma decimal


def _barras(ax, etiquetas: list[str], ws: list[dict], titulo: str) -> None:
    p = np.array([100 * (w["p"] or 0) for w in ws])
    bajo = np.array([100 * (w["bajo"] or 0) for w in ws])
    alto = np.array([100 * (w["alto"] or 0) for w in ws])
    barras = ax.bar(etiquetas, p, yerr=[p - bajo, alto - p], capsize=4, color="#4C72B0")
    ax.bar_label(
        barras, labels=[f"{x:.0f} %\n(n={w['n']})" for x, w in zip(p, ws, strict=True)], padding=2
    )
    ax.set_ylim(0, 115)
    ax.set_ylabel("%")
    ax.set_title(titulo)
    ax.tick_params(axis="x", labelrotation=15)


def graficos(m: dict[str, Any], directorio: Path, filas: list[dict]) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rutas = []
    fig, ax = plt.subplots(figsize=(7, 4))
    cats = m["M2"]["por_categoria"]
    _barras(ax, list(cats), list(cats.values()), "M2 éxito por categoría (IC 95 % Wilson)")
    fig.tight_layout()
    rutas.append(directorio / "m2_por_categoria.png")
    fig.savefig(rutas[-1], dpi=150)
    plt.close(fig)

    fuentes = m["M1"]["por_fuente"]
    if fuentes:
        fig, ax = plt.subplots(figsize=(7, 4))
        _barras(
            ax,
            [NOMBRE_FUENTE[f] for f in fuentes],
            [d["global"] for d in fuentes.values()],
            "M1 exactitud de extracción por fuente (campos)",
        )
        fig.tight_layout()
        rutas.append(directorio / "m1_por_fuente.png")
        fig.savefig(rutas[-1], dpi=150)
        plt.close(fig)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.5))
    a1.hist([f["segundos"] for f in filas if f.get("segundos")], bins=15, color="#55A868")
    a1.set_xlabel("segundos por tarea")
    a1.set_title("M6 latencia")
    a2.hist([f["costo_usd"] for f in filas if f.get("costo_usd")], bins=15, color="#C44E52")
    a2.set_xlabel("US$ por tarea")
    a2.set_title("M6 costo")
    fig.tight_layout()
    rutas.append(directorio / "m6_costo_latencia.png")
    fig.savefig(rutas[-1], dpi=150)
    plt.close(fig)
    return rutas


def nombre_corrida(ruta: Path) -> str:
    return ruta.name.removesuffix(".gz").removesuffix(".jsonl")


def cargar_corrida(ruta: Path) -> list[dict]:
    """Lee una corrida en ``.jsonl`` o comprimida en ``.jsonl.gz`` (la que se versiona)."""
    if ruta.suffix == ".gz":
        texto = gzip.decompress(ruta.read_bytes()).decode("utf-8")
    else:
        texto = ruta.read_text(encoding="utf-8")
    return [json.loads(x) for x in texto.splitlines() if x.strip()]


def informe(
    ruta: str | Path,
    directorio: Path | None = None,
    tareas: list[Tarea] | None = None,
    verdad: dict | None = None,
) -> Path:
    """Calcula las métricas de una corrida y escribe ``metricas.md``, ``metricas.json`` y PNG."""
    ruta = Path(ruta)
    filas = cargar_corrida(ruta)
    m = calcular(filas, tareas, verdad)
    directorio = directorio or DIR_INFORMES / nombre_corrida(ruta)
    directorio.mkdir(parents=True, exist_ok=True)
    (directorio / "metricas.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    texto = a_markdown(m)
    (directorio / "metricas.md").write_text(texto, encoding="utf-8")
    graficos(m, directorio, filas)
    print(texto)
    print(f"Informe en {directorio}")
    return directorio


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("corrida", help="Archivo JSONL de resultados/corridas/")
    informe(parser.parse_args().corrida)


if __name__ == "__main__":
    main()
