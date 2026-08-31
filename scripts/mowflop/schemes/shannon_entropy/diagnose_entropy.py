"""RQ1: o particionamento por entropia de Shannon se aplica ao MoWFLOP?

Reproduz a Fig. 5 de Ochoa, Malan & Blum (2021) para os dados do MoWFLOP: a
curva de entropia por posição, ordenada de forma não crescente, com o ``z`` de
cada critério de área marcado.  Passa pelo mesmo caminho de código usado para
produzir as STNs, então o relatório descreve o particionamento que é de fato
emitido.

Escreve em ``reports/rq1_entropy/``:

``summary.csv``
    uma linha por (instância, config): densidade, ``|S(T)|``, estatísticas de
    entropia e ``z`` para cada critério de área (:data:`AREA_PERCENTS`).
``entropy_curve_*.csv``
    os valores de entropia ordenados -- a curva em si.
``figures/entropy_curve_*.{png,pdf}``
    a figura, se ``--figs`` for dado.

Uso::

    python -m mowflop.schemes.shannon_entropy.diagnose_entropy --instance ns101 --config p100_i50 --figs
"""

from __future__ import annotations

import argparse
import glob
import math
from collections import Counter
from pathlib import Path

import pandas as pd

from . import entropy as entropy_mod
from ... import io_raw

AREA_PERCENTS = (50, 60, 70, 80, 90)


def load_pmed7(folder: str | Path) -> tuple[list[entropy_mod.Solution], int]:
    """Carrega os dados de p-mediana dos próprios autores do esquema.

    Não é mais usada pela CLI deste script -- a comparação com esse controle
    foi removida daqui --, mas segue neste módulo porque
    :mod:`mowflop.test.test_partition` a importa para a regressão contra os
    números publicados no artigo.

    Args:
        folder: pasta com os arquivos ``*.out`` de trajetória.

    Returns:
        Tupla ``(soluções únicas, número de posições)``.

    Raises:
        FileNotFoundError: se nenhum ``*.out`` for encontrado na pasta.
    """
    unique: set[str] = set()
    for path in sorted(glob.glob(str(Path(folder) / "*.out"))):
        with open(path, "r", encoding="utf-8") as handle:
            next(handle, None)  # cabeçalho
            for line in handle:
                parts = line.split()
                if len(parts) >= 5:
                    # colunas 2 e 4 são os dois traços binários registrados na linha
                    unique.add(parts[2])
                    unique.add(parts[4])
    if not unique:
        raise FileNotFoundError(f"no *.out trajectories under {folder}")
    n = len(next(iter(unique)))
    return [entropy_mod.from_binary_string(s) for s in unique], n


def curve_stats(entropy: list[float]) -> dict:
    """Resumo estatístico de uma curva de entropia.

    Args:
        entropy: entropia de cada posição, em qualquer ordem.

    Returns:
        Dicionário com total, máximo, mediana não nula, fração de posições
        zeradas e o tamanho do maior bloco de empate.
    """
    values = sorted(entropy, reverse=True)
    ties = Counter(round(value, 12) for value in values)
    nonzero = [value for value in values if value > 0.0]
    return {
        "n": len(values),
        "entropy_total": sum(values),
        "entropy_max": values[0] if values else 0.0,
        "entropy_median_nonzero": (
            sorted(nonzero)[len(nonzero) // 2] if nonzero else 0.0
        ),
        "positions_nonzero": len(nonzero),
        "fraction_zero": 1.0 - len(nonzero) / len(values) if values else 0.0,
        "distinct_values": len(ties),
        "largest_tie_block": max(ties.values()) if ties else 0,
    }


def analyse(
    solutions: list[entropy_mod.Solution],
    n: int,
    tie_break: str = "random",
    seed: int = 0,
) -> tuple[list[float], list[int], dict]:
    """Entropia, ranking e estatísticas de ``z`` para cada critério de área.

    Args:
        solutions: soluções únicas de ``S(T)``.
        n: número total de posições do espaço de busca.
        tie_break: política de desempate do ranking de entropia.
        seed: semente do desempate aleatório.

    Returns:
        Tupla ``(entropia por posição, ranking, estatísticas)``, com
        ``z_<percent>`` e ``tie_at_z_<percent>`` para cada percentual de
        :data:`AREA_PERCENTS`.
    """
    entropy = entropy_mod.position_entropy(solutions, n)
    order = entropy_mod.rank_positions(entropy, tie_break=tie_break, seed=seed)
    ordered = [entropy[i] for i in order]
    stats = curve_stats(entropy)
    for percent in AREA_PERCENTS:
        z = entropy_mod.area_partition_z(ordered, percent)
        stats[f"z_{percent}"] = z
        if z:
            cutoff = ordered[z - 1]
            stats[f"tie_at_z_{percent}"] = sum(
                1 for value in ordered if math.isclose(value, cutoff)
            )
        else:
            stats[f"tie_at_z_{percent}"] = 0
    return entropy, order, stats


def _save(fig, folder: Path, name: str) -> None:
    """Salva uma figura em PNG e PDF na pasta dada.

    Args:
        fig: figura do matplotlib.
        folder: pasta de destino (criada se não existir).
        name: nome do arquivo, sem extensão.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        fig.savefig(folder / f"{name}.{extension}", dpi=150, bbox_inches="tight")


def figure_entropy_curve(
    ordered: list[float], stats: dict, label: str, folder: Path, name: str
) -> None:
    """Fig. 5 do artigo para os nossos dados: a curva de entropia ordenada, com o ``z`` de cada critério.

    Args:
        ordered: entropia ordenada de forma não crescente.
        stats: estatísticas de :func:`analyse`, com os ``z_<percent>``.
        label: rótulo da (instância, config) no título.
        folder: pasta de destino das figuras.
        name: nome do arquivo, sem extensão.
    """
    import matplotlib.pyplot as plt

    ranks = range(1, len(ordered) + 1)
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.fill_between(ranks, ordered, color="tab:blue", alpha=0.20)
    ax.plot(ranks, ordered, color="tab:blue", lw=1.4)
    colors = plt.cm.viridis([i / len(AREA_PERCENTS) for i in range(len(AREA_PERCENTS))])
    for color, percent in zip(colors, AREA_PERCENTS, strict=True):
        z = stats.get(f"z_{percent}")
        if z:
            # uma linha vertical e uma anotação deslocada por critério de área, para não se sobreporem
            ax.axvline(z, color=color, ls="--", lw=1.0)
            ax.annotate(
                f"{percent}%: z={z}",
                xy=(z, 1.0),
                xytext=(2, -10 - 11 * AREA_PERCENTS.index(percent)),
                textcoords="offset points",
                fontsize=8,
                color=color,
            )
    ax.set_xscale("log")
    ax.set_xlabel("posição, ordenada por entropia decrescente (posto em L)")
    ax.set_ylabel("H(x_i)  [bits]")
    ax.set_title(
        f"Curva de entropia — {label}\n"
        f"H=0 em {stats['fraction_zero']:.1%} das posições; "
        f"maior bloco de empate: {stats['largest_tie_block']}"
    )
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    _save(fig, folder, name)
    plt.close(fig)


def diagnose(args) -> pd.DataFrame:
    """Roda o diagnóstico (tabelas e, opcionalmente, a figura) para os alvos pedidos.

    Args:
        args: argumentos já parseados de :func:`main`.

    Returns:
        DataFrame ``summary.csv``, uma linha por (instância, config).
    """
    out = Path(args.out_root) / "reports" / "rq1_entropy"
    figures = out / "figures"
    out.mkdir(parents=True, exist_ok=True)

    inv = io_raw.inventory(args.raw_root)
    if args.all:
        targets = [(str(i), str(c)) for i, c in inv.set_index(["instance", "config"]).index.unique()]
    else:
        targets = [(args.instance, args.config)]

    summaries = []
    for instance, config in targets:
        df = io_raw.load_trajectories(instance, config, root=args.raw_root)
        n = io_raw.n_positions(instance, root=args.raw_root)
        # S(T): as soluções únicas da trajetória, como o artigo pede
        solutions = [entropy_mod.from_index_list(text) for text in df["occupied"].unique()]
        tau = len(solutions[0])
        entropy, order, stats = analyse(solutions, n, args.tie_break, args.seed)
        ordered = [entropy[i] for i in order]
        label = f"{instance} / {config}"
        key = f"{instance}_{config}"

        stats.update(
            {
                "instance": instance,
                "config": config,
                "tau": tau,
                "density": tau / n,
                "recordings": len(df),
                "unique_solutions": len(solutions),
                "algorithms": "|".join(sorted(df["algorithm"].unique().tolist())),
            }
        )
        summaries.append(stats)

        pd.DataFrame({"rank": range(1, n + 1), "entropy": ordered}).to_csv(
            out / f"entropy_curve_{key}.csv", index=False
        )
        if args.figs:
            figure_entropy_curve(ordered, stats, label, figures, f"entropy_curve_{key}")

    summary = pd.DataFrame(summaries)
    front = ["instance", "config", "algorithms", "n", "tau", "density",
             "recordings", "unique_solutions"]
    summary = summary[front + [c for c in summary.columns if c not in front]]
    summary.to_csv(out / "summary.csv", index=False)
    return summary


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
    parser.add_argument("--tie-break", choices=["index", "random"], default="random")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--raw-root")
    parser.add_argument("--out-root", default=str(io_raw.repo_root()))
    parser.add_argument("--figs", action="store_true", help="also render the figure")
    args = parser.parse_args(argv)

    if not args.all and not (args.instance and args.config):
        parser.error("give --instance and --config, or --all")

    summary = diagnose(args)
    with pd.option_context("display.width", 200, "display.max_columns", 40):
        print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
