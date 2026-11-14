"""E1 con fallas sembradas (P4): N3 como detector cuando sí hay errores de extracción.

    uv run python -m comercio_agentico.arnes.e1_fallas   # US$0, sin red ni corpus servido

E1 no encontró errores de extracción en las ofertas ganadoras, así que N3 no tuvo nada que atrapar.
Aquí se siembran fallas conocidas en la primera extracción, una a la vez y en todas las ejecuciones
donde aplican, sobre las mismas corridas C1 de E1. La segunda lectura de N3 depende solo del
fragmento (caché por SHA-256 en ``resultados/e1/segundas_lecturas.jsonl``), no de lo que extrajo la
primera ruta: alterar la extracción no exige lecturas nuevas. El fragmento no se regenera porque E1
comprobó que el 100 % reproduce su suma.

Fallas (sobre todas las copias de la oferta en la ejecución):

- ``precio_baja`` y ``precio_sube``: precio de la ganadora × 0,9 y × 1,1.
- ``envio_omitido``: el envío de la ganadora (> 0) pasa a no informado.
- ``agotado_falso``: la ganadora pasa a ``agotado``.
- ``disponible_falso``: una oferta agotada pasa a ``en_stock`` (la más barata que así gane).

Una decisión es correcta si acierta la oferta (``evaluar``) y, cuando recomienda, cotiza el costo
total verdadero de esa oferta. Escribe ``resultados/informes/e1_fallas/``.
"""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from comercio_agentico.agente.grafo import proponer, proponer_con_n3
from comercio_agentico.agente.interpretacion import Necesidad
from comercio_agentico.arnes.correr import recursos_corpus
from comercio_agentico.arnes.e1 import CORRIDAS, POLITICAS, _de_dict, cargar_lecturas
from comercio_agentico.arnes.metricas import DIR_INFORMES, cargar_corrida, wilson
from comercio_agentico.corpus_b import RUTA_PERFIL
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.corpus_b.tareas import Tarea, cargar_tareas
from comercio_agentico.esquema import Oferta, cargar_perfil
from comercio_agentico.preguntar import evaluar
from comercio_agentico.verificacion import verificar_oferta

log = logging.getLogger("comercio_agentico.e1_fallas")
DIR_SALIDA = DIR_INFORMES / "e1_fallas"
FALLAS = ("precio_baja", "precio_sube", "envio_omitido", "agotado_falso", "disponible_falso")
# Favorecen a la oferta alterada (la hacen ganar o seguir ganando) o la perjudican (la sacan).
EFECTO = {
    "precio_baja": "favorece",
    "envio_omitido": "favorece",
    "disponible_falso": "favorece",
    "precio_sube": "perjudica",
    "agotado_falso": "perjudica",
}
NOMBRES_FALLA = {
    "ninguna": "Sin falla (control)",
    "precio_baja": "Precio -10 %",
    "precio_sube": "Precio +10 %",
    "envio_omitido": "Envío omitido",
    "agotado_falso": "Disponible leída como agotada",
    "disponible_falso": "Agotada leída como disponible",
}
NOMBRES_POLITICA = {"sin_n3": "Sin N3", "abstener": "N3 + abstención", "excluir": "N3 + exclusión"}
ETIQUETAS = {
    "precio_baja": "Precio\n-10 %",
    "precio_sube": "Precio\n+10 %",
    "envio_omitido": "Envío\nomitido",
    "agotado_falso": "Disponible\n→ agotada",
    "disponible_falso": "Agotada\n→ disponible",
}

Decidir = Callable[[list[Oferta], str], Any]


def _clave(o: Oferta) -> tuple:
    """Identidad de una oferta extraída (las copias de la misma lectura comparten la clave)."""
    return (o.proveedor, o.producto_catalogo, o.procedencia.suma_verificacion, o.precio)


def ofertas_de(fila: dict) -> list[Oferta]:
    """Ofertas registradas sin regenerar el fragmento: se conserva la suma registrada."""
    ofertas = []
    for o in fila.get("ofertas_todas", []):
        p = {**o["procedencia"], "fragmento_original": "-", "suma_verificacion": ""}
        oferta = Oferta.model_validate({**o, "procedencia": p})
        oferta.procedencia.suma_verificacion = o["procedencia"]["suma_verificacion"]
        ofertas.append(oferta)
    return ofertas


def _alterar(ofertas: list[Oferta], objetivo: Oferta, cambio: dict) -> tuple[list[Oferta], set]:
    clave = _clave(objetivo)
    nuevas = [o.model_copy(update=cambio) if _clave(o) == clave else o for o in ofertas]
    return nuevas, {i for i, o in enumerate(ofertas) if _clave(o) == clave}


def sembrar(
    falla: str, ofertas: list[Oferta], ganadora: Oferta | None, decidir: Decidir
) -> tuple[list[Oferta], set[int]] | None:
    """Ofertas con la falla y los índices alterados; None si la falla no aplica a la ejecución."""
    if falla == "disponible_falso":
        tope = ganadora.costo_total if ganadora else float("inf")
        candidatas = sorted(
            {_clave(o): o for o in ofertas if o.disponibilidad == "agotado"}.values(),
            key=lambda o: (o.costo_total, o.proveedor),
        )
        for c in candidatas:
            if c.costo_total >= tope:
                break
            nuevas, indices = _alterar(ofertas, c, {"disponibilidad": "en_stock"})
            p = decidir(nuevas, "sin_n3")
            if p.recomendada is not None and _clave(p.ofertas[p.recomendada]) == _clave(c):
                return nuevas, indices
        return None
    if ganadora is None:
        return None
    if falla == "precio_baja":
        cambio: dict[str, Any] = {"precio": round(ganadora.precio * 0.9)}
    elif falla == "precio_sube":
        cambio = {"precio": round(ganadora.precio * 1.1)}
    elif falla == "envio_omitido":
        if not ganadora.costo_envio:
            return None
        cambio = {"costo_envio": None}
    elif falla == "agotado_falso":
        cambio = {"disponibilidad": "agotado"}
    else:
        raise ValueError(falla)
    return _alterar(ofertas, ganadora, cambio)


def resultado(tarea: Tarea, propuesta, costos_verdad: dict[tuple, float]) -> str:
    """``correcta``, ``erronea`` (recomienda mal o cotiza mal) o ``abstencion_indebida``."""
    ev = evaluar(tarea, SimpleNamespace(propuesta=propuesta))  # type: ignore[arg-type]
    if ev["acierto"] and propuesta.recomendada is not None:
        o = propuesta.ofertas[propuesta.recomendada]
        verdadero = costos_verdad.get((o.proveedor, o.producto_catalogo))
        if verdadero is None or abs(o.costo_total - verdadero) >= 0.5:
            return "erronea"
    if ev["acierto"]:
        return "correcta"
    return "abstencion_indebida" if propuesta.abstencion else "erronea"


def _costos_verdad(verdad: dict) -> dict[tuple, float]:
    return {
        (o["proveedor"], o["producto_id"]): o["oferta"]["precio"]
        + (o["oferta"].get("costo_envio") or 0.0)
        for o in verdad["ofertas"]
    }


def correr_corpus(corpus: str, filas: list[dict], lecturas: dict[str, dict]) -> list[dict]:
    """Una fila por ejecución y falla (incluida ``ninguna``) con el resultado de cada política."""
    rec = recursos_corpus(corpus)
    tareas = {t.id: t for t in cargar_tareas(rec["tareas"])}
    productos = {p.id: p for p in cargar_catalogo(rec["catalogo"])}
    perfil = cargar_perfil(RUTA_PERFIL)
    costos = _costos_verdad(json.loads(Path(rec["verdad"]).read_text(encoding="utf-8")))
    salida = []

    for fila in filas:
        if fila.get("error") or not fila.get("necesidad"):
            continue
        tarea = tareas[fila["tarea"]]
        necesidad = Necesidad.model_validate(fila["necesidad"])
        alertas = (fila.get("propuesta") or {}).get("alertas") or []
        errores = [a["mensaje"] for a in alertas if a["tipo"] == "fuente_no_disponible"]
        consulta = fila["propuesta"]["consulta"]
        contexto = (consulta, necesidad, perfil, productos, errores)

        def decidir(ofertas: list[Oferta], politica: str, ctx: tuple = contexto):
            c, n, pf, pr, e = ctx
            args = (c, n, ofertas, pf, pr, e, "", 0.0)
            if politica == "sin_n3":
                return proponer(*args)
            return proponer_con_n3(*args, politica=politica)  # type: ignore[arg-type]

        def verificar(o: Oferta) -> Oferta:
            lectura = lecturas[o.procedencia.suma_verificacion]
            contrapartes = [_de_dict(c) for c in lectura["contrapartes"]]
            v = verificar_oferta(o, lectura["ruta"], contrapartes)
            return o.model_copy(update={"verificacion": v.estado})

        base = [verificar(o) for o in ofertas_de(fila)]
        p0 = decidir(base, "sin_n3")
        ganadora = p0.ofertas[p0.recomendada] if p0.recomendada is not None else None
        comun = {"corpus": corpus, "tarea": tarea.id, "categoria": fila["categoria"]}

        control = {p: resultado(tarea, decidir(base, p), costos) for p in POLITICAS}
        salida.append(
            {
                **comun,
                "falla": "ninguna",
                "acierto_original": fila["evaluacion"]["acierto"],
                "acierto_reproducido": evaluar(tarea, SimpleNamespace(propuesta=p0))["acierto"],
                "ganadora_marcada": ganadora is not None and ganadora.verificacion != "verificada",
                "resultados": control,
            }
        )
        for falla in FALLAS:
            sembrada = sembrar(falla, base, ganadora, decidir)
            if sembrada is None:
                continue
            ofertas, indices = sembrada
            ofertas = [verificar(o) if i in indices else o for i, o in enumerate(ofertas)]
            alterada = ofertas[min(indices)]
            lectura = lecturas[alterada.procedencia.suma_verificacion]
            salida.append(
                {
                    **comun,
                    "falla": falla,
                    "ruta": lectura["ruta"],
                    "tipo_fuente": alterada.procedencia.tipo_fuente,
                    "detectada": alterada.verificacion != "verificada",
                    "estado": alterada.verificacion,
                    "resultados": {
                        p: resultado(tarea, decidir(ofertas, p), costos) for p in POLITICAS
                    },
                }
            )
    return salida


# --------------------------------------------------------------------------------------------------
# Métricas e informe


def resumir(filas: list[dict]) -> dict[str, Any]:
    resumen: dict[str, Any] = {}
    for corpus in sorted({f["corpus"] for f in filas}, reverse=True):
        propias = [f for f in filas if f["corpus"] == corpus]
        control = [f for f in propias if f["falla"] == "ninguna"]
        por_falla: dict[str, Any] = {}
        for falla in ("ninguna", *FALLAS):
            fs = [f for f in propias if f["falla"] == falla]
            n = len(fs)
            entrada: dict[str, Any] = {"n": n}
            if falla != "ninguna":
                entrada["efecto"] = EFECTO[falla]
                entrada["detectada"] = wilson(sum(f["detectada"] for f in fs), n)
                entrada["detectada_por_ruta"] = {
                    r: [
                        sum(f["detectada"] for f in fs if f["ruta"] == r),
                        sum(f["ruta"] == r for f in fs),
                    ]
                    for r in sorted({f["ruta"] for f in fs})
                }
            erroneas_sin = [f for f in fs if f["resultados"]["sin_n3"] == "erronea"]
            entrada["politicas"] = {
                p: {
                    "correcta": wilson(sum(f["resultados"][p] == "correcta" for f in fs), n),
                    "erronea": wilson(sum(f["resultados"][p] == "erronea" for f in fs), n),
                    "abstencion_indebida": wilson(
                        sum(f["resultados"][p] == "abstencion_indebida" for f in fs), n
                    ),
                    "erroneas_evitadas": [
                        sum(f["resultados"][p] != "erronea" for f in erroneas_sin),
                        len(erroneas_sin),
                    ],
                }
                for p in POLITICAS
            }
            por_falla[falla] = entrada
        resumen[corpus] = {
            "ejecuciones": len(control),
            "control_reproduccion": wilson(
                sum(f["acierto_reproducido"] == f["acierto_original"] for f in control),
                len(control),
            ),
            "ganadoras": sum(f["falla"] == "agotado_falso" for f in propias),
            "falsas_alarmas_ganadoras": sum(f["ganadora_marcada"] for f in control),
            "fallas": por_falla,
        }
    return resumen


def _pct(w: dict) -> str:
    if not w.get("n"):
        return "—"
    return (
        f"{w['k']}/{w['n']} = {100 * w['p']:.1f} % [{100 * w['bajo']:.1f}; {100 * w['alto']:.1f}]"
    )


def a_markdown(resumen: dict[str, Any]) -> str:
    lineas = ["# E1 con fallas sembradas en la primera extracción (P4)", ""]
    for corpus, m in resumen.items():
        lineas += [
            f"## Corpus {corpus.upper()} — {m['ejecuciones']} ejecuciones, "
            f"{m['ganadoras']} con oferta ganadora",
            "",
            f"Control: la decisión sin N3 reproduce el acierto original en "
            f"{_pct(m['control_reproduccion'])}. Ganadoras sin falla marcadas por N3 "
            f"(falsas alarmas): {m['falsas_alarmas_ganadoras']}.",
            "",
            "| Falla | Efecto | n | Detectada por N3 | Por ruta (detectadas/total) |",
            "|---|---|--:|---|---|",
        ]
        for falla, e in m["fallas"].items():
            if falla == "ninguna":
                continue
            rutas = ", ".join(f"{r} {k}/{n}" for r, (k, n) in e["detectada_por_ruta"].items())
            lineas.append(
                f"| {NOMBRES_FALLA[falla]} | {e['efecto']} | {e['n']} | {_pct(e['detectada'])} | "
                f"{rutas or '—'} |"
            )
        lineas += [
            "",
            "| Falla | Política | Correcta | Errónea | Abstención indebida | Erróneas evitadas |",
            "|---|---|---|---|---|---|",
        ]
        for falla, e in m["fallas"].items():
            for p, t in e["politicas"].items():
                k, n = t["erroneas_evitadas"]
                evitadas = "—" if p == "sin_n3" or not n else f"{k}/{n}"
                lineas.append(
                    f"| {NOMBRES_FALLA[falla]} | {NOMBRES_POLITICA[p]} | {_pct(t['correcta'])} | "
                    f"{_pct(t['erronea'])} | {_pct(t['abstencion_indebida'])} | {evitadas} |"
                )
        lineas.append("")
    return "\n".join(lineas)


def grafico(resumen: dict[str, Any], ruta: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ejes = plt.subplots(1, len(resumen), figsize=(5.2 * len(resumen), 4.2), sharey=True)
    ejes = ejes if len(resumen) > 1 else [ejes]
    ancho = 0.27
    for ax, (corpus, m) in zip(ejes, resumen.items(), strict=True):
        fallas = [f for f in FALLAS if m["fallas"][f]["n"]]
        for j, p in enumerate(POLITICAS):
            valores = [100 * m["fallas"][f]["politicas"][p]["erronea"]["p"] for f in fallas]
            posiciones = [i + (j - 1) * ancho for i in range(len(fallas))]
            ax.bar(posiciones, valores, ancho, label=NOMBRES_POLITICA[p])
        ax.set_xticks(range(len(fallas)))
        ax.set_xticklabels(
            [f"{ETIQUETAS[f]}\n(n={m['fallas'][f]['n']})" for f in fallas], fontsize=7
        )
        ax.set_title(f"Corpus {corpus.upper()}")
        ax.grid(axis="y", alpha=0.3)
    ejes[0].set_ylabel("Recomendaciones erróneas (%)")
    manejadores, nombres = ejes[0].get_legend_handles_labels()
    fig.legend(manejadores, nombres, loc="lower center", ncol=3, fontsize=8)
    fig.suptitle("E1 con fallas sembradas: recomendaciones erróneas por política")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def principal() -> Path:
    lecturas = cargar_lecturas()
    filas: list[dict] = []
    for corpus, ruta in CORRIDAS.items():
        corrida = cargar_corrida(ruta)
        sumas = {
            o["procedencia"]["suma_verificacion"]
            for f in corrida
            for o in f.get("ofertas_todas", [])
        }
        if faltan := sumas - set(lecturas):
            raise SystemExit(f"Faltan {len(faltan)} segundas lecturas; corra make e1-lecturas")
        filas += correr_corpus(corpus, corrida, lecturas)
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    resumen = resumir(filas)
    (DIR_SALIDA / "e1_fallas.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    with (DIR_SALIDA / "ejecuciones.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in filas)
    texto = a_markdown(resumen)
    (DIR_SALIDA / "e1_fallas.md").write_text(texto, encoding="utf-8")
    grafico(resumen, DIR_SALIDA / "e1_fallas.png")
    print(texto)
    print(f"Informe en {DIR_SALIDA}")
    return DIR_SALIDA


def main() -> None:
    argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    ).parse_args()
    logging.basicConfig(format="%(message)s")
    principal()


if __name__ == "__main__":
    main()
