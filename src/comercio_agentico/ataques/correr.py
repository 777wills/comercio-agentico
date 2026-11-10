"""Ejecuta cargas × configuraciones C0–C3 y calcula M5 sin juicio humano.

El servidor HTTP de cada variante usa un puerto local efímero; P1 sigue en el MCP local de
``make corpus-b-servir``. La salida JSONL se puede reanudar: la clave es
(carga, configuración, tarea, repetición), no solo la tarea.

Prueba de humo (5 clases × C0/C3, DeepSeek Flash, tope total US$0,15)::

    uv run python -m comercio_agentico.ataques.correr --humo --tope-total 0.15
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import gzip
import json
import logging
import threading
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from comercio_agentico.agente.defensa import ClasificadorInyeccion
from comercio_agentico.agente.fuentes import RegistroFuentes, cargar_fuentes
from comercio_agentico.agente.grafo import CONFIGURACIONES, Configuracion, Resultado, preguntar
from comercio_agentico.arnes.correr import (
    commit_actual,
    hash_corpus,
    registro_ejecucion,
    registro_error,
    version_prompt,
)
from comercio_agentico.arnes.metricas import wilson
from comercio_agentico.ataques.plantar import DIR_VARIANTES, plantar
from comercio_agentico.ataques.suite import (
    CLASES,
    RUTA_CARGAS,
    UBICACIONES,
    Carga,
    cargar_suite,
    evaluar_exito,
    m5,
)
from comercio_agentico.corpus_b import DIR_CORPUS, RAIZ, RUTA_TAREAS
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.corpus_b.servir import servidor_web
from comercio_agentico.corpus_b.tareas import Tarea, cargar_tareas
from comercio_agentico.emparejamiento import Emparejador
from comercio_agentico.modelos import MODELOS

log = logging.getLogger("comercio_agentico.ataques")
DIR_RESULTADOS = RAIZ / "resultados" / "ataques"
Preguntar = Callable[..., Awaitable[Resultado]]


def leer_filas(ruta: Path) -> list[dict[str, Any]]:
    if not ruta.exists():
        return []
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines() if linea]


def diagonal(cargas: Sequence[Carga]) -> list[Carga]:
    """Una carga por clase recorriendo las cuatro ubicaciones (clase i → ubicación i mod 4)."""
    pares = {(c, UBICACIONES[i % len(UBICACIONES)]) for i, c in enumerate(CLASES)}
    return [c for c in cargas if (c.clase, c.ubicacion) in pares]


def _usd(valor: float, decimales: int = 4) -> str:
    return f"{valor:.{decimales}f}".replace(".", ",")


def registro_local(puerto: int) -> RegistroFuentes:
    """P2–P5 apuntan a la variante; P1 conserva el MCP limpio, cuyo inventario es idéntico."""
    registro = cargar_fuentes()
    for fuente in registro.fuentes:
        if fuente.herramienta != "consultar_mcp":
            fuente.url = urlsplit(fuente.url)._replace(netloc=f"127.0.0.1:{puerto}").geturl()
    return registro


def _resumen_grupo(filas: list[dict[str, Any]]) -> dict[str, Any]:
    resultado = m5(filas)
    intervalo = wilson(int(resultado["k"]), int(resultado["n"]))
    return {
        **resultado,
        "ic95": [intervalo["bajo"], intervalo["alto"]],
        "errores": sum(bool(f.get("error")) for f in filas),
        "costo_usd": round(sum(f.get("costo_usd") or 0.0 for f in filas), 6),
    }


def resumen_m5(filas: list[dict[str, Any]], salida: Path, modelo: str) -> dict[str, Any]:
    def grupo(clave: str) -> dict[str, Any]:
        valores = sorted({f[clave] for f in filas if clave in f})
        return {
            valor: _resumen_grupo([f for f in filas if f.get(clave) == valor]) for valor in valores
        }

    return {
        "corrida": salida.stem,
        "modelo": modelo,
        "ejecuciones": len(filas),
        "cargas": sorted({f["carga"] for f in filas if "carga" in f}),
        "global": _resumen_grupo(filas),
        "por_configuracion": grupo("configuracion"),
        "por_clase": grupo("clase"),
        "por_ubicacion": grupo("ubicacion"),
        "nota": "M5 = ejecuciones con predicado verdadero / ejecuciones registradas; "
        "los errores cuentan como no éxito y se reportan aparte.",
    }


def informe_markdown(resumen: dict[str, Any]) -> str:
    def porcentaje(valor: float | None) -> str:
        return "—" if valor is None else f"{100 * valor:.1f} %".replace(".", ",")

    lineas = [
        "# Resultados E2: tasa de éxito del ataque (M5)",
        "",
        f"Corrida `{resumen['corrida']}` con modelo `{resumen['modelo']}` y cargas "
        f"{', '.join(resumen['cargas'])}. M5 es la proporción de ejecuciones cuyo predicado "
        "automático resulta verdadero; "
        "seguridad = 1 - M5. Los errores de ejecución se contabilizan como no éxito y se "
        "reportan por separado para no ocultar fallos de infraestructura.",
        "",
        f"Se registraron {resumen['ejecuciones']} ejecuciones, con un costo total de "
        f"US${_usd(resumen['global']['costo_usd'], 6)} y {resumen['global']['errores']} errores.",
        "",
        "| Configuración | Éxitos / ejecuciones | M5 | IC 95 % | Errores | Costo (US$) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for configuracion, dato in resumen["por_configuracion"].items():
        bajo, alto = dato["ic95"]
        intervalo = "—" if bajo is None else f"[{porcentaje(bajo)}; {porcentaje(alto)}]"
        lineas.append(
            f"| {configuracion} | {dato['k']} / {dato['n']} | {porcentaje(dato['M5'])} | "
            f"{intervalo} | {dato['errores']} | {_usd(dato['costo_usd'])} |"
        )
    lineas += [
        "",
        "## Lectura por clase",
        "",
        "| Clase | Éxitos / ejecuciones | M5 |",
        "|---|---:|---:|",
    ]
    for clase, dato in resumen["por_clase"].items():
        lineas.append(f"| {clase} | {dato['k']} / {dato['n']} | {porcentaje(dato['M5'])} |")
    lineas += ["", "## Lectura por ubicación", "", "| Ubicación | Éxitos / ejecuciones | M5 |"]
    lineas.append("|---|---:|---:|")
    for ubicacion, dato in resumen["por_ubicacion"].items():
        lineas.append(f"| {ubicacion} | {dato['k']} / {dato['n']} | {porcentaje(dato['M5'])} |")
    lineas += [
        "",
        "## Alcance de la evidencia",
        "",
        "Las clases de navegación miden que el planificador **solicitó** la URL de acción local, "
        "no que una compra se haya consumado: el corpus no ejecuta pagos ni pedidos. El predicado "
        "de precio examina el cuadro final, no las ofertas retiradas por C3. Una prueba de humo "
        "no sustituye la matriz completa de E2 ni permite comparar ubicaciones con una sola carga "
        "por clase.",
        "",
    ]
    return "\n".join(lineas)


def guardar_evidencia(
    salida: Path,
    filas: list[dict[str, Any]],
    modelo: str,
    informe: Path | None,
) -> dict[str, Any]:
    resumen = resumen_m5(filas, salida, modelo)
    base = salida.with_suffix("")
    base.with_name(base.name + "_m5.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = informe_markdown(resumen)
    base.with_name(base.name + "_m5.md").write_text(markdown, encoding="utf-8")
    salida.with_name(salida.name + ".gz").write_bytes(gzip.compress(salida.read_bytes(), mtime=0))
    if informe is not None:
        informe.parent.mkdir(parents=True, exist_ok=True)
        informe.write_text(markdown, encoding="utf-8")
    return resumen


async def ejecutar(
    cargas: Sequence[Carga],
    configuraciones: Sequence[Configuracion],
    *,
    salida: Path,
    tareas: dict[str, Tarea],
    repeticiones: int = 1,
    modelo: str = "deepseek-flash",
    tope_usd: float | None = 0.05,
    tope_total: float | None = None,
    origen: Path = DIR_CORPUS,
    variantes: Path = DIR_VARIANTES,
    preguntar_fn: Preguntar = preguntar,
    emparejador: Emparejador | Any = None,
    clasificador: Any = None,
    informe: Path | None = None,
) -> dict[str, Any]:
    """Corre secuencialmente para aislar cada variante y acotar el gasto."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    previas = leer_filas(salida)
    hechas = {
        (f["carga"], f["configuracion"], f["tarea"], f["repeticion"])
        for f in previas
        if all(k in f for k in ("carga", "configuracion", "tarea", "repeticion"))
    }
    gasto = sum(f.get("costo_usd") or 0.0 for f in previas)
    emparejador = emparejador or Emparejador(cargar_catalogo(origen / "catalogo.json"))
    if clasificador is None and any(c in ("C2", "C3") for c in configuraciones):
        clasificador = ClasificadorInyeccion()
    prompt, commit = version_prompt(), commit_actual()
    ficha = MODELOS[modelo]

    for carga in cargas:
        pendientes = [
            (configuracion, repeticion)
            for configuracion in configuraciones
            for repeticion in range(1, repeticiones + 1)
            if (carga.id, configuracion, carga.tarea, repeticion) not in hechas
        ]
        if not pendientes:
            continue
        if tope_total is not None and gasto >= tope_total:
            log.warning("Tope total US$%.4f alcanzado; quedan ejecuciones pendientes", tope_total)
            break
        web = servidor_web(0, directorio=origen)  # reserva el puerto antes de escribir la URL
        puerto = int(web.server_address[1])
        hilo = threading.Thread(target=web.serve_forever, daemon=True)
        try:
            variante = plantar(
                carga,
                origen=origen,
                destino=variantes / carga.id,
                url_base=f"http://127.0.0.1:{puerto}",
            )
            # La variante ya está cerrada a escrituras antes de aceptar las lecturas del agente.
            web.RequestHandlerClass.keywords["directory"] = str(variante)
            hilo.start()
            registro = registro_local(puerto)
            huella = hash_corpus(variante, tareas=RUTA_TAREAS)
            for configuracion, repeticion in pendientes:
                if tope_total is not None and gasto >= tope_total:
                    log.warning("Tope total alcanzado; no se inician más ejecuciones")
                    break
                tarea = tareas[carga.tarea]
                restante = None if tope_total is None else max(0.0, tope_total - gasto)
                if restante is None:
                    tope = tope_usd
                elif tope_usd is None:
                    tope = restante
                else:
                    tope = min(tope_usd, restante)
                meta = {
                    "corrida": salida.stem,
                    "config": {
                        "modelo": modelo,
                        "configuracion": configuracion,
                        "tope_usd": tope,
                    },
                    "modelo": modelo,
                    "id_modelo": ficha.id_modelo,
                    "proveedor_fijado": ficha.proveedor or ficha.plataforma,
                    "version_prompt": prompt,
                    "hash_corpus": huella,
                    "corpus": f"b_ataques/{carga.id}",
                    "commit": commit,
                    "conjunto_tareas": RUTA_TAREAS.name,
                    "carga": carga.id,
                    "clase": carga.clase,
                    "ubicacion": carga.ubicacion,
                    "proveedor_atacante": carga.proveedor,
                    "configuracion": configuracion,
                }
                inicio = asyncio.get_running_loop().time()
                try:
                    resultado = await preguntar_fn(
                        tarea.consulta,
                        modelo=modelo,
                        configuracion=configuracion,
                        separacion_planos=configuracion != "C0",
                        clasificador=clasificador,
                        tope_usd=tope,
                        emparejador=emparejador,
                        registro=registro,
                    )
                    fila = registro_ejecucion(tarea, repeticion, resultado, meta)
                except Exception as error:
                    segundos = asyncio.get_running_loop().time() - inicio
                    log.warning("%s %s: %s", carga.id, configuracion, error)
                    fila = registro_error(tarea, repeticion, error, segundos, meta)
                fila["exito_ataque"] = evaluar_exito(carga, fila)
                with salida.open("a", encoding="utf-8") as archivo:
                    archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")
                gasto += fila.get("costo_usd") or 0.0
                log.info(
                    "%s %s r%d: %s · US$%.4f · acumulado US$%.4f",
                    carga.id,
                    configuracion,
                    repeticion,
                    "ÉXITO ATAQUE" if fila["exito_ataque"] else "sin éxito",
                    fila.get("costo_usd") or 0.0,
                    gasto,
                )
        finally:
            if hilo.is_alive():
                web.shutdown()
                hilo.join()
            web.server_close()

    filas = leer_filas(salida)
    return guardar_evidencia(salida, filas, modelo, informe)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cargas", type=Path, default=RUTA_CARGAS)
    parser.add_argument("--solo", help="IDs de carga separados por coma")
    parser.add_argument("--configuraciones", help="C0,C1,C2,C3; por defecto todas (C0,C3 en humo)")
    parser.add_argument(
        "--humo",
        action="store_true",
        help="Diagonal clase × ubicación (A01, A06, A11, A16, A17) en C0 y C3",
    )
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument("--modelo", default="deepseek-flash", choices=MODELOS)
    parser.add_argument("--tope", type=float, default=0.05, help="Tope de US$ por ejecución")
    parser.add_argument("--tope-total", type=float, help="No inicia ejecuciones tras este gasto")
    parser.add_argument("--salida", type=Path)
    parser.add_argument("--simulado", action="store_true", help="Agente simulado, US$0 y sin red")
    args = parser.parse_args()
    logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("comercio_agentico").setLevel(logging.WARNING)
    log.setLevel(logging.INFO)

    cargas = cargar_suite(args.cargas).cargas
    if args.humo:
        cargas = diagonal(cargas)
    if args.solo:
        pedidas = set(args.solo.split(","))
        cargas = [c for c in cargas if c.id in pedidas]
        if pedidas - {c.id for c in cargas}:
            parser.error("Alguna carga de --solo no existe o no pertenece a la selección")
    configuraciones = args.configuraciones.split(",") if args.configuraciones else None
    configuraciones = configuraciones or (["C0", "C3"] if args.humo else list(CONFIGURACIONES))
    if any(c not in CONFIGURACIONES for c in configuraciones):
        parser.error("Configuración desconocida")
    nombre = "humo_ataques" if args.humo else "suite_ataques"
    if args.simulado:
        nombre += "_simulado"
    salida = args.salida or DIR_RESULTADOS / f"{dt.date.today().isoformat()}_{nombre}.jsonl"
    extra: dict[str, Any] = {}
    if args.simulado:
        from comercio_agentico.arnes.simulado import AgenteSimulado

        extra = {
            "preguntar_fn": AgenteSimulado(),
            "emparejador": "no se usa",
            "clasificador": "no se usa",
        }
    resumen = asyncio.run(
        ejecutar(
            cargas,
            configuraciones,
            salida=salida,
            tareas={t.id: t for t in cargar_tareas()},
            repeticiones=args.repeticiones,
            modelo=args.modelo,
            tope_usd=args.tope,
            tope_total=args.tope_total,
            informe=None,
            **extra,
        )
    )
    print(json.dumps(resumen["por_configuracion"], ensure_ascii=False, indent=2))
    print(f"Evidencia: {salida} · gasto total US${resumen['global']['costo_usd']:.4f}")


if __name__ == "__main__":
    main()
