"""Detecta archivos que volvieron a una versión vieja (búferes de VS Code guardados sobre el disco).

Falla si un archivo modificado frente a HEAD coincide byte a byte con una versión anterior del
historial, o si docs/DECISIONES.md perdió decisiones. Para aceptar una reversión: GUARDIA_OK=1.
"""

import os
import re
import subprocess
import sys

DECISIONES = "docs/DECISIONES.md"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def max_decision(texto: str) -> int:
    return max((int(n) for n in re.findall(r"^\| D(\d+) \|", texto, re.MULTILINE)), default=0)


def main() -> int:
    if os.environ.get("GUARDIA_OK") == "1":
        return 0
    problemas = []
    for ruta in git("diff", "--name-only", "HEAD").splitlines():
        if not os.path.isfile(ruta):
            continue
        blob = git("hash-object", ruta)
        # El commit más antiguo que menciona el blob es el que introdujo esa versión.
        commits = git(
            "log", "--all", "--format=%h %ad", "--date=short", f"--find-object={blob}", "--", ruta
        )
        if commits:
            commit = commits.splitlines()[-1]
            problemas.append(f"{ruta}: es idéntico a la versión del commit {commit}")
    if os.path.isfile(DECISIONES):
        with open(DECISIONES, encoding="utf-8") as f:
            actual = max_decision(f.read())
        en_head = max_decision(git("show", f"HEAD:{DECISIONES}"))
        if actual < en_head:
            problemas.append(f"{DECISIONES}: llega a D{actual} y HEAD llega a D{en_head}")
    if not problemas:
        return 0
    print("Posible búfer viejo de VS Code guardado sobre el disco:", file=sys.stderr)
    for p in problemas:
        print(f"  - {p}", file=sys.stderr)
    print("Revisar con `git diff`; si es sobrescritura, `git restore <archivo>`.", file=sys.stderr)
    print("Si la reversión es intencional: GUARDIA_OK=1.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
