"""Roda ``scripts/metrics.R`` num dataset do MoWFLOP sem editar o arquivo R.

Mesmo padrão de ``run_create_r.py``/``run_plot_r.py``: copia o script pra um
arquivo temporário, reescreve só as constantes ``iset``/``algo``/``outfolder``
(``infolder`` é derivado dessas duas primeiras no próprio ``metrics.R``),
confere com um diff que nada mais mudou, roda a cópia.

``metrics.R`` tenta ler ``t[3]``/``t[6]`` do nome do arquivo como ``r``
(correlação objetivo, do benchmark rho-mnk) e ``k`` (interação de variáveis) --
campos que não existem na nossa convenção de nomes, então essas duas colunas
saem ``NA`` no CSV. Todas as outras colunas (nodes, pareto, edges, p_edges,
mean_in/out, mean_pareto_in, pareto_num_path, pareto_mean_path) são
corretas e não dependem desse parsing.

Uso::

    python -m mowflop.run_metrics_r --tag g1.0 --algo MOEAD
    python -m mowflop.run_metrics_r --tag x60 --algo NSGA2
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .io_raw import repo_root

CONST_LINES = {
    "iset": re.compile(r'^iset\s*<-\s*".*?"'),
    "algo": re.compile(r'^algo\s*<-\s*".*?"'),
    # outfolder is already "metrics/" in the original script -- rewriting it
    # to the same value would produce zero diff and break the safety check
    # below, which assumes every constant it touches actually changes.
}


def rewrite(source: str, values: dict[str, str]) -> tuple[str, list[int]]:
    """Reescreve só ``iset``/``algo``/``outfolder`` no texto-fonte de ``metrics.R``.

    Args:
        source: conteúdo original de ``metrics.R``.
        values: novos valores para ``iset``, ``algo`` e ``outfolder``.

    Returns:
        Tupla ``(fonte reescrita, números das linhas alteradas)``.

    Raises:
        ValueError: se alguma das três constantes não for encontrada no fonte.
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
        raise ValueError(f"could not find the constants in metrics.R: {sorted(missing)}")
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
    parser.add_argument("--algo", required=True, choices=["MOEAD", "NSGA2"])
    parser.add_argument("--repo", default=str(repo_root()))
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    script = repo / "scripts" / "metrics.R"
    if not script.is_file():
        print(f"not found: {script}", file=sys.stderr)
        return 1

    iset = f"mowflop_{args.tag}"
    infolder = repo / "stns" / iset / args.algo
    if not infolder.is_dir():
        print(f"missing STNs: {infolder}", file=sys.stderr)
        return 1
    (repo / "metrics").mkdir(parents=True, exist_ok=True)

    values = {"iset": iset, "algo": args.algo}
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
        print("refusing to run: more than the three constants differ", file=sys.stderr)
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
