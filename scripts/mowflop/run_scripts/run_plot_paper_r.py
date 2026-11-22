"""Desenha STNs no formato das figuras do artigo CEC 2027 com ``scripts/plot_paper.R``.

Uso: ``python -m mowflop.run_scripts.run_plot_paper_r --layout of|fd [--column]
[--position-strip OUT.png] --outdir <pasta> <stn>.RData ...``
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from ..io_raw import repo_root


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando.

    Args:
        argv: argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns:
        Código de saída do ``Rscript``; 1 se faltar algum ``.RData``; 127 se o
        ``Rscript`` não for encontrado.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rdata", nargs="+", help="STNs (.RData) a desenhar")
    parser.add_argument("--layout", choices=["of", "fd"], required=True)
    parser.add_argument("--outdir", default=".", help="pasta dos PNGs")
    parser.add_argument("--column", action="store_true",
                        help="versão de coluna: 1,13 x 0,95 in, legenda sem Position")
    parser.add_argument("--position-strip", default="",
                        help="grava só a legenda Position (uma linha) neste PNG; uma STN")
    parser.add_argument("--repo", default=str(repo_root()))
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--lib", default=str(Path.home() / "R" / "library"),
                        help="biblioteca R extra (onde está o ggraph)")
    args = parser.parse_args(argv)

    files = [Path(f).resolve() for f in args.rdata]
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        print("STN não encontrada: " + ", ".join(missing), file=sys.stderr)
        return 1

    cmd = [args.rscript, str(Path(args.repo) / "scripts" / "plot_paper.R"),
           "--layout", args.layout, "--outdir", str(Path(args.outdir).resolve())]
    if args.column:
        cmd.append("--column")
    if args.position_strip:
        cmd += ["--position-strip", str(Path(args.position_strip).resolve())]
    if Path(args.lib).is_dir():
        cmd += ["--lib", args.lib]
    cmd += [str(f) for f in files]

    with tempfile.TemporaryDirectory(prefix="plot_paper_") as work:
        try:
            # cwd temporário: um Rplots.pdf perdido não cai em pasta nenhuma
            return subprocess.run(cmd, cwd=work, check=False).returncode
        except FileNotFoundError:
            print(f"{args.rscript} não encontrado", file=sys.stderr)
            return 127


if __name__ == "__main__":
    raise SystemExit(main())
