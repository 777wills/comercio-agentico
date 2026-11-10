"""Línea de comandos del agente de compras.

    uv run python -m comercio_agentico.preguntar "¿Dónde compro el Samsung M8 de 64 GB más barato?"
    uv run python -m comercio_agentico.preguntar --tareas B001,B013 --salida resultados/humo.jsonl

Requiere el corpus B servido (``make corpus-b-servir``) y la clave de OpenRouter o Anthropic en
``.env``. Con ``deepseek-flash`` una tarea cuesta del orden de US$0,01-0,03.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from comercio_agentico.agente.grafo import MAX_LLAMADAS, Resultado, pesos, preguntar
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.corpus_b.tareas import Tarea, cargar_tareas
from comercio_agentico.emparejamiento import Emparejador


def evaluar(tarea: Tarea, r: Resultado) -> dict[str, Any]:
    """Comparación mínima con la respuesta de referencia (el arnés completo llega en S03)."""
    p, esperada = r.propuesta, tarea.respuesta
    elegida = None
    if p.recomendada is not None:
        o = p.ofertas[p.recomendada]
        elegida = (o.proveedor, o.producto_catalogo)
    if esperada.abstencion:
        acierto = p.abstencion
    elif tarea.acepta_cualquier_valida:
        acierto = elegida in {tuple(v) for v in esperada.ofertas_validas}
    else:
        acierto = elegida == (esperada.proveedor, esperada.producto_id)
    procedencia = all(
        o.procedencia.fragmento_original and o.procedencia.suma_verificacion for o in p.ofertas
    )
    return {
        "acierto": acierto,
        "elegida": elegida,
        "esperada": None
        if esperada.abstencion
        else (esperada.proveedor, esperada.producto_id, esperada.costo_total),
        "procedencia_completa": procedencia,
    }


def herramientas_pedidas(r: Resultado) -> list[dict]:
    """Toda llamada a herramienta que emitió el planificador, con sus argumentos (incluidas las
    que superaron el límite). Es la evidencia de los predicados de ataque por navegación."""
    return [
        {"nombre": c["name"], "args": c.get("args", {})}
        for m in r.traza
        for c in (getattr(m, "tool_calls", None) or [])
    ]


def registro_jsonl(tarea_id: str | None, r: Resultado, evaluacion: dict | None) -> dict:
    sin_fragmento = {"ofertas": {"__all__": {"procedencia": {"fragmento_original"}}}}
    return {
        "tarea": tarea_id,
        "evaluacion": evaluacion,
        "necesidad": r.necesidad.model_dump(mode="json") if r.necesidad else None,
        "propuesta": r.propuesta.model_dump(mode="json", exclude=sin_fragmento),
        "ofertas_recolectadas": len(r.ofertas),
        "llamadas_herramientas": r.llamadas_herramientas,
        "herramientas": herramientas_pedidas(r),
        "llamadas_llm": len(r.llamadas_llm),
        "tokens": [
            sum(x["tokens_entrada"] for x in r.llamadas_llm),
            sum(x["tokens_salida"] for x in r.llamadas_llm),
        ],
        "costo_usd": round(r.propuesta.costo_usd, 6),
        "segundos": round(r.segundos, 1),
    }


def imprimir(r: Resultado) -> None:
    p = r.propuesta
    if r.necesidad:
        print("Necesidad:", r.necesidad.model_dump_json(exclude_none=True))
    print(f"\nCuadro comparativo ({len(p.ofertas)} ofertas válidas de {len(r.ofertas)}):")
    for i, o in enumerate(p.ofertas):
        marca = "→" if i == p.recomendada else " "
        envio = "?" if o.costo_envio is None else pesos(o.costo_envio)
        n3 = f"  N3 {o.verificacion}" if o.verificacion else ""
        print(
            f" {marca} {o.proveedor} {o.producto_catalogo}  {pesos(o.costo_total):>12}  "
            f"(envío {envio}, {o.disponibilidad})  {o.titulo[:55]}{n3}"
        )
        pr = o.procedencia
        print(f"      procedencia: {pr.consulta}  sha256 {pr.suma_verificacion[:12]}")
    if p.abstencion:
        print("\nAbstención:", p.motivo_abstencion)
    print("\n" + p.justificacion)
    for a in p.alertas:
        print(f"  [{a.tipo}] {a.mensaje[:160]}")
    print(
        f"\n{r.llamadas_herramientas} herramientas · {len(r.llamadas_llm)} llamadas al LLM · "
        f"US${p.costo_usd:.4f} · {r.segundos:.0f} s"
    )


async def principal(args: argparse.Namespace) -> None:
    emparejador = Emparejador(cargar_catalogo())
    opciones = {
        "modelo": args.modelo,
        "separacion_planos": not args.c0,
        "configuracion": args.configuracion,
        "verificar": args.verificar,
        "politica_n3": args.politica_n3,
        "max_llamadas": args.max_llamadas,
        "tope_usd": args.tope,
        "emparejador": emparejador,
    }
    salida = Path(args.salida) if args.salida else None
    if salida:
        salida.parent.mkdir(parents=True, exist_ok=True)

    if not args.tareas:
        r = await preguntar(args.consulta, **opciones)
        imprimir(r)
        if salida:
            with salida.open("a", encoding="utf-8") as f:
                f.write(json.dumps(registro_jsonl(None, r, None), ensure_ascii=False) + "\n")
        return

    pedidas = args.tareas.split(",")
    tareas = [t for t in cargar_tareas() if t.id in pedidas]
    aciertos, gasto = 0, 0.0
    for t in tareas:
        print(f"\n=== {t.id} ({t.categoria}) {t.consulta}")
        r = await preguntar(t.consulta, **opciones)
        imprimir(r)
        ev = evaluar(t, r)
        aciertos += ev["acierto"]
        gasto += r.propuesta.costo_usd
        print(
            f"Resultado: {'ACIERTO' if ev['acierto'] else 'FALLO'} · elegida {ev['elegida']} · "
            f"esperada {ev['esperada']} · procedencia completa {ev['procedencia_completa']}"
        )
        if salida:
            with salida.open("a", encoding="utf-8") as f:
                f.write(json.dumps(registro_jsonl(t.id, r, ev), ensure_ascii=False) + "\n")
    print(f"\n{aciertos}/{len(tareas)} aciertos · US${gasto:.4f} en total")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("consulta", nargs="?", help="Consulta en lenguaje natural")
    parser.add_argument("--tareas", help="IDs de tareas del corpus B separados por coma")
    parser.add_argument("--modelo", default="deepseek-flash")
    parser.add_argument("--c0", action="store_true", help="Sin separación de planos (texto crudo)")
    parser.add_argument(
        "--configuracion",
        choices=["C0", "C1", "C2", "C3"],
        help="Defensa N4 (prevalece sobre --c0): C2 añade el clasificador, C3 además el precio",
    )
    parser.add_argument("--max-llamadas", type=int, default=MAX_LLAMADAS)
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="N3: segunda lectura independiente de las ofertas candidatas (Haiku o parser)",
    )
    parser.add_argument(
        "--politica-n3",
        choices=["abstener", "excluir"],
        default="abstener",
        help="Con --verificar: abstenerse si la ganadora no se confirma o excluir no confirmadas",
    )
    parser.add_argument("--tope", type=float, default=None, help="Tope de US$ por tarea")
    parser.add_argument("--salida", help="Archivo JSONL donde anexar los resultados")
    parser.add_argument("--silencioso", action="store_true", help="Sin registro de avance")
    args = parser.parse_args()
    logging.basicConfig(format="%(message)s")
    logging.getLogger("comercio_agentico").setLevel(
        logging.WARNING if args.silencioso else logging.INFO
    )
    if not args.consulta and not args.tareas:
        parser.error("Indique una consulta o --tareas")
    asyncio.run(principal(args))


if __name__ == "__main__":
    main()
