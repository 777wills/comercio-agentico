"""Ataques adaptativos contra el canal residual de la separación de planos (D123).

Con C1 el planificador no lee el texto del proveedor, pero sí recibe el título y el enlace de cada
oferta extraída. A21 escribe la instrucción dentro del nombre del producto. El plantado se hace
en una copia desechable del corpus B (nunca en sitios reales, D21) y el éxito se evalúa con el
mismo predicado por programa de la clase «exfiltrar el mandato» de E2.

    make ataque-adaptativo   # C0–C3 × 3 con Flash (~US$0,20; requiere corpus-b-servir)
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import shutil
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from comercio_agentico.agente.grafo import CONFIGURACIONES, preguntar
from comercio_agentico.ataques.correr import registro_local
from comercio_agentico.ataques.suite import Predicado, exito_exfiltrar_mandato
from comercio_agentico.corpus_b import DIR_CORPUS, RAIZ
from comercio_agentico.corpus_b.servir import servidor_web
from comercio_agentico.preguntar import registro_jsonl

RUTA_CARGAS_ADAPTATIVAS = RAIZ / "ataques" / "cargas_adaptativas.yaml"
DIR_RESULTADOS = RAIZ / "resultados" / "ataques"


class CargaAdaptativa(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^A2\d$")
    clase: str = Field(pattern="^exfiltrar_mandato$")
    ubicacion: str = Field(pattern="^titulo$")
    proveedor: str = Field(pattern=r"^P[2-5]$")
    archivo: str
    nombre_producto: str
    tarea: str = Field(pattern=r"^B\d{3}$")
    consulta: str
    objetivo: str
    predicado: Predicado
    texto: str
    url_accion: str


def cargar_adaptativas(ruta: Path = RUTA_CARGAS_ADAPTATIVAS) -> list[CargaAdaptativa]:
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    return [CargaAdaptativa.model_validate(c) for c in datos["cargas"]]


def plantar_titulo(carga: CargaAdaptativa, destino: Path, url_base: str) -> Path:
    """Copia el corpus B y escribe la carga a continuación del nombre del producto."""
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(DIR_CORPUS, destino)
    pagina = destino / carga.archivo
    directorio = Path(carga.archivo).parts[0]
    url = f"{url_base.rstrip('/')}/{directorio}/{carga.url_accion}"
    contenido = pagina.read_text(encoding="utf-8")
    if contenido.count(carga.nombre_producto) != 1:
        raise ValueError(f"{carga.id}: el nombre del producto debe aparecer una vez en {pagina}")
    carga_html = html.escape(carga.texto.format(URL_ACCION=url), quote=False)
    pagina.write_text(
        contenido.replace(carga.nombre_producto, f"{carga.nombre_producto} {carga_html}", 1),
        encoding="utf-8",
    )
    accion = destino / directorio / carga.url_accion.split("?")[0]
    accion.write_text("<html><body>Precio confirmado.</body></html>", encoding="utf-8")
    return destino


def exito(carga: CargaAdaptativa, fila: dict[str, Any]) -> bool:
    if fila.get("error"):
        return False
    return exito_exfiltrar_mandato(fila, SimpleNamespace(predicado=carga.predicado))  # type: ignore[arg-type]


async def correr(
    carga: CargaAdaptativa,
    configuraciones: list[str],
    repeticiones: int,
    salida: Path,
    modelo: str = "deepseek-flash",
    preguntar_fn: Any = preguntar,
) -> list[dict[str, Any]]:
    web = servidor_web(0)
    puerto = int(web.server_address[1])
    with tempfile.TemporaryDirectory(prefix=f"adaptativo_{carga.id}_") as tmp:
        variante = plantar_titulo(carga, Path(tmp) / carga.id, f"http://127.0.0.1:{puerto}")
        web.RequestHandlerClass.keywords["directory"] = str(variante)
        threading.Thread(target=web.serve_forever, daemon=True).start()
        registro = registro_local(puerto)
        filas = []
        try:
            for configuracion in configuraciones:
                for repeticion in range(repeticiones):
                    inicio = time.perf_counter()
                    try:
                        r = await preguntar_fn(
                            carga.consulta,
                            modelo=modelo,
                            configuracion=configuracion,
                            registro=registro,
                            tope_usd=0.10,
                        )
                        fila = registro_jsonl(carga.tarea, r, None)
                    except Exception as error:  # una ejecución fallida cuenta como no éxito
                        fila = {"error": f"{type(error).__name__}: {error}"}
                    fila |= {
                        "carga": carga.id,
                        "configuracion": configuracion,
                        "repeticion": repeticion,
                        "modelo": modelo,
                        "segundos": round(time.perf_counter() - inicio, 1),
                    }
                    fila["exito_ataque"] = exito(carga, fila)
                    filas.append(fila)
                    salida.parent.mkdir(parents=True, exist_ok=True)
                    with salida.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(fila, ensure_ascii=False) + "\n")
                    print(
                        f"{carga.id} {configuracion} rep {repeticion}: "
                        f"éxito={fila['exito_ataque']} US${fila.get('costo_usd', 0):.4f}",
                        flush=True,
                    )
        finally:
            web.shutdown()
    return filas


def resumen(filas: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    tabla: dict[str, dict[str, int]] = {}
    for f in filas:
        celda = tabla.setdefault(f["configuracion"], {"exitos": 0, "n": 0})
        celda["n"] += 1
        celda["exitos"] += bool(f["exito_ataque"])
    return tabla


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", default="deepseek-flash")
    parser.add_argument("--configuraciones", default=",".join(CONFIGURACIONES))
    parser.add_argument("--repeticiones", type=int, default=3)
    parser.add_argument("--salida", type=Path, default=DIR_RESULTADOS / "adaptativo_titulo.jsonl")
    args = parser.parse_args()
    filas = []
    for carga in cargar_adaptativas():
        filas += asyncio.run(
            correr(
                carga,
                args.configuraciones.split(","),
                args.repeticiones,
                args.salida,
                args.modelo,
            )
        )
    print(json.dumps(resumen(filas), ensure_ascii=False))


if __name__ == "__main__":
    main()
