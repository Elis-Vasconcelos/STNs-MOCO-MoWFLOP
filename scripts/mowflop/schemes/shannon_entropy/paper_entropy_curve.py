"""Desenha a curva de entropia no formato do artigo CEC 2027, a partir do CSV do ``diagnose_entropy``.

Uso (de dentro de ``scripts/``)::

    python -m mowflop.schemes.shannon_entropy.diagnose_entropy --instance ns509 --config p100_i50 --max-run 9 --out-root <pasta>
    python -m mowflop.schemes.shannon_entropy.paper_entropy_curve \\
        --csv <pasta>/reports/rq1_entropy/entropy_curve_ns509_p100_i50.csv --out <figura>.png --expect-z70 41
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from . import entropy as entropy_mod
from .diagnose_entropy import AREA_PERCENTS

SIZE_IN = (3.5, 1.8)
FONT_PT = 8.0
DPI = 600
X_MAX = 1e3
LABEL_GAP_PT = 1.5  # distância entre o rótulo de cada reta e a reta


def figure(ordered: list[float], stats: dict, path: Path) -> None:
    """Grava a curva ordenada com uma reta tracejada no ``z`` de cada critério de área.

    Args:
        ordered: entropia ordenada de forma não crescente.
        stats: ``z_<percent>`` de cada critério.
        path: PNG de saída.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=SIZE_IN, layout="constrained")
    ranks = range(1, len(ordered) + 1)
    ax.fill_between(ranks, ordered, color="tab:blue", alpha=0.20)
    ax.plot(ranks, ordered, color="tab:blue", lw=1.4)
    colors = plt.cm.viridis([i / len(AREA_PERCENTS) for i in range(len(AREA_PERCENTS))])
    lines = [(stats[f"z_{p}"], f"{p}%", c) for p, c in zip(AREA_PERCENTS, colors, strict=True) if stats[f"z_{p}"]]
    for z, _, color in lines:
        ax.axvline(z, color=color, ls="--", lw=1.0)
    ax.set_xscale("log")
    ax.tick_params(axis="both", which="both", labelsize=FONT_PT)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.set_xlim(right=X_MAX)
    ax.set_xlabel("Position rank", fontsize=FONT_PT)
    ax.set_ylabel("Entropy", fontsize=FONT_PT)
    # rótulo na vertical, à esquerda da reta e no topo, com fundo para a grade não cortá-lo
    for z, text, color in lines:
        ax.annotate(text, xy=(z, 1.0), xytext=(-LABEL_GAP_PT, 0), textcoords="offset points",
                    rotation=90, ha="right", va="top", fontsize=FONT_PT, color=color,
                    bbox={"boxstyle": "square,pad=0.05", "facecolor": ax.get_facecolor(), "linewidth": 0})
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando.

    Args:
        argv: argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns:
        0 se a figura foi gravada; 1 se o CSV não estiver ordenado ou o ``z``
        de 70% não bater com ``--expect-z70``.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--expect-z70", type=int, help="aborta se z(70%%) for diferente")
    args = parser.parse_args(argv)

    ordered = pd.read_csv(args.csv).sort_values("rank")["entropy"].tolist()
    if any(a < b for a, b in zip(ordered, ordered[1:])):
        print(f"{args.csv}: entropia não está em ordem não crescente", file=sys.stderr)
        return 1
    stats = {f"z_{p}": entropy_mod.area_partition_z(ordered, p) for p in AREA_PERCENTS}
    print(" ".join(f"{k}={v}" for k, v in stats.items()))
    if args.expect_z70 is not None and stats["z_70"] != args.expect_z70:
        print(f"z_70 = {stats['z_70']}, esperado {args.expect_z70}", file=sys.stderr)
        return 1
    figure(ordered, stats, Path(args.out))
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
