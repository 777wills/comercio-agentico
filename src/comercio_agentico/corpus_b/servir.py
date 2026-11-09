"""Arranque único del corpus B: sirve P2 a P5 por HTTP y P1 por MCP en la máquina local.

- http://127.0.0.1:8800/p2_web_schema/  · /p3_web_plana/ · /p4_pdf/lista_precios.pdf ·
  /p5_mensaje/chat.txt
- http://127.0.0.1:8801/mcp  (P1, FastMCP)

Uso: ``make corpus-b-servir`` (Ctrl+C para detener). US$0, sin red externa.
"""

from __future__ import annotations

import argparse
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from comercio_agentico.corpus_b import DIR_CORPUS
from comercio_agentico.corpus_b.servidor_mcp import crear_servidor


def servidor_web(puerto: int) -> ThreadingHTTPServer:
    manejador = functools.partial(SimpleHTTPRequestHandler, directory=str(DIR_CORPUS))
    return ThreadingHTTPServer(("127.0.0.1", puerto), manejador)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puerto-web", type=int, default=8800)
    parser.add_argument("--puerto-mcp", type=int, default=8801)
    args = parser.parse_args()

    web = servidor_web(args.puerto_web)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{args.puerto_web}"
    print(f"P2 {base}/p2_web_schema/index.html")
    print(f"P3 {base}/p3_web_plana/index.html")
    print(f"P4 {base}/p4_pdf/lista_precios.pdf")
    print(f"P5 {base}/p5_mensaje/chat.txt")
    print(f"P1 http://127.0.0.1:{args.puerto_mcp}/mcp (MCP)")
    try:
        crear_servidor().run(transport="http", host="127.0.0.1", port=args.puerto_mcp)
    finally:
        web.shutdown()


if __name__ == "__main__":
    main()
