"""Sirve las tiendas reconstruidas del corpus A en http://127.0.0.1:8802/{a1,a2,a3}/index.html.

Uso: ``make corpus-a-servir`` (Ctrl+C para detener). US$0, sin red externa.
"""

from __future__ import annotations

import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from comercio_agentico.corpus_a.construir import DIR_SITIO


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puerto", type=int, default=8802)
    args = parser.parse_args()
    manejador = functools.partial(SimpleHTTPRequestHandler, directory=str(DIR_SITIO))
    servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), manejador)
    for t in ("a1", "a2", "a3"):
        print(f"{t.upper()} http://127.0.0.1:{args.puerto}/{t}/index.html")
    servidor.serve_forever()


if __name__ == "__main__":
    main()
