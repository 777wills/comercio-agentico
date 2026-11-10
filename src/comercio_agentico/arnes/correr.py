"""Arnés de evaluación: corre una configuración del agente sobre un conjunto de tareas.

    uv run python -m comercio_agentico.arnes.correr --config configs/calibracion_flash.yaml \\
        --tareas tareas/tareas_b.jsonl --repeticiones 1

Cada ejecución (tarea × repetición) se anexa como una línea a
``resultados/corridas/<fecha>_<config>.jsonl`` con lo necesario para reproducirla y medirla:
modelo, proveedor, versión de prompt, hash del corpus, commit, tokens, costo, latencia, la
propuesta y **todas** las ofertas recolectadas (M1 las compara campo a campo con la verdad).

Las tareas corren en paralelo (``concurrencia_tareas``) y comparten un único semáforo de llamadas
simultáneas al LLM (``concurrencia_llm``), que acota la presión sobre el límite de tasa del
proveedor. Si el archivo de salida ya existe, se omiten las ejecuciones registradas: una corrida
interrumpida se reanuda con el mismo comando.

Requiere el corpus B servido (``make corpus-b-servir``) y la clave correspondiente en ``.env``.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import gzip
import hashlib
import json
import logging
import subprocess
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from comercio_agentico.agente import extraccion, grafo, interpretacion
from comercio_agentico.agente.fuentes import cargar_fuentes
from comercio_agentico.agente.grafo import MAX_LLAMADAS, Resultado, preguntar
from comercio_agentico.agente.interpretacion import Necesidad
from comercio_agentico.corpus_b import DIR_CORPUS, RAIZ
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.corpus_b.tareas import Tarea, cargar_tareas
from comercio_agentico.emparejamiento import INSTRUCCIONES_CONFIRMAR, Decisiones, Emparejador
from comercio_agentico.esquema import ListaOfertas
from comercio_agentico.modelos import MODELOS
from comercio_agentico.preguntar import evaluar, registro_jsonl

log = logging.getLogger("comercio_agentico.arnes")
DIR_CORRIDAS = RAIZ / "resultados" / "corridas"
SIN_FRAGMENTO = {"procedencia": {"fragmento_original"}}


class ConfigCorrida(BaseModel):
    """Una configuración evaluable del agente (un archivo YAML en ``configs/``)."""

    nombre: str = Field(description="Identificador corto; forma parte del nombre del archivo.")
    modelo: str = "deepseek-flash"
    separacion_planos: bool = Field(default=True, description="C1 (True) o C0 (False).")
    max_llamadas: int = MAX_LLAMADAS
    tope_usd: float | None = Field(default=None, description="Tope por tarea; None = .env.")
    concurrencia_tareas: int = 4
    concurrencia_llm: int = 6
    corpus: Literal["b", "a"] = Field(
        default="b", description="b: sintético (S01) · a: tiendas reales reconstruidas (S04)."
    )


def recursos_corpus(corpus: str) -> dict[str, Path]:
    """Fuentes, catálogo, tareas, verdad y directorio de cada corpus."""
    if corpus == "a":
        from comercio_agentico.corpus_a import RAIZ as DIR_A

        return {
            "fuentes": RAIZ / "fuentes" / "corpus_a.yaml",
            "catalogo": DIR_A / "catalogo.json",
            "tareas": RAIZ / "tareas" / "tareas_a.jsonl",
            "verdad": DIR_A / "verdad.json",
            "directorio": DIR_A,
        }
    return {
        "fuentes": RAIZ / "fuentes" / "corpus_b.yaml",
        "catalogo": DIR_CORPUS / "catalogo.json",
        "tareas": RAIZ / "tareas" / "tareas_b.jsonl",
        "verdad": DIR_CORPUS / "verdad.json",
        "directorio": DIR_CORPUS,
    }


def cargar_config(ruta: str | Path) -> ConfigCorrida:
    return ConfigCorrida.model_validate(yaml.safe_load(Path(ruta).read_text(encoding="utf-8")))


# --------------------------------------------------------------------------------------------------
# Huellas de reproducibilidad


def _sha(partes: list[bytes]) -> str:
    h = hashlib.sha256()
    for parte in partes:
        h.update(hashlib.sha256(parte).digest())
    return h.hexdigest()[:12]


def version_prompt() -> str:
    """Huella de las instrucciones de los cuatro roles del LLM y de sus esquemas de salida.

    Cambia si se edita un prompt o un esquema."""
    textos = [
        interpretacion.INSTRUCCIONES,
        grafo.INSTRUCCIONES_PLANIFICADOR,
        extraccion.INSTRUCCIONES,
        extraccion.ADVERTENCIA_DATOS,
        INSTRUCCIONES_CONFIRMAR,
    ]
    esquemas = [m.model_json_schema() for m in (Necesidad, ListaOfertas, Decisiones)]
    return _sha(
        [t.encode() for t in textos] + [json.dumps(e, sort_keys=True).encode() for e in esquemas]
    )


def hash_corpus(directorio: Path = DIR_CORPUS, tareas: Path | None = None) -> str:
    """Huella de todos los archivos del corpus (ruta y contenido) y, si se da, de las tareas."""
    archivos = sorted(p for p in directorio.rglob("*") if p.is_file())
    if tareas is not None:
        archivos.append(tareas)
    return _sha([str(p.relative_to(RAIZ)).encode() + p.read_bytes() for p in archivos])


def commit_actual() -> str:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True
        ).stdout.strip()
        sucio = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except OSError:
        return "desconocido"
    return f"{sha}-sucio" if sucio else sha


# --------------------------------------------------------------------------------------------------
# Registro de una ejecución


def registro_ejecucion(
    tarea: Tarea, repeticion: int, r: Resultado, meta: dict[str, Any]
) -> dict[str, Any]:
    fila = registro_jsonl(tarea.id, r, evaluar(tarea, r))
    proveedores = sorted({x["proveedor"] for x in r.llamadas_llm if x.get("proveedor")})
    return {
        **meta,
        "repeticion": repeticion,
        "categoria": tarea.categoria,
        **fila,
        "proveedor_llm": proveedores,
        "ofertas_todas": [o.model_dump(mode="json", exclude=SIN_FRAGMENTO) for o in r.ofertas],
        "error": None,
    }


def registro_error(
    tarea: Tarea, repeticion: int, error: Exception, segundos: float, meta: dict[str, Any]
) -> dict[str, Any]:
    """Una excepción no detiene la corrida: queda registrada y cuenta como fallo."""
    return {
        **meta,
        "repeticion": repeticion,
        "categoria": tarea.categoria,
        "tarea": tarea.id,
        "evaluacion": {"acierto": False, "elegida": None, "procedencia_completa": False},
        "propuesta": None,
        "ofertas_todas": [],
        "costo_usd": None,
        "segundos": round(segundos, 1),
        "error": f"{type(error).__name__}: {str(error)[:500]}",
    }


def ya_registradas(salida: Path) -> set[tuple[str, int]]:
    if not salida.exists():
        return set()
    hechas = set()
    for linea in salida.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            fila = json.loads(linea)
            hechas.add((fila["tarea"], fila["repeticion"]))
    return hechas


# --------------------------------------------------------------------------------------------------
# Ejecución


Preguntar = Callable[..., Awaitable[Resultado]]


async def correr(
    config: ConfigCorrida,
    tareas: list[Tarea],
    repeticiones: int,
    salida: Path,
    *,
    preguntar_fn: Preguntar = preguntar,
    emparejador: Emparejador | Any = None,
    meta: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Ejecuta las tareas pendientes y anexa cada resultado a ``salida`` en cuanto termina."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    hechas = ya_registradas(salida)
    pendientes = [
        (t, rep) for rep in range(1, repeticiones + 1) for t in tareas if (t.id, rep) not in hechas
    ]
    if hechas:
        log.info(
            "Reanudando: %d ejecuciones ya registradas, %d pendientes", len(hechas), len(pendientes)
        )
    recursos = recursos_corpus(config.corpus)
    emparejador = emparejador or Emparejador(cargar_catalogo(recursos["catalogo"]))
    registro = cargar_fuentes(recursos["fuentes"])
    meta = meta or {}
    sem_tareas = asyncio.Semaphore(config.concurrencia_tareas)
    sem_llm = asyncio.Semaphore(config.concurrencia_llm)
    cerrojo = asyncio.Lock()
    filas: list[dict[str, Any]] = []
    gasto = 0.0

    async def una(tarea: Tarea, rep: int) -> None:
        nonlocal gasto
        async with sem_tareas:
            inicio = asyncio.get_running_loop().time()
            try:
                r = await preguntar_fn(
                    tarea.consulta,
                    modelo=config.modelo,
                    separacion_planos=config.separacion_planos,
                    max_llamadas=config.max_llamadas,
                    tope_usd=config.tope_usd,
                    emparejador=emparejador,
                    registro=registro,
                    semaforo_llm=sem_llm,
                )
                fila = registro_ejecucion(tarea, rep, r, meta)
            except Exception as error:
                segundos = asyncio.get_running_loop().time() - inicio
                log.warning("  %s r%d: error %s", tarea.id, rep, error)
                fila = registro_error(tarea, rep, error, segundos, meta)
        async with cerrojo:
            with salida.open("a", encoding="utf-8") as f:
                f.write(json.dumps(fila, ensure_ascii=False) + "\n")
            filas.append(fila)
            gasto += fila["costo_usd"] or 0.0
            ev = fila["evaluacion"]
            log.info(
                "[%d/%d] %s r%d %-13s %s · US$%.4f · %.0f s · acumulado US$%.3f",
                len(filas),
                len(pendientes),
                tarea.id,
                rep,
                tarea.categoria,
                "ERROR" if fila["error"] else ("ACIERTO" if ev["acierto"] else "fallo"),
                fila["costo_usd"] or 0.0,
                fila["segundos"],
                gasto,
            )

    await asyncio.gather(*(una(t, rep) for t, rep in pendientes))
    return filas


def principal(args: argparse.Namespace) -> Path:
    config = cargar_config(args.config)
    if config.modelo not in MODELOS:
        raise SystemExit(f"Modelo desconocido: {config.modelo}")
    recursos = recursos_corpus(config.corpus)
    ruta_tareas = Path(args.tareas or recursos["tareas"]).resolve()
    tareas = cargar_tareas(ruta_tareas)
    if args.solo:
        pedidas = set(args.solo.split(","))
        tareas = [t for t in tareas if t.id in pedidas]
    fecha = dt.date.today().isoformat()
    nombre = f"{config.nombre}_simulado" if args.simulado else config.nombre
    salida = Path(args.salida) if args.salida else DIR_CORRIDAS / f"{fecha}_{nombre}.jsonl"
    ficha = MODELOS[config.modelo]
    meta = {
        "corrida": salida.stem,
        "config": config.model_dump(),
        "modelo": config.modelo,
        "id_modelo": ficha.id_modelo,
        "proveedor_fijado": ficha.proveedor or ficha.plataforma,
        "version_prompt": version_prompt(),
        "hash_corpus": hash_corpus(recursos["directorio"], tareas=ruta_tareas),
        "corpus": config.corpus,
        "commit": commit_actual(),
        "conjunto_tareas": ruta_tareas.name,
    }
    log.info(
        "Corrida %s: %d tareas × %d repeticiones con %s (prompt %s, corpus %s, commit %s)",
        salida.stem,
        len(tareas),
        args.repeticiones,
        config.modelo,
        meta["version_prompt"],
        meta["hash_corpus"],
        meta["commit"],
    )
    extra: dict[str, Any] = {}
    if args.simulado:
        from comercio_agentico.arnes.simulado import AgenteSimulado

        extra = {"preguntar_fn": AgenteSimulado(), "emparejador": "no se usa"}
        meta["modelo"] = meta["id_modelo"] = "simulado"
    asyncio.run(correr(config, tareas, args.repeticiones, salida, meta=meta, **extra))
    comprimida = comprimir(salida)
    log.info("Registro: %s (copia versionable: %s)", salida, comprimida.name)
    return salida


def comprimir(salida: Path) -> Path:
    """Copia ``.jsonl.gz`` de la corrida: es la que se versiona (el ``.jsonl`` sirve para reanudar).

    ``mtime=0`` hace que el archivo comprimido sea idéntico byte a byte si la corrida no cambió.
    """
    destino = salida.with_name(salida.name + ".gz")
    destino.write_bytes(gzip.compress(salida.read_bytes(), mtime=0))
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--config", required=True, help="YAML de la configuración (configs/)")
    parser.add_argument("--tareas", help="JSONL de tareas (por defecto, las del corpus)")
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument("--solo", help="Subconjunto de IDs de tarea separados por coma")
    parser.add_argument("--salida", help="Archivo JSONL (por defecto resultados/corridas/...)")
    parser.add_argument(
        "--simulado",
        action="store_true",
        help="Agente simulado desde la verdad, con errores conocidos (US$0, sin red ni servidor)",
    )
    parser.add_argument(
        "--metricas", action="store_true", help="Al terminar, calcula el informe de métricas"
    )
    args = parser.parse_args()
    logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("comercio_agentico").setLevel(logging.WARNING)
    logging.getLogger("comercio_agentico.arnes").setLevel(logging.INFO)
    salida = principal(args)
    if args.metricas:
        from comercio_agentico.arnes.metricas import informe
        from comercio_agentico.corpus_b.tareas import cargar_tareas as _tareas

        recursos = recursos_corpus(cargar_config(args.config).corpus)
        informe(
            salida,
            tareas=_tareas(Path(args.tareas or recursos["tareas"])),
            verdad=json.loads(recursos["verdad"].read_text(encoding="utf-8")),
        )


if __name__ == "__main__":
    main()
