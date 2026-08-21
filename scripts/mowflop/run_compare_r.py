"""Gera as grades comparativas 2x3 (algo x P) que ``plot.R`` já sabia fazer, para nossos dados.

``plot.R`` já tem ``arrange_plot_fd``/``arrange_plot_of`` (linhas 99-116):
``ggpubr::ggarrange(..., common.legend = T, legend = "right", nrow = 2, ncol = 3)``,
com título por painel via ``plot_stn``. É o padrão estabelecido por Arthur/Ochoa
para comparar vários arquivos lado a lado com uma legenda só -- só que o
driver original indexa ``c(1, 3, 5)``/``c(2, 4, 6)`` do jeito rho-mnk (dois
arquivos por algoritmo, k=1 e k=4), enquanto temos um arquivo por (algoritmo, P).
Este script reaproveita o mesmo prefixo de ``plot.R`` que ``run_plot_r.py`` já
reaproveita (``plot_stn`` ao pé da letra, mesmo diff de segurança) e troca só
o driver final por um que:

1. Sobrescreve o título por painel para ``"ALGO instance p<P>i<k>"`` (em vez do
   ``"ALGO r = instance"`` residual do benchmark rho-mnk) -- sem tocar
   ``plot_stn``, só ``+ ggtitle(...)`` no ggplot já retornado.
2. Fixa a escala de Count (tamanho dos nós, alpha das arestas) num range
   *global*, calculado antes de desenhar qualquer painel, a partir do maior
   ``Count`` de nó e de aresta entre **todos** os arquivos comparados (todas
   as tags/kappas, os dois algoritmos, os três P). Sem isso cada painel
   normaliza Count sozinho (default do ggplot), e o mesmo tamanho visual
   passaria a significar contagens reais diferentes conforme o kappa -- o que
   inviabilizaria comparar o efeito do particionamento a olho. Count não
   depende do layout (``of``/``fd`` são o mesmo grafo, só reposicionado), então
   o mesmo máximo vale para os dois.

Uso::

    python -m mowflop.run_compare_r --tags x60,g0.5,g1.0,g2.0 --instance ns101 --layout of
    python -m mowflop.run_compare_r --tags g0.5,g1.0,g2.0 --instance ns178 --layout both
"""

from __future__ import annotations

import argparse
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

from .io_raw import repo_root
from .run_plot_r import cut_prefix, rewrite

P_ORDER = [10, 50, 100]


def discover_tags(repo: Path, instance: str) -> list[str]:
    """Toda tag com arquivos da instância dada, nos dois algoritmos.

    Usada como default de ``--tags``: sem isso, é fácil esquecer uma tag ao
    montar a lista à mão e acabar com um máximo de Count calculado sobre um
    subconjunto -- o que corta (vira ``NA``, invisível) qualquer valor real
    acima dele assim que essa tag aparecer numa comparação futura com o
    conjunto completo.

    Args:
        repo: raiz do repositório.
        instance: nome da instância.

    Returns:
        Tags (``x60``, ``g0.5``, ...) ordenadas, com arquivo de ``instance``
        em pelo menos um dos dois algoritmos.
    """
    found = []
    for d in sorted((repo / "stns").glob("mowflop_*")):
        tag = d.name[len("mowflop_") :]
        if any(next((d / algo).glob(f"*_{instance}_*"), None) is not None for algo in ("MOEAD", "NSGA2")):
            found.append(tag)
    return found

DRIVER_TEMPLATE = r"""
# ---- driver added by mowflop.run_compare_r ---------------------------------
tags <- c({tags})
instance <- "{instance}"
layouts <- c({layouts})
p_order <- c({p_order})

# Pass 1: global Count max across every (tag, algo, P) file for this instance,
# so the same node size / edge alpha always means the same real Count, no
# matter which tag/kappa/P/layout is being drawn.
node_max <- 0
edge_max <- 0
for (tag in tags) {{
   for (algo in c("MOEAD", "NSGA2")) {{
      dir <- paste0("stns/mowflop_", tag, "/", algo, "/")
      files <- list.files(dir, pattern = paste0("_", instance, "_"))
      for (f in files) {{
         load(paste0(dir, f), verbose = F)
         node_max <- max(node_max, V(STN)$Count)
         edge_max <- max(edge_max, E(STN)$Count)
      }}
   }}
}}
cat("global Count max -- nodes:", node_max, " edges:", edge_max, "\n")

for (tag in tags) {{
   for (mode in layouts) {{
      panels <- list()
      for (algo in c("MOEAD", "NSGA2")) {{
         dir <- paste0("stns/mowflop_", tag, "/", algo, "/")
         infolder <- dir
         files <- list.files(dir, pattern = paste0("_", instance, "_"))
         for (P in p_order) {{
            f <- files[grepl(paste0("_p", P, "i"), files)]
            if (length(f) == 0) next
            p <- plot_stn(f[1], "", bObjLay = (mode == "of"))
            t <- strsplit(sub("\\.RData$", "", f[1]), "_")[[1]]
            p <- p + ggtitle(paste0(t[1], " ", t[3], " ", t[6])) +
               scale_size(name = "Node Count", range = c(0.7, 4.2), limits = c(0, node_max)) +
               scale_edge_alpha(name = "Edge Count", limits = c(0, edge_max))
            panels[[paste0(algo, "_", P)]] <- p
         }}
      }}
      order <- c(paste0("MOEAD_", p_order), paste0("NSGA2_", p_order))
      order <- order[order %in% names(panels)]
      if (length(order) < 2 * length(p_order)) {{
         cat("skipping", tag, mode, "-- missing panels:",
             setdiff(c(paste0("MOEAD_", p_order), paste0("NSGA2_", p_order)), order), "\n")
         next
      }}
      arr <- ggarrange(plotlist = panels[order], common.legend = T, legend = "right",
                        nrow = 2, ncol = length(p_order))
      out <- paste0("plots/mowflop_", tag, "/compare_", instance, "_", mode, ".png")
      ggsave(arr, filename = out, device = "png", width = 14, height = 8, dpi = 150,
             bg = "white", limitsize = FALSE)
      cat("->", out, "\n")
   }}
}}
"""


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--tags",
        help="lista separada por vírgula, ex: x60,g0.5,g1.0,g2.0; "
        "default: toda tag com dados para --instance (recomendado -- "
        "garante que o máximo de Count é global de verdade, não de um subconjunto)",
    )
    parser.add_argument("--instance", required=True)
    parser.add_argument("--layout", choices=["of", "fd", "both"], default="of")
    parser.add_argument("--repo", default=str(repo_root()))
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--lib", default=str(Path.home() / "R" / "library"),
                        help="extra R library path (ggraph/ggpubr vivem lá)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    script = repo / "scripts" / "plot.R"
    if not script.is_file():
        print(f"not found: {script}", file=sys.stderr)
        return 1

    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    else:
        tags = discover_tags(repo, args.instance)
        if not tags:
            print(f"no tag has data for instance {args.instance!r}", file=sys.stderr)
            return 1
        print(f"--tags not given; auto-discovered for {args.instance}: {', '.join(tags)}")
    for tag in tags:
        for algo in ("MOEAD", "NSGA2"):
            d = repo / "stns" / f"mowflop_{tag}" / algo
            if not d.is_dir():
                print(f"missing STNs: {d}", file=sys.stderr)
                return 1

    source = script.read_text(encoding="utf-8")
    prefix, cut = cut_prefix(source)
    original_prefix = "".join(prefix)
    # infolder/outfolder are overwritten per-iteration by the driver below;
    # the values here only need to be syntactically valid placeholders.
    folders = {"infolder": "stns/mowflop_placeholder/", "outfolder": "plots/mowflop_placeholder/"}
    rewritten, changed = rewrite(list(prefix), folders, {"pSize": None, "pAlpha": None})

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
    if len(diff) != 2 * len(changed):
        print("refusing to run: something other than the constants changed", file=sys.stderr)
        return 1

    layouts = ["of", "fd"] if args.layout == "both" else [args.layout]
    header = (
        f'.libPaths(c("{args.lib}", .libPaths()))\n'
        if Path(args.lib).is_dir()
        else ""
    )
    driver = DRIVER_TEMPLATE.format(
        tags=", ".join(f'"{t}"' for t in tags),
        instance=args.instance,
        layouts=", ".join(f'"{m}"' for m in layouts),
        p_order=", ".join(str(p) for p in P_ORDER),
    )
    body = header + rewritten + driver

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
