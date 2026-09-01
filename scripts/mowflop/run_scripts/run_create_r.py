"""Roda ``scripts/create .R`` num dataset do MoWFLOP sem editar o arquivo R.

``create .R`` fixa suas três constantes de pasta no topo (linhas 20-22), que o
autor original troca manualmente por dataset.  Para manter o arquivo no
repositório byte a byte idêntico -- de modo que o modelo particionado e o
baseline não particionado demonstravelmente atravessem o mesmo código --, este
utilitário copia o script para um arquivo temporário, reescreve *só* essas três
atribuições, verifica com um diff que nada mais mudou, e roda essa cópia.

Uso::

    python -m mowflop.run_scripts.run_create_r --tag x60
    python -m mowflop.run_scripts.run_create_r --tag raw --keep-script /tmp/create_raw.R
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..io_raw import repo_root

FOLDER_LINES = {
    "infolder": re.compile(r'^infolder\s*<-\s*".*?"'),
    "parfolder": re.compile(r'^parfolder\s*<-\s*".*?"'),
    "outfolder": re.compile(r'^outfolder\s*<-\s*".*?"'),
}


def rewrite(source: str, folders: dict[str, str]) -> tuple[str, list[int]]:
    """Reescreve só as três constantes de pasta no texto-fonte de ``create .R``.

    Args:
        source: conteúdo original de ``create .R``.
        folders: novos valores para ``infolder``, ``parfolder`` e ``outfolder``.

    Returns:
        Tupla ``(fonte reescrita, números das linhas alteradas)``.

    Raises:
        ValueError: se alguma das três constantes não for encontrada no fonte.
    """
    lines = source.splitlines(keepends=True)
    changed = []
    for i, line in enumerate(lines):
        for name, pattern in FOLDER_LINES.items():
            if pattern.match(line):
                lines[i] = f'{name} <- "{folders[name]}"\n'
                changed.append(i + 1)
    missing = set(FOLDER_LINES) - {
        name
        for name, pattern in FOLDER_LINES.items()
        if any(pattern.match(line) for line in source.splitlines())
    }
    if missing:
        raise ValueError(f"could not find the folder constants in create .R: {sorted(missing)}")
    return "".join(lines), changed


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando.

    Args:
        argv: argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns:
        Código de saída do ``Rscript`` chamado, ou um código próprio se algo
        falhar antes disso (arquivo ausente, pastas ausentes, diff inesperado,
        ``Rscript`` não encontrado).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", required=True, help="dataset tag, e.g. x60 or raw")
    parser.add_argument("--repo", default=str(repo_root()))
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--keep-script", help="also save the rewritten script here")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    script = repo / "scripts" / "create .R"
    if not script.is_file():
        print(f"not found: {script}", file=sys.stderr)
        return 1

    folders = {
        "infolder": f"data/mowflop_{args.tag}/",
        "parfolder": "pf/mowflop/",
        "outfolder": f"stns/mowflop_{args.tag}/",
    }
    for name in ("infolder", "parfolder"):
        if not (repo / folders[name]).is_dir():
            print(f"missing input folder: {repo / folders[name]}", file=sys.stderr)
            return 1
    for algorithm in ("MOEAD", "NSGA2"):
        (repo / folders["outfolder"] / algorithm).mkdir(parents=True, exist_ok=True)

    source = script.read_text(encoding="utf-8")
    rewritten, changed = rewrite(source, folders)

    # diff de segurança: só as linhas das três constantes podem diferir do original
    diff = [
        line
        for line in difflib.unified_diff(
            source.splitlines(), rewritten.splitlines(), lineterm="", n=0
        )
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    print(f"lines rewritten: {changed}")
    for line in diff:
        print(f"  {line}")
    if len(diff) != 2 * len(FOLDER_LINES):
        print("refusing to run: more than the three folder constants differ", file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile(
        "w", suffix=".R", dir=str(repo / "scripts"), delete=False, encoding="utf-8"
    ) as handle:
        handle.write(rewritten)
        temporary = Path(handle.name)
    if args.keep_script:
        shutil.copy(temporary, args.keep_script)

    if args.dry_run:
        temporary.unlink(missing_ok=True)
        where = args.keep_script or "(not kept; pass --keep-script to inspect it)"
        print(f"dry run, R not invoked; rewritten script: {where}")
        return 0

    try:
        completed = subprocess.run(
            [args.rscript, str(temporary)], cwd=str(repo), check=False
        )
    except FileNotFoundError:
        print(
            f"{args.rscript} not found. Install R first, e.g. "
            "sudo apt install -y r-base r-cran-igraph r-cran-dplyr r-cran-tidyr",
            file=sys.stderr,
        )
        return 127
    finally:
        temporary.unlink(missing_ok=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
