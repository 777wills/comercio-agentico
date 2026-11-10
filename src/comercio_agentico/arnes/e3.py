"""E3: comparación de modelos con escalamiento y regla de parada (D31, D42, D77). Sin costo.

    uv run python -m comercio_agentico.arnes.e3

Lee las métricas de las corridas ``*_e3_<modelo>`` (subconjunto de 30 tareas × 3 repeticiones),
las ordena según D31 y escribe en ``resultados/informes/e3/`` la tabla comparativa, la decisión de
la regla de parada en cada paso y la figura de la frontera costo-desempeño.

Regla (D77): el ruido es el mayor rango de M2 entre repeticiones de los dos modelos comparados; se
sube al siguiente modelo solo si el último supera al mejor ya medido, en la media de M2 o en la
abstención correcta, por más que ese ruido.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from comercio_agentico.arnes.metricas import DIR_INFORMES

ORDEN_D31 = ["deepseek-flash", "haiku", "deepseek-pro", "kimi", "sonnet", "opus"]
DIR_E3 = DIR_INFORMES / "e3"


@dataclass
class Paso:
    modelo: str
    corrida: str
    m2_media: float  # media de M2 entre repeticiones
    m2_rango: float  # máximo menos mínimo de M2 entre repeticiones
    m2_bajo: float  # IC 95 % de Wilson sobre todas las ejecuciones
    m2_alto: float
    ejecuciones: int
    abstencion_correcta: float
    acuerdo_total: float | None
    costo_medio: float
    latencia_p50: float | None


@dataclass
class Veredicto:
    modelo: str
    frente_a: str  # mejor modelo ya medido
    ruido: float
    delta_m2: float
    delta_abstencion: float
    sube: bool


def paso_desde_metricas(m: dict[str, Any]) -> Paso:
    m3, m2 = m["M3"], m["M2"]["global"]
    reps = m3.get("m2_por_repeticion") or [m2["p"]]
    return Paso(
        modelo=m["meta"]["modelo"],
        corrida=m["meta"]["corrida"],
        m2_media=sum(reps) / len(reps),
        m2_rango=m3.get("m2_rango", 0.0),
        m2_bajo=m2["bajo"],
        m2_alto=m2["alto"],
        ejecuciones=m2["n"],
        abstencion_correcta=m["M4"]["abstencion_correcta"]["p"] or 0.0,
        acuerdo_total=(m3.get("acuerdo_total") or {}).get("p"),
        costo_medio=m["M6"]["costo_medio"]["valor"] or 0.0,
        latencia_p50=m["M6"]["latencia_p50"].get("valor"),
    )


def regla_parada(pasos: list[Paso]) -> list[Veredicto]:
    """Aplica D77 en orden. El primer modelo siempre se mide y siempre se sube al segundo; cada
    veredicto dice si, con lo medido hasta ese modelo, se justifica correr el siguiente."""
    veredictos: list[Veredicto] = []
    mejor = pasos[0] if pasos else None
    for actual in pasos[1:]:
        assert mejor is not None
        ruido = max(mejor.m2_rango, actual.m2_rango)
        d_m2 = actual.m2_media - mejor.m2_media
        d_ab = actual.abstencion_correcta - mejor.abstencion_correcta
        veredictos.append(
            Veredicto(actual.modelo, mejor.modelo, ruido, d_m2, d_ab, d_m2 > ruido or d_ab > ruido)
        )
        if actual.m2_media > mejor.m2_media:  # en empate se queda el más barato (el anterior)
            mejor = actual
    return veredictos


def frontera_pareto(pasos: list[Paso]) -> list[str]:
    """Modelos que ningún otro domina (más barato y con M2 igual o mayor)."""
    return [
        p.modelo
        for p in pasos
        if not any(
            o is not p
            and o.costo_medio <= p.costo_medio
            and o.m2_media >= p.m2_media
            and (o.costo_medio < p.costo_medio or o.m2_media > p.m2_media)
            for o in pasos
        )
    ]


def cargar_pasos(directorio: Path = DIR_INFORMES) -> list[Paso]:
    pasos = [
        paso_desde_metricas(json.loads(r.read_text(encoding="utf-8")))
        for r in sorted(directorio.glob("*_e3_*/metricas.json"))
    ]
    return sorted(pasos, key=lambda p: ORDEN_D31.index(p.modelo))


def _coma(texto: str) -> str:
    return texto.replace(".", ",")


def _pct(x: float | None) -> str:
    return "—" if x is None else _coma(f"{100 * x:.1f} %")


def a_markdown(pasos: list[Paso], veredictos: list[Veredicto], pareto: list[str]) -> str:
    lineas = [
        "# E3: comparación de modelos (subconjunto de 30 tareas × 3 repeticiones)",
        "",
        "| Modelo | M2 media | IC 95 % | Rango M2 | Abst. correcta | Acuerdo M3 | US$/tarea "
        "| Latencia p50 (s) | Pareto |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for p in pasos:
        lineas.append(
            f"| {p.modelo} | {_pct(p.m2_media)} "
            f"| {_pct(p.m2_bajo).removesuffix(' %')}–{_pct(p.m2_alto)} "
            f"| {_coma(f'{100 * p.m2_rango:.1f}')} pp | {_pct(p.abstencion_correcta)} "
            f"| {_pct(p.acuerdo_total)} | {_coma(f'{p.costo_medio:.4f}')} "
            f"| {'—' if p.latencia_p50 is None else f'{p.latencia_p50:.0f}'} "
            f"| {'sí' if p.modelo in pareto else ''} |"
        )
    lineas += ["", "## Regla de parada (D77)", ""]
    if pasos:
        lineas.append(f"- {pasos[0].modelo}: primer paso; se mide siempre y se sube al siguiente.")
    for v in veredictos:
        lineas.append(
            _coma(
                f"- {v.modelo} frente a {v.frente_a}: ΔM2 = {100 * v.delta_m2:+.1f} pp, "
                f"Δabstención = {100 * v.delta_abstencion:+.1f} pp, ruido = {100 * v.ruido:.1f} pp "
            )
            + f"→ **{'se sube' if v.sube else 'se para'}**."
        )
    return "\n".join(lineas) + "\n"


def grafico_frontera(pasos: list[Paso], pareto: list[str], ruta: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, p in enumerate(pasos):
        y = 100 * p.m2_media
        ax.errorbar(
            p.costo_medio,
            y,
            yerr=[[y - 100 * p.m2_bajo], [100 * p.m2_alto - y]],
            fmt="o",
            capsize=4,
            color="#C44E52" if p.modelo in pareto else "#4C72B0",
        )
        izquierda = i % 2 == 0  # alterna el lado para que no se pisen modelos de costo parecido
        ax.annotate(
            p.modelo,
            (p.costo_medio, y),
            textcoords="offset points",
            xytext=(-8, 0) if izquierda else (8, 0),
            ha="right" if izquierda else "left",
            va="center",
        )
    frente = sorted((p for p in pasos if p.modelo in pareto), key=lambda p: p.costo_medio)
    ax.plot(
        [p.costo_medio for p in frente],
        [100 * p.m2_media for p in frente],
        "--",
        color="#C44E52",
        alpha=0.6,
        label="frontera de Pareto",
    )
    ax.set_xscale("log")
    ax.set_xlim(0.005, 1.0)  # del modelo más barato al tope del costo por tarea (US$0,50-1,00)
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:g}".replace(".", ","))
    )
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("US$ por tarea (escala logarítmica)")
    ax.set_ylabel("M2 éxito (%), IC 95 % Wilson")
    ax.set_title("E3: frontera costo-desempeño")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


def main() -> None:
    pasos = cargar_pasos()
    if not pasos:
        raise SystemExit("No hay corridas *_e3_* con métricas en resultados/informes/")
    veredictos = regla_parada(pasos)
    pareto = frontera_pareto(pasos)
    DIR_E3.mkdir(parents=True, exist_ok=True)
    texto = a_markdown(pasos, veredictos, pareto)
    (DIR_E3 / "e3.md").write_text(texto, encoding="utf-8")
    (DIR_E3 / "e3.json").write_text(
        json.dumps(
            {
                "pasos": [asdict(p) for p in pasos],
                "veredictos": [asdict(v) for v in veredictos],
                "pareto": pareto,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    grafico_frontera(pasos, pareto, DIR_E3 / "frontera.png")
    print(texto)
    print(f"Informe en {DIR_E3}")


if __name__ == "__main__":
    main()
