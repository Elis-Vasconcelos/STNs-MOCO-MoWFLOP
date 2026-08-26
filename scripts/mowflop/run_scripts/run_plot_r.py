"""Desenha as STNs com o ``scripts/plot.R`` deste repositório, um arquivo por algoritmo.

No modelo multiobjetivo (Ochoa, Liefooghe, Lavinas & Aranha 2023) uma STN
mesclada mescla os grafos dos *p vetores de escalarização de um algoritmo* --
o que ``create .R`` já fez, nos atributos ``Vector``/``Vectors``.  Mesclar
entre algoritmos é a construção monoobjetivo do trabalho de 2021, não este.
Então cada algoritmo ganha sua própria figura, desenhada pelo seu
``plot_stn``.

``plot.R`` não pode simplesmente ser rodado: o driver no final do arquivo
assume seis arquivos por algoritmo e os indexa como ``c(1, 3, 5)`` /
``c(2, 4, 6)`` (o design rho-mnk), enquanto temos um arquivo por algoritmo.
Este script portanto reaproveita ``plot_stn`` **ao pé da letra** -- pega o
prefixo de ``plot.R`` até o fim dessa função, reescreve só as constantes de
pasta (como ``run_scripts/run_create_r.py`` faz), e adiciona um driver que
itera sobre quaisquer arquivos que existam.  Confere que nada além dessas
constantes mudou antes de rodar.

Layouts, ambos de ``plot_stn``:

``of``  espaço objetivo -- ``x = f1``, ``y = f2``, com a frente de referência
        desenhada por cima.  O default sensato aqui: nenhum layout de força a
        calcular, e a figura é diretamente legível como custo contra potência.
``fd``  força dirigida (``graphopt``).  Opcional: é lento e vira uma bola de
        lã com dezenas de milhares de nós.

Uso::

    python -m mowflop.run_scripts.run_plot_r --tag x60
    python -m mowflop.run_scripts.run_plot_r --tag raw --layout both --pf-size 0.8 --pf-alpha 0.6
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

CONSTANTS = {
    "infolder": re.compile(r'^infolder\s*<-\s*".*?"'),
    "outfolder": re.compile(r'^outfolder\s*<-\s*".*?"'),
}
NUMERIC_CONSTANTS = {
    "pSize": re.compile(r"^pSize\s*<-\s*[0-9.]+"),
    "pAlpha": re.compile(r"^pAlpha\s*<-\s*[0-9.]+"),
}

DRIVER = r"""
# ---- driver added by mowflop.run_scripts.run_plot_r ------------------------
# One picture per algorithm: the STN of an algorithm already merges its p
# scalarisation vectors (see the Vectors attribute built by "create .R").
for (iset in isets) {
   files <- list.files(paste0(infolder, iset))
   if (length(files) == 0) next
   for (f in files) {
      for (mode in LAYOUTS) {
         p <- plot_stn(f, iset, bObjLay = (mode == "of"))
         stem <- substr(f, 1, nchar(f) - 6)   # drop ".RData"
         out <- paste0(outfolder, stem, "_", mode, ".png")
         ggsave(p, filename = out, device = "png",
                width = 9, height = 7, dpi = 150, limitsize = FALSE)
         cat("->", out, "\n")
      }
   }
}
"""


def cut_prefix(source: str) -> tuple[list[str], int]:
    """Linhas de ``plot.R`` até o fim (inclusive) de ``plot_stn``.

    Args:
        source: conteúdo original de ``plot.R``.

    Returns:
        Tupla ``(linhas do prefixo, índice da última linha do prefixo)``.

    Raises:
        ValueError: se ``plot_stn`` não for encontrada, ou se o fim da função
            não puder ser localizado.
    """
    lines = source.splitlines(keepends=True)
    if not any("plot_stn <- function" in line for line in lines):
        raise ValueError("plot_stn not found in plot.R")
    # procura o "return(p)" da função e depois o "}" de fechamento seguinte
    for i, line in enumerate(lines):
        if line.strip() == "return(p)":
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "}":
                    return lines[: j + 1], j + 1
    raise ValueError("could not find the end of plot_stn in plot.R")


def rewrite(lines: list[str], folders: dict[str, str], numbers: dict[str, float]) -> tuple[str, list[int]]:
    """Reescreve as constantes de pasta e, se dados, os parâmetros numéricos de estilo.

    Args:
        lines: linhas do prefixo de ``plot.R`` (ver :func:`cut_prefix`).
        folders: novos valores para ``infolder`` e ``outfolder``.
        numbers: novos valores para ``pSize``/``pAlpha``; ``None`` mantém o
            valor original.

    Returns:
        Tupla ``(fonte reescrita, números das linhas alteradas)``.
    """
    changed = []
    for i, line in enumerate(lines):
        for name, pattern in CONSTANTS.items():
            if pattern.match(line):
                lines[i] = f'{name} <- "{folders[name]}"\n'
                changed.append(i + 1)
        for name, pattern in NUMERIC_CONSTANTS.items():
            if numbers.get(name) is not None and pattern.match(line):
                lines[i] = f"{name} <- {numbers[name]}\n"
                changed.append(i + 1)
    return "".join(lines), changed


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando.

    Args:
        argv: argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns:
        Código de saída do ``Rscript`` chamado, ou um código próprio se algo
        falhar antes disso (arquivo ausente, STNs ausentes, diff inesperado,
        ``Rscript`` não encontrado).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", required=True, help="dataset tag, e.g. x60, raw")
    parser.add_argument("--layout", choices=["of", "fd", "both"], default="of")
    parser.add_argument("--pf-size", type=float, help="override pSize in plot.R")
    parser.add_argument("--pf-alpha", type=float, help="override pAlpha in plot.R")
    parser.add_argument("--repo", default=str(repo_root()))
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--lib", default=str(Path.home() / "R" / "library"),
                        help="extra R library path (ggraph lives there)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    script = repo / "scripts" / "plot.R"
    if not script.is_file():
        print(f"not found: {script}", file=sys.stderr)
        return 1

    folders = {
        "infolder": f"stns/mowflop_{args.tag}/",
        "outfolder": f"plots/mowflop_{args.tag}/",
    }
    if not (repo / folders["infolder"]).is_dir():
        print(f"missing STNs: {repo / folders['infolder']}", file=sys.stderr)
        return 1
    (repo / folders["outfolder"]).mkdir(parents=True, exist_ok=True)

    source = script.read_text(encoding="utf-8")
    prefix, cut = cut_prefix(source)
    original_prefix = "".join(prefix)
    rewritten, changed = rewrite(
        list(prefix), folders, {"pSize": args.pf_size, "pAlpha": args.pf_alpha}
    )

    # diff de segurança: só as constantes reescritas podem diferir do prefixo original
    diff = [
        line
        for line in difflib.unified_diff(
            original_prefix.splitlines(), rewritten.splitlines(), lineterm="", n=0
        )
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    print(f"plot.R: reaproveitando as linhas 1-{cut} (até o fim de plot_stn) sem alteração,")
    print(f"        exceto as constantes nas linhas {changed}:")
    for line in diff:
        print(f"  {line}")
    # diff vazio é ok: acontece quando o valor reescrito já era igual ao
    # anterior (ex.: plot.R já apontava pra essa mesma tag) -- só um diff de
    # tamanho *diferente* de 0 ou 2*len(changed) indica que outra coisa mudou
    if len(diff) not in (0, 2 * len(changed)):
        print("refusing to run: something other than the constants changed", file=sys.stderr)
        return 1

    layouts = ["of", "fd"] if args.layout == "both" else [args.layout]
    header = (
        f'.libPaths(c("{args.lib}", .libPaths()))\n'
        if Path(args.lib).is_dir()
        else ""
    )
    names = ", ".join(f'"{mode}"' for mode in layouts)
    body = header + rewritten + f"\nLAYOUTS <- c({names})\n" + DRIVER

    with tempfile.NamedTemporaryFile(
        "w", suffix=".R", dir=str(repo / "scripts"), delete=False, encoding="utf-8"
    ) as handle:
        handle.write(body)
        temporary = Path(handle.name)

    if args.dry_run:
        temporary.unlink(missing_ok=True)
        print("dry run; R não foi chamado")
        return 0

    try:
        completed = subprocess.run([args.rscript, str(temporary)], cwd=str(repo), check=False)
    except FileNotFoundError:
        print(f"{args.rscript} não encontrado", file=sys.stderr)
        return 127
    finally:
        temporary.unlink(missing_ok=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
