"""RQ1: o ranking de entropia de Shannon é reprodutível? (``rank_stab``)

O esquema de Shannon ordena as posições candidatas pela entropia de cada uma
sobre as soluções visitadas e retém as do topo.  Se essa ordem reflete posições
genuinamente informativas, ela deve se repetir em execuções independentes.

A métrica divide as ``r`` execuções em duas metades disjuntas (as ``r/2``
primeiras e as ``r/2`` últimas), calcula a entropia de cada posição
separadamente em cada metade e mede a concordância entre as duas ordens pela
correlação de Spearman.  ``≈ 1``: as metades concordam sobre quais posições
importam, e o ranking é reprodutível.  ``≈ 0``: a ordem é decidida pelo acaso
amostral.  Especificação original em ``references/rank_stab.md``.

Escreve ``reports/rq1_rank_stab/summary.csv`` e, com ``--figs``, a figura
densidade × ``rank_stab``.

Uso::

    python -m mowflop.schemes.shannon_entropy.rank_stability --all --figs
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from . import entropy as entropy_mod
from .diagnose_entropy import _save
from ... import io_raw


def half_entropy(df: pd.DataFrame, runs: list[int], n: int) -> list[float]:
    """Entropia de Shannon de cada posição, sobre as soluções visitadas por um grupo de runs.

    Junta os registros das runs do grupo e mantém cada solução uma vez só (uma
    solução vista em várias runs ou gerações conta uma vez).  Para cada posição
    ``i``, ``p`` é a fração dessas soluções com turbina em ``i`` e
    ``H(x_i) = -p log2 p - (1-p) log2 (1-p)``: 0 se a posição nunca ou sempre
    está ocupada, 1 bit se está ocupada em metade das soluções.

    Args:
        df: registros da (instância, config), com ``run_id`` e ``occupied``.
        runs: runs do grupo.
        n: número total de posições.

    Returns:
        ``H(x_i)`` de cada posição, na ordem do índice.
    """
    texts = df.loc[df["run_id"].isin(runs), "occupied"].unique()
    return entropy_mod.position_entropy([entropy_mod.from_index_list(t) for t in texts], n)


def rank_stab(df: pd.DataFrame, n: int) -> dict:
    """Concordância entre as entropias por posição de duas metades das runs.

    Ordena as runs, põe a primeira metade num grupo e a segunda no outro,
    calcula a curva de entropia de cada grupo com :func:`half_entropy` e
    correlaciona as duas curvas com Spearman, posição a posição.

    O Spearman converte cada curva em postos (a posição de maior entropia
    recebe o maior posto) e mede a correlação entre os postos.  Por isso
    aplicá-lo direto às entropias equivale a comparar as duas listas de
    posições ordenadas por entropia.  Posições empatadas recebem o posto
    médio.  (``entropy_mod.rank_positions`` não é usada porque desempata ao
    acaso, e a ordem dentro de um bloco empatado viraria ruído da semente.)

    Args:
        df: registros da (instância, config), com ``run_id`` e ``occupied``.
        n: número total de posições.

    Returns:
        ``runs``, ``rank_stab``, ``rank_stab_active`` e ``positions_active``.
    """
    runs = sorted(df["run_id"].unique())
    half = len(runs) // 2
    h1 = half_entropy(df, runs[:half], n)
    h2 = half_entropy(df, runs[half:], n)
    # posições com H = 0 nas duas metades têm o mesmo rank nas duas e inflam o
    # rho; rank_stab_active é o mesmo Spearman só onde alguma metade tem H > 0
    active = [i for i in range(n) if h1[i] > 0 or h2[i] > 0]
    return {
        "runs": len(runs),
        "rank_stab": spearmanr(h1, h2).statistic,
        "rank_stab_active": spearmanr(
            [h1[i] for i in active], [h2[i] for i in active]
        ).statistic,
        "positions_active": len(active),
    }


def figure_vs_density(summary: pd.DataFrame, folder: Path) -> None:
    """Densidade × ``rank_stab``, com as duas leituras.

    Args:
        summary: o ``summary.csv``.
        folder: pasta de destino.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.scatter(summary["density"], summary["rank_stab"], color="tab:orange",
               label="todas as posições")
    ax.scatter(summary["density"], summary["rank_stab_active"], color="tab:blue",
               marker="s", label="só as posições ativas (H > 0)")
    ax.axhline(0.0, color="0.6", ls="--", lw=1.0)
    ax.set_xscale("log")
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel("densidade  τ / |P|")
    ax.set_ylabel("rank_stab  (ρ de Spearman)")
    ax.set_title("Estabilidade do ranking de entropia em função da densidade")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    _save(fig, folder, "rank_stab_vs_density")
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando.

    Args:
        argv: argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns:
        Código de saída do processo.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instance")
    parser.add_argument("--config")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--raw-root")
    parser.add_argument("--out-root", default=str(io_raw.out_root()))
    parser.add_argument("--figs", action="store_true", help="also render the figure")
    args = parser.parse_args(argv)
    if not args.all and not (args.instance and args.config):
        parser.error("give --instance and --config, or --all")

    out = Path(args.out_root) / "reports" / "rq1_rank_stab"
    out.mkdir(parents=True, exist_ok=True)
    if args.all:
        inv = io_raw.inventory(args.raw_root)
        targets = list(inv.set_index(["instance", "config"]).index.unique())
    else:
        targets = [(args.instance, args.config)]

    rows = []
    for instance, config in targets:
        df = io_raw.load_trajectories(instance, config, root=args.raw_root)
        n = io_raw.n_positions(instance, root=args.raw_root)
        tau = len(df["occupied"].iloc[0].split())
        rows.append({"instance": instance, "config": config, "n": n, "tau": tau,
                     "density": tau / n, **rank_stab(df, n)})

    summary = pd.DataFrame(rows)
    summary.to_csv(out / "summary.csv", index=False)
    if args.figs:
        figure_vs_density(summary, out / "figures")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
