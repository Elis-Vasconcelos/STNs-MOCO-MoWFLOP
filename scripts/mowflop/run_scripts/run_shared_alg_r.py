"""Roda ``scripts/shared_alg.R`` num dataset do MoWFLOP sem editar o arquivo R.

Mesmo padrão de ``run_scripts/run_stn_metrics_r.py``, mas ``shared_alg.R``
não tem constante ``algo`` -- ele processa MOEAD e NSGA2 juntos, casando os
arquivos pelo sufixo do nome (ver docstring de ``shared_alg.R``). Só
``iset`` é reescrito.

Uso::

    python -m mowflop.run_scripts.run_shared_alg_r --tag g1.0
    python -m mowflop.run_scripts.run_shared_alg_r --tag x60
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from ..io_raw import repo_root

CONST_LINES = {
    "iset": re.compile(r'^iset\s*<-\s*".*?"'),
}


def rewrite(source: str, values: dict[str, str]) -> tuple[str, list[int]]:
    """Reescreve só ``iset`` no texto-fonte de ``shared_alg.R``.

    Args:
        source: conteúdo original de ``shared_alg.R``.
        values: novo valor para ``iset``.

    Returns:
        Tupla ``(fonte reescrita, números das linhas alteradas)``.

    Raises:
        ValueError: se a constante não for encontrada no fonte.
    """
    lines = source.splitlines(keepends=True)
    changed = []
    for i, line in enumerate(lines):
        for name, pattern in CONST_LINES.items():
            if pattern.match(line):
                lines[i] = f'{name} <- "{values[name]}"\n'
                changed.append(i + 1)
    missing = set(CONST_LINES) - {
        name
        for name, pattern in CONST_LINES.items()
        if any(pattern.match(line) for line in source.splitlines())
    }
    if missing:
        raise ValueError(f"could not find the constants in shared_alg.R: {sorted(missing)}")
    return "".join(lines), changed


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando.

    Args:
        argv: argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns:
        Código de saída do ``Rscript`` chamado, ou um código próprio se algo
        falhar antes disso.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", required=True, help="dataset tag, e.g. x60, g1.0")
    parser.add_argument("--repo", default=str(repo_root()))
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    script = repo / "scripts" / "shared_alg.R"
    if not script.is_file():
        print(f"not found: {script}", file=sys.stderr)
        return 1

    iset = f"mowflop_{args.tag}"
    for algo in ("MOEAD", "NSGA2"):
        d = repo / "stns" / iset / algo
        if not d.is_dir():
            print(f"missing STNs: {d}", file=sys.stderr)
            return 1
    (repo / "metrics").mkdir(parents=True, exist_ok=True)

    values = {"iset": iset}
    source = script.read_text(encoding="utf-8")
    rewritten, changed = rewrite(source, values)

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
    if len(diff) != 2 * len(CONST_LINES):
        print("refusing to run: more than the constant differs", file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile(
        "w", suffix=".R", dir=str(repo / "scripts"), delete=False, encoding="utf-8"
    ) as handle:
        handle.write(rewritten)
        temporary = Path(handle.name)

    if args.dry_run:
        temporary.unlink(missing_ok=True)
        print("dry run; R not invoked")
        return 0

    try:
        completed = subprocess.run([args.rscript, str(temporary)], cwd=str(repo), check=False)
    except FileNotFoundError:
        print(f"{args.rscript} not found", file=sys.stderr)
        return 127
    finally:
        temporary.unlink(missing_ok=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
