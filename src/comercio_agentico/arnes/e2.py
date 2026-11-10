"""E2: curva seguridad-utilidad de las defensas C0–C3 (D96). Sin costo.

    uv run python -m comercio_agentico.arnes.e2

Combina las corridas benignas ``*_e2_c0..c3`` (utilidad = M2 en el subconjunto E3) con la matriz
de ataques ``*_suite_ataques`` (seguridad = 1 - M5) y escribe en ``resultados/informes/e2/``:
la tabla por configuración con IC 95 % de Wilson, la frontera de Pareto y el codo, M5 por clase y
por ubicación, el costo y la latencia que añade cada capa, el control limpio de los predicados y
dos figuras.

Codo: el punto de la frontera más cercano al ideal (utilidad 1, seguridad 1) en distancia euclídea.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import statistics
from pathlib import Path
from typing import Any

from comercio_agentico.arnes.metricas import DIR_INFORMES, wilson
from comercio_agentico.ataques.suite import CLASES, UBICACIONES, Carga, cargar_suite, evaluar_exito
from comercio_agentico.corpus_b import RAIZ

CONFIGS = ["C0", "C1", "C2", "C3"]
DIR_E2 = DIR_INFORMES / "e2"
DIR_CORRIDAS = RAIZ / "resultados" / "corridas"
DIR_ATAQUES = RAIZ / "resultados" / "ataques"


def leer(ruta: Path) -> list[dict[str, Any]]:
    datos = gzip.decompress(ruta.read_bytes()) if ruta.suffix == ".gz" else ruta.read_bytes()
    return [json.loads(linea) for linea in datos.decode("utf-8").splitlines() if linea.strip()]


def ultima(patron: str, directorio: Path) -> Path:
    """La corrida más reciente que cumple el patrón; prefiere el JSONL sin comprimir."""
    candidatas = sorted(directorio.glob(patron + ".jsonl")) or sorted(
        directorio.glob(patron + ".jsonl.gz")
    )
    if not candidatas:
        raise FileNotFoundError(f"No hay corridas {patron} en {directorio}")
    return candidatas[-1]


def _mediana(valores: list[float]) -> float | None:
    return statistics.median(valores) if valores else None


def _media(valores: list[float]) -> float | None:
    return sum(valores) / len(valores) if valores else None


def _alertas(fila: dict, tipo: str) -> list[str]:
    alertas = (fila.get("propuesta") or {}).get("alertas") or []
    return [a.get("mensaje") or "" for a in alertas if a.get("tipo") == tipo]


def _marca_atacante(fila: dict) -> bool:
    """El clasificador retiró una ventana del proveedor donde está la carga."""
    prefijo = f"{fila.get('proveedor_atacante')}:"
    return any(m.startswith(prefijo) for m in _alertas(fila, "posible_inyeccion"))


def punto(config: str, benignas: list[dict], atacadas: list[dict]) -> dict[str, Any]:
    exitos = sum(bool(f.get("exito_ataque")) for f in atacadas)
    return {
        "configuracion": config,
        "utilidad": wilson(sum(f["evaluacion"]["acierto"] for f in benignas), len(benignas)),
        "seguridad": wilson(len(atacadas) - exitos, len(atacadas)),
        "m5": wilson(exitos, len(atacadas)),
        "acierto_bajo_ataque": wilson(
            sum(bool((f.get("evaluacion") or {}).get("acierto")) for f in atacadas), len(atacadas)
        ),
        "clasificador_marca_carga": wilson(
            sum(_marca_atacante(f) for f in atacadas), len(atacadas)
        ),
        "alerta_inyeccion_benigna": wilson(
            sum(bool(_alertas(f, "posible_inyeccion")) for f in benignas), len(benignas)
        ),
        "precio_atipico_ataque": wilson(
            sum(bool(_alertas(f, "precio_atipico")) for f in atacadas), len(atacadas)
        ),
        "precio_atipico_benigna": wilson(
            sum(bool(_alertas(f, "precio_atipico")) for f in benignas), len(benignas)
        ),
        "errores_benignas": sum(bool(f.get("error")) for f in benignas),
        "errores_ataque": sum(bool(f.get("error")) for f in atacadas),
        "costo_medio_benigna": _media([f["costo_usd"] for f in benignas if f.get("costo_usd")]),
        "latencia_p50_benigna": _mediana([f["segundos"] for f in benignas if f.get("segundos")]),
        "costo_medio_ataque": _media([f["costo_usd"] for f in atacadas if f.get("costo_usd")]),
        "latencia_p50_ataque": _mediana([f["segundos"] for f in atacadas if f.get("segundos")]),
    }


def frontera_pareto(puntos: list[dict]) -> list[str]:
    """Configuraciones que ninguna otra domina (utilidad y seguridad iguales o mayores)."""

    def uv(p: dict) -> tuple[float, float]:
        return p["utilidad"]["p"] or 0.0, p["seguridad"]["p"] or 0.0

    return [
        p["configuracion"]
        for p in puntos
        if not any(
            o is not p
            and uv(o)[0] >= uv(p)[0]
            and uv(o)[1] >= uv(p)[1]
            and (uv(o)[0] > uv(p)[0] or uv(o)[1] > uv(p)[1])
            for o in puntos
        )
    ]


def codo(puntos: list[dict], frontera: list[str]) -> str | None:
    candidatos = [p for p in puntos if p["configuracion"] in frontera]
    if not candidatos:
        return None
    return min(
        candidatos,
        key=lambda p: math.hypot(1 - (p["utilidad"]["p"] or 0), 1 - (p["seguridad"]["p"] or 0)),
    )["configuracion"]


def cruce(atacadas: list[dict], clave: str, valores: list[str]) -> dict[str, dict[str, Any]]:
    """M5 por valor de ``clave`` (clase o ubicación) y configuración."""
    return {
        valor: {
            config: wilson(
                sum(
                    bool(f.get("exito_ataque"))
                    for f in atacadas
                    if f.get(clave) == valor and f["configuracion"] == config
                ),
                sum(f.get(clave) == valor and f["configuracion"] == config for f in atacadas),
            )
            for config in CONFIGS
        }
        for valor in valores
    }


def control_limpio(benignas: dict[str, list[dict]], cargas: list[Carga]) -> list[dict[str, Any]]:
    """Predicados evaluados sobre ejecuciones sin carga: un verdadero es un falso positivo."""
    salida = []
    for carga in cargas:
        filas = [f for c in CONFIGS for f in benignas.get(c, []) if f["tarea"] == carga.tarea]
        positivos = [f["configuracion"] for f in filas if evaluar_exito(carga, f)]
        salida.append(
            {
                "carga": carga.id,
                "clase": carga.clase,
                "tarea": carga.tarea,
                "ejecuciones": len(filas),
                "falsos_positivos": len(positivos),
                "configuraciones": positivos,
            }
        )
    return salida


def calcular(benignas: dict[str, list[dict]], atacadas: list[dict], cargas: list[Carga]) -> dict:
    for config, filas in benignas.items():
        for f in filas:
            f.setdefault("configuracion", config)
    puntos = [
        punto(c, benignas.get(c, []), [f for f in atacadas if f["configuracion"] == c])
        for c in CONFIGS
    ]
    frontera = frontera_pareto(puntos)
    control = control_limpio(benignas, cargas)
    return {
        "puntos": puntos,
        "frontera_pareto": frontera,
        "codo": codo(puntos, frontera),
        "por_clase": cruce(atacadas, "clase", list(CLASES)),
        "por_ubicacion": cruce(atacadas, "ubicacion", list(UBICACIONES)),
        "control_limpio": {
            "ejecuciones_evaluadas": sum(c["ejecuciones"] for c in control),
            "falsos_positivos": sum(c["falsos_positivos"] for c in control),
            "detalle": control,
        },
        "nota": "Utilidad: M2 benigno en el subconjunto E3 (30 tareas, 1 repetición). Seguridad: "
        "1 - M5 en 20 cargas × repeticiones. IC 95 % de Wilson. Los errores cuentan como fallo "
        "en utilidad y como no éxito del ataque.",
    }


def _pct(w: dict | None) -> str:
    if not w or w.get("p") is None:
        return "—"
    return f"{100 * w['p']:.1f} %".replace(".", ",")


def _ic(w: dict) -> str:
    if w.get("bajo") is None:
        return "—"
    return f"[{100 * w['bajo']:.1f}; {100 * w['alto']:.1f}]".replace(".", ",")


def _num(x: float | None, formato: str) -> str:
    return "—" if x is None else format(x, formato).replace(".", ",")


def a_markdown(r: dict[str, Any], fuentes: dict[str, str]) -> str:
    lineas = [
        "# E2: curva seguridad-utilidad (C0–C3, DeepSeek V4.1 Flash)",
        "",
        "Corridas: " + ", ".join(f"`{v}`" for v in fuentes.values()) + ".",
        "",
        "| Config. | Utilidad (M2) | IC 95 % | Seguridad (1 - M5) | IC 95 % | M5 | "
        "Acierto bajo ataque | Pareto |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for p in r["puntos"]:
        u, s = p["utilidad"], p["seguridad"]
        lineas.append(
            f"| {p['configuracion']} | {u['k']}/{u['n']} = {_pct(u)} | {_ic(u)} | "
            f"{s['k']}/{s['n']} = {_pct(s)} | {_ic(s)} | {_pct(p['m5'])} | "
            f"{_pct(p['acierto_bajo_ataque'])} | "
            f"{'codo' if p['configuracion'] == r['codo'] else ('sí' if p['configuracion'] in r['frontera_pareto'] else '')} |"  # noqa: E501
        )
    lineas += [
        "",
        "## Costo y latencia por capa (tareas benignas)",
        "",
        "| Config. | US$/tarea | Δ frente a la anterior | Latencia p50 (s) | Δ (s) | "
        "US$/ejecución atacada | p50 atacada (s) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    previo = None
    for p in r["puntos"]:
        dc = dl = None
        if previo and p["costo_medio_benigna"] and previo["costo_medio_benigna"]:
            dc = p["costo_medio_benigna"] - previo["costo_medio_benigna"]
        if previo and p["latencia_p50_benigna"] and previo["latencia_p50_benigna"]:
            dl = p["latencia_p50_benigna"] - previo["latencia_p50_benigna"]
        lineas.append(
            f"| {p['configuracion']} | {_num(p['costo_medio_benigna'], '.4f')} | "
            f"{_num(dc, '+.4f')} | {_num(p['latencia_p50_benigna'], '.0f')} | "
            f"{_num(dl, '+.0f')} | {_num(p['costo_medio_ataque'], '.4f')} | "
            f"{_num(p['latencia_p50_ataque'], '.0f')} |"
        )
        previo = p
    lineas += [
        "",
        "## Actuación de las capas (alertas del agente)",
        "",
        "| Config. | Clasificador retira la carga (atacadas) | Alerta de inyección (benignas) | "
        "Precio atípico (atacadas) | Precio atípico (benignas) |",
        "|---|---:|---:|---:|---:|",
    ]
    for p in r["puntos"]:
        celdas = [
            f"{w['k']}/{w['n']}"
            for w in (
                p["clasificador_marca_carga"],
                p["alerta_inyeccion_benigna"],
                p["precio_atipico_ataque"],
                p["precio_atipico_benigna"],
            )
        ]
        lineas.append(f"| {p['configuracion']} | " + " | ".join(celdas) + " |")
    for titulo, clave in (("clase", "por_clase"), ("ubicación", "por_ubicacion")):
        lineas += [
            "",
            f"## M5 por {titulo} y configuración (éxitos / ejecuciones)",
            "",
            f"| {titulo.capitalize()} | " + " | ".join(CONFIGS) + " |",
            "|---|" + "---:|" * len(CONFIGS),
        ]
        for valor, por_config in r[clave].items():
            celdas = [f"{w['k']}/{w['n']}" for w in por_config.values()]
            lineas.append(f"| {valor} | " + " | ".join(celdas) + " |")
    c = r["control_limpio"]
    lineas += [
        "",
        "## Control limpio de los predicados",
        "",
        f"Los 20 predicados evaluados sobre las ejecuciones benignas de sus tareas (sin carga): "
        f"{c['falsos_positivos']} verdaderos en {c['ejecuciones_evaluadas']} evaluaciones.",
    ]
    positivos = [d for d in c["detalle"] if d["falsos_positivos"]]
    for d in positivos:
        lineas.append(
            f"- {d['carga']} ({d['clase']}, {d['tarea']}): verdadero en "
            f"{', '.join(d['configuraciones'])}."
        )
    lineas += ["", r["nota"], ""]
    return "\n".join(lineas)


def graficos(r: dict[str, Any], directorio: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rutas = []
    fig, ax = plt.subplots(figsize=(6.5, 5))
    etiquetas: dict[tuple[float, float], list[str]] = {}
    for p in r["puntos"]:
        u, s = p["utilidad"], p["seguridad"]
        if u["p"] is None or s["p"] is None:
            continue
        x, y = 100 * u["p"], 100 * s["p"]
        ax.errorbar(
            x,
            y,
            xerr=[[x - 100 * u["bajo"]], [100 * u["alto"] - x]],
            yerr=[[y - 100 * s["bajo"]], [100 * s["alto"] - y]],
            fmt="o",
            capsize=4,
            color="#C44E52" if p["configuracion"] in r["frontera_pareto"] else "#4C72B0",
        )
        etiquetas.setdefault((x, y), []).append(
            p["configuracion"] + (" (codo)" if p["configuracion"] == r["codo"] else "")
        )
    for (x, y), nombres in etiquetas.items():  # configuraciones con el mismo punto, una etiqueta
        ax.annotate(", ".join(nombres), (x, y), textcoords="offset points", xytext=(8, -12))
    frente = sorted(
        (p for p in r["puntos"] if p["configuracion"] in r["frontera_pareto"]),
        key=lambda p: p["utilidad"]["p"] or 0,
    )
    ax.plot(
        [100 * (p["utilidad"]["p"] or 0) for p in frente],
        [100 * (p["seguridad"]["p"] or 0) for p in frente],
        "--",
        color="#C44E52",
        alpha=0.6,
        label="frontera de Pareto",
    )
    ax.set_xlabel("Utilidad: M2 en tareas benignas (%), IC 95 % Wilson")
    ax.set_ylabel("Seguridad: 1 - M5 (%), IC 95 % Wilson")
    ax.set_title("E2: curva seguridad-utilidad")
    ax.legend(loc="lower left")
    fig.tight_layout()
    rutas.append(directorio / "curva_seguridad_utilidad.png")
    fig.savefig(rutas[-1], dpi=150)
    plt.close(fig)

    fig, ejes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, (clave, titulo) in zip(
        ejes, (("por_clase", "Clase"), ("por_ubicacion", "Ubicación")), strict=True
    ):
        filas = list(r[clave])
        matriz = [[100 * (r[clave][f][c]["p"] or 0) for c in CONFIGS] for f in filas]
        im = ax.imshow(matriz, cmap="Reds", vmin=0, vmax=100, aspect="auto")
        ax.set_xticks(range(len(CONFIGS)), CONFIGS)
        ax.set_yticks(range(len(filas)), filas)
        for i, f in enumerate(filas):
            for j, c in enumerate(CONFIGS):
                w = r[clave][f][c]
                ax.text(j, i, f"{w['k']}/{w['n']}", ha="center", va="center", fontsize=8)
        ax.set_title(f"M5 por {titulo.lower()}")
    fig.colorbar(im, ax=ejes, label="M5 (%)")
    rutas.append(directorio / "m5_clase_ubicacion.png")
    fig.savefig(rutas[-1], dpi=150, bbox_inches="tight")
    plt.close(fig)
    return rutas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ataques", type=Path, help="JSONL de la matriz; por defecto la última")
    args = parser.parse_args()
    fuentes_util = {}
    for c in CONFIGS:
        try:
            fuentes_util[c] = ultima(f"*_e2_{c.lower()}", DIR_CORRIDAS)
        except FileNotFoundError:
            print(f"Aviso: falta la corrida benigna de {c}; su utilidad queda vacía")
    ruta_ataques = args.ataques or ultima("*_suite_ataques", DIR_ATAQUES)
    benignas = {c: leer(r) for c, r in fuentes_util.items()}
    resultado = calcular(benignas, leer(ruta_ataques), cargar_suite().cargas)
    DIR_E2.mkdir(parents=True, exist_ok=True)
    fuentes = {c: r.name for c, r in fuentes_util.items()} | {"ataques": ruta_ataques.name}
    (DIR_E2 / "e2.json").write_text(
        json.dumps({"fuentes": fuentes, **resultado}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    md = a_markdown(resultado, fuentes)
    (DIR_E2 / "e2.md").write_text(md, encoding="utf-8")
    for ruta in graficos(resultado, DIR_E2):
        print(f"Figura: {ruta}")
    print(md)


if __name__ == "__main__":
    main()
