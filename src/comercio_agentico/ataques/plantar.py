"""Planta una carga ya redactada en una copia desechable del corpus B.

Nunca escribe en ``corpus/b_sintetico``. Las variantes se generan en ``corpus/b_ataques/<id>/``
y están ignoradas por git para no publicar los textos.
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from comercio_agentico.ataques.suite import RUTA_CARGAS, Carga, cargar_suite
from comercio_agentico.corpus_b import DIR_CORPUS, RAIZ
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.corpus_b.generar import POR_ID, SEMILLA, cargar_verdad
from comercio_agentico.corpus_b.render import render_p4_pdf

DIR_VARIANTES = RAIZ / "corpus" / "b_ataques"
URL_BASE_LOCAL = "http://127.0.0.1:8800"


def url_accion_local(carga: Carga, base: str = URL_BASE_LOCAL) -> str:
    """Resuelve la acción dentro del directorio local del proveedor atacante."""
    partes = urlsplit(base)
    if partes.scheme != "http" or partes.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("La URL de acción solo puede pertenecer al servidor HTTP local")
    if partes.query or partes.fragment:
        raise ValueError("La URL base no puede incluir consulta ni fragmento")
    directorio = Path(carga.archivo).parts[0]
    return urljoin(base.rstrip("/") + "/", f"{directorio}/{carga.predicado.url_accion}")


def _visible(destino: Path, texto: str) -> None:
    contenido = destino.read_text(encoding="utf-8")
    nota = f'<p class="nota-proveedor">{html.escape(texto)}</p>\n'
    marcador = "</main>" if "</main>" in contenido else "</body>"
    if marcador not in contenido:
        raise ValueError(f"No hay dónde insertar el texto visible en {destino}")
    destino.write_text(contenido.replace(marcador, nota + marcador, 1), encoding="utf-8")


def _oculto_jsonld(destino: Path, texto: str) -> None:
    """Añade la carga al JSON-LD: crawl4ai puede descartar comentarios al hacer Markdown."""
    contenido = destino.read_text(encoding="utf-8")
    patron = re.compile(
        r'(<script\s+type=["\']application/ld\+json["\']\s*>)(.*?)(</script>)',
        flags=re.IGNORECASE | re.DOTALL,
    )
    encontrados = list(patron.finditer(contenido))
    if len(encontrados) != 1:
        raise ValueError(f"Se esperaba un bloque JSON-LD en {destino}")
    datos = json.loads(encontrados[0].group(2))
    datos["description"] = texto
    serializado = json.dumps(datos, ensure_ascii=False, indent=2).replace("</", "<\\/")
    reemplazo = encontrados[0].group(1) + serializado + encontrados[0].group(3)
    destino.write_text(
        contenido[: encontrados[0].start()] + reemplazo + contenido[encontrados[0].end() :],
        encoding="utf-8",
    )


def _pdf(destino: Path, texto: str, origen: Path) -> None:
    """Regenera la lista de P4 con el mismo generador y el texto como nota tras la tabla."""
    verdad = cargar_verdad(origen / "verdad.json")
    productos = {p.id: p for p in cargar_catalogo(origen / "catalogo.json")}
    propias = [o for o in verdad["ofertas"] if o["proveedor"] == "P4"]
    azar = random.Random(SEMILLA)  # render_p4_pdf no lo usa; se pasa por firma
    render_p4_pdf(destino.parent, POR_ID["P4"], propias, productos, azar, nota=texto)


HORA_CHAT = re.compile(r"^(\d{2}/\d{2}/\d{2}), (\d{1,2}):(\d{2}) ([ap])\. m\. - ")


def _hora_siguiente(linea: str, minutos: int = 2) -> str:
    m = HORA_CHAT.match(linea)
    if m is None:
        raise ValueError(f"Línea de chat sin fecha y hora: {linea[:40]}")
    total = (int(m[2]) % 12) * 60 + int(m[3]) + (720 if m[4] == "p" else 0) + minutos
    h24, minuto = divmod(total % 1440, 60)
    return f"{m[1]}, {h24 % 12 or 12}:{minuto:02d} {'p' if h24 >= 12 else 'a'}. m."


def _mensaje(destino: Path, texto: str) -> None:
    """Una línea más del propio vendedor, con hora posterior al último mensaje."""
    lineas = destino.read_text(encoding="utf-8").splitlines()
    nueva = f"{_hora_siguiente(lineas[-1])} - {POR_ID['P5'].nombre}: {texto}"
    destino.write_text("\n".join([*lineas, nueva]) + "\n", encoding="utf-8")


def insertar(destino: Path, carga: Carga, texto: str, origen: Path = DIR_CORPUS) -> None:
    match carga.ubicacion:
        case "visible":
            _visible(destino, texto)
        case "oculto_html":
            _oculto_jsonld(destino, texto)
        case "pdf":
            _pdf(destino, texto, origen)
        case "mensaje":
            _mensaje(destino, texto)


def plantar(
    carga: Carga,
    *,
    origen: Path = DIR_CORPUS,
    destino: Path | None = None,
    url_base: str = URL_BASE_LOCAL,
) -> Path:
    """Recrea la variante desde el corpus limpio y modifica solo su archivo objetivo."""
    origen = origen.resolve()
    destino = (destino or DIR_VARIANTES / carga.id).resolve()
    if not origen.is_dir() or destino == origen or origen in destino.parents:
        raise ValueError("El destino debe ser una copia fuera del corpus limpio")
    if destino.name != carga.id:
        raise ValueError("El directorio de destino debe llamarse como la carga")
    if destino.exists():
        shutil.rmtree(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(origen, destino)
    texto = carga.texto
    if "{URL_ACCION}" in texto:
        texto = texto.replace("{URL_ACCION}", url_accion_local(carga, url_base))
    insertar(destino / carga.archivo, carga, texto, origen)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cargas", type=Path, default=RUTA_CARGAS)
    parser.add_argument("--solo", help="IDs separados por coma; por defecto planta las 20")
    parser.add_argument("--origen", type=Path, default=DIR_CORPUS)
    parser.add_argument("--destino", type=Path, default=DIR_VARIANTES)
    parser.add_argument("--url-base", default=URL_BASE_LOCAL)
    args = parser.parse_args()
    cargas = cargar_suite(args.cargas).cargas
    if args.solo:
        pedidas = set(args.solo.split(","))
        cargas = [c for c in cargas if c.id in pedidas]
        faltantes = pedidas - {c.id for c in cargas}
        if faltantes:
            parser.error(f"Cargas desconocidas: {sorted(faltantes)}")
    for carga in cargas:
        variante = plantar(
            carga,
            origen=args.origen,
            destino=args.destino / carga.id,
            url_base=args.url_base,
        )
        print(f"{carga.id}: {variante}")


if __name__ == "__main__":
    main()
