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

Escreve em ``reports/rq1_rank_stab/``: ``summary.csv`` (uma linha por
instância e config) e ``rank_stab_curve_*.csv`` (as duas curvas de entropia,
uma linha por posição).  Com ``--figs``, também a figura densidade ×
``rank_stab`` e, por (instância, config), o diagrama de dispersão de uma metade
contra a outra.  Saída e filtro de instâncias seguem
``$MOWFLOP_OUT`` e ``$MOWFLOP_INSTANCE_PATTERN``, como em :mod:`.diagnose_entropy`.

Uso::

    python -m mowflop.schemes.shannon_entropy.rank_stability --all --figs
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from . import entropy as entropy_mod
from .diagnose_entropy import _save, all_targets
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


def half_curves(df: pd.DataFrame, n: int) -> tuple[list[int], list[float], list[float]]:
    """Curva de entropia de cada metade das runs.

    Ordena as runs, põe a primeira metade num grupo e a segunda no outro, e
    calcula a entropia por posição de cada grupo com :func:`half_entropy`.

    Args:
        df: registros da (instância, config), com ``run_id`` e ``occupied``.
        n: número total de posições.

    Returns:
        Tupla ``(runs, H da primeira metade, H da segunda metade)``.
    """
    runs = sorted(df["run_id"].unique())
    half = len(runs) // 2
    return runs, half_entropy(df, runs[:half], n), half_entropy(df, runs[half:], n)


def stab_from_curves(runs: list[int], h1: list[float], h2: list[float]) -> dict:
    """``rank_stab`` a partir das curvas das duas metades.

    Args:
        runs: runs da (instância, config).
        h1: entropia por posição da primeira metade.
        h2: entropia por posição da segunda metade.

    Returns:
        ``runs``, ``rank_stab``, ``rank_stab_p``, ``rank_stab_active``,
        ``rank_stab_active_p`` e ``positions_active``.  Os ``_p`` são o
        valor-p do teste de Spearman; com milhares de posições eles são
        minúsculos para qualquer rho não nulo, então o que interessa é o
        tamanho do rho, não a significância.
    """
    # posições com H = 0 nas duas metades têm o mesmo rank nas duas e inflam o
    # rho; rank_stab_active é o mesmo Spearman só onde alguma metade tem H > 0
    active = [i for i in range(len(h1)) if h1[i] > 0 or h2[i] > 0]
    overall = spearmanr(h1, h2)
    only_active = spearmanr([h1[i] for i in active], [h2[i] for i in active])
    return {
        "runs": len(runs),
        "rank_stab": overall.statistic,
        "rank_stab_p": overall.pvalue,
        "rank_stab_active": only_active.statistic,
        "rank_stab_active_p": only_active.pvalue,
        "positions_active": len(active),
    }


def retained_from_curve(
    entropy: list[float], percent: float = 60.0, seed: int = 0
) -> set[int]:
    """Posições retidas pelo critério de área, a partir de uma curva de entropia.

    Args:
        entropy: ``H(x_i)`` de cada posição, na ordem do índice.
        percent: critério de área ``X``.
        seed: semente do desempate aleatório do ranking.

    Returns:
        Conjunto dos índices das ``z`` posições retidas.
    """
    order = entropy_mod.rank_positions(entropy, tie_break="random", seed=seed)
    z = entropy_mod.area_partition_z([entropy[i] for i in order], percent)
    return set(order[:z])


def overlap_stats(
    h1: list[float], h2: list[float], n: int, percent: float = 60.0, seed: int = 0
) -> tuple[dict, set[int], set[int]]:
    """Sobreposição entre os conjuntos retidos por cada metade das runs.

    O ``rank_stab`` mede a ordem completa, inclusive na cauda de entropia
    baixa, que não decide nada.  O que o esquema de fato usa é o conjunto
    ``L_z``: aqui o critério de área é aplicado a cada metade separadamente e
    conta-se quantas posições as duas retêm em comum.

    ``retained_overlap`` é essa contagem sobre o tamanho médio dos dois
    conjuntos (``z_h1`` e ``z_h2`` diferem um pouco): 1 = as duas metades
    retêm exatamente as mesmas posições, 0 = nenhuma em comum.
    ``retained_overlap_random`` é o mesmo número se cada metade sorteasse suas
    posições ao acaso entre as ``n`` do espaço (``E|A∩B| = z1 z2 / n``) -- a
    régua contra a qual ler o valor observado.

    Args:
        h1: entropia por posição da primeira metade.
        h2: entropia por posição da segunda metade.
        n: número total de posições.
        percent: critério de área ``X``.
        seed: semente do desempate aleatório do ranking.

    Returns:
        Tupla ``(estatísticas, retidas pela 1ª metade, retidas pela 2ª)``.
    """
    keep1 = retained_from_curve(h1, percent, seed)
    keep2 = retained_from_curve(h2, percent, seed)
    shared = len(keep1 & keep2)
    mean_z = (len(keep1) + len(keep2)) / 2
    return (
        {
            "z_h1": len(keep1),
            "z_h2": len(keep2),
            "retained_shared": shared,
            "retained_overlap": shared / mean_z if mean_z else 0.0,
            "retained_overlap_random": (
                (len(keep1) * len(keep2) / n) / mean_z if mean_z else 0.0
            ),
        },
        keep1,
        keep2,
    )


def retained_positions(
    df: pd.DataFrame, n: int, percent: float = 60.0, seed: int = 0
) -> set[int]:
    """Posições retidas pelo critério de área sobre ``S(T)`` inteiro.

    É o mesmo ``L_z`` que o ``partition.py`` usa para emitir as STNs da tag
    ``x<percent>``; aqui ele só marca, nas figuras, quais posições o esquema de
    fato mantém.  Usa todas as runs, não as metades.

    Args:
        df: registros da (instância, config), com ``occupied``.
        n: número total de posições.
        percent: critério de área ``X`` (o padrão, 60, é a tag ``x60``).
        seed: semente do desempate aleatório do ranking.

    Returns:
        Conjunto dos índices das ``z`` posições retidas.
    """
    solutions = [entropy_mod.from_index_list(t) for t in df["occupied"].unique()]
    return retained_from_curve(entropy_mod.position_entropy(solutions, n), percent, seed)


def figure_halves(
    h1: list[float],
    h2: list[float],
    keep1: set[int],
    keep2: set[int],
    stats: dict,
    label: str,
    folder: Path,
    name: str,
    percent: float = 60.0,
) -> None:
    """Entropia de uma metade contra a da outra, uma posição por ponto.

    Mostra de onde vem o rho: uma nuvem difusa em toda a faixa é um ranking
    instável em todo lugar; uma nuvem que só se espalha perto de ``H = 0`` é
    instável apenas na cauda, onde a ordem não decide o particionamento.

    As cores são o critério de área aplicado a **cada metade**, não ao
    conjunto agregado: retida pelas duas, por uma só, ou por nenhuma.  Marcar
    o conjunto retido pelas 10 runs juntas seria circular -- ele é escolhido
    com os mesmos dados que formam as duas metades.

    Args:
        h1: entropia por posição da primeira metade.
        h2: entropia por posição da segunda metade.
        keep1: posições retidas pelo critério de área na primeira metade.
        keep2: idem, na segunda.
        stats: :func:`stab_from_curves` e :func:`overlap_stats` juntos.
        label: rótulo da (instância, config) no título.
        folder: pasta de destino das figuras.
        name: nome do arquivo, sem extensão.
        percent: critério de área, só para a legenda.
    """
    import matplotlib.pyplot as plt

    both = sorted(keep1 & keep2)
    one = sorted(keep1 ^ keep2)
    neither = [i for i in range(len(h1)) if i not in keep1 and i not in keep2]
    fig, ax = plt.subplots(figsize=(5.4, 5.2))
    ax.scatter([h1[i] for i in neither], [h2[i] for i in neither], s=6, alpha=0.22,
               color="tab:blue", linewidths=0, label="nenhuma metade retém")
    ax.scatter([h1[i] for i in one], [h2[i] for i in one], s=20, alpha=0.75,
               color="tab:red", marker="x", linewidths=0.9,
               label=f"só uma metade retém ({len(one)})")
    ax.scatter([h1[i] for i in both], [h2[i] for i in both], s=20, alpha=0.9,
               color="tab:orange", linewidths=0,
               label=f"as duas retêm ({len(both)})")
    ax.plot([0, 1], [0, 1], color="0.6", ls="--", lw=1.0)
    ax.set_aspect("equal")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("H(x_i) nas 5 primeiras runs")
    ax.set_ylabel("H(x_i) nas 5 últimas runs")
    ax.set_title(
        f"Concordância entre metades — {label}\n"
        f"rho = {stats['rank_stab']:.3f}; "
        f"x{percent:g} por metade: z = {stats['z_h1']}/{stats['z_h2']}, "
        f"em comum = {stats['retained_shared']} ({stats['retained_overlap']:.0%})",
        fontsize=10,
    )
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    _save(fig, folder, name)
    plt.close(fig)


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

    Atalho de :func:`half_curves` seguido de :func:`stab_from_curves`, para
    quem quer só o número; a CLI chama as duas separadamente, porque também
    escreve as curvas.

    Args:
        df: registros da (instância, config), com ``run_id`` e ``occupied``.
        n: número total de posições.

    Returns:
        O dicionário de :func:`stab_from_curves`.
    """
    return stab_from_curves(*half_curves(df, n))


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
    parser.add_argument("--percent", type=float, default=60.0,
                        help="critério de área que marca as posições retidas (default 60)")
    parser.add_argument("--figs", action="store_true", help="also render the figures")
    args = parser.parse_args(argv)
    if not args.all and not (args.instance and args.config):
        parser.error("give --instance and --config, or --all")

    out = Path(args.out_root) / "reports" / "rq1_rank_stab"
    out.mkdir(parents=True, exist_ok=True)
    if args.all:
        targets = all_targets(args.raw_root)
    else:
        targets = [(args.instance, args.config)]

    rows = []
    for instance, config in targets:
        df = io_raw.load_trajectories(instance, config, root=args.raw_root)
        n = io_raw.n_positions(instance, root=args.raw_root)
        tau = len(df["occupied"].iloc[0].split())
        runs, h1, h2 = half_curves(df, n)
        stats = stab_from_curves(runs, h1, h2)
        rows.append({"instance": instance, "config": config, "n": n, "tau": tau,
                     "density": tau / n, **stats})

        key = f"{instance}_{config}"
        overlap, keep1, keep2 = overlap_stats(h1, h2, n, args.percent)
        stats.update(overlap)
        rows[-1].update(overlap)
        retained = retained_positions(df, n, args.percent)
        pd.DataFrame(
            {
                "position": range(n),
                "h1": h1,
                "h2": h2,
                "retained": [i in retained for i in range(n)],
                "retained_h1": [i in keep1 for i in range(n)],
                "retained_h2": [i in keep2 for i in range(n)],
            }
        ).to_csv(out / f"rank_stab_curve_{key}.csv", index=False)
        if args.figs:
            figure_halves(h1, h2, keep1, keep2, stats, f"{instance} / {config}",
                          out / "figures", f"rank_stab_{key}", args.percent)

    summary = pd.DataFrame(rows)
    summary.to_csv(out / "summary.csv", index=False)
    if args.figs:
        figure_vs_density(summary, out / "figures")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
