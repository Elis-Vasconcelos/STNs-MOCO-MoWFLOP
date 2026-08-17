"""RQ1: is Shannon-entropy partitioning applicable to MoWFLOP?

Computes the diagnostic tables (CSV) and renders the figures (matplotlib) that
answer it.  Everything is driven by the same code path used to produce the STNs,
so the report describes the partitioning that is actually emitted.

Tables written to ``reports/rq1_entropy/``:

``summary.csv``
    one row per (instance, config): density, ``|S(T)|``, entropy statistics,
    ``z`` for each area criterion and whether that ``z`` landed inside a tie
    block (in which case the retained set is largely arbitrary -- the paper
    breaks those ties at random).
``entropy_curve_*.csv``
    the ranked entropy values, i.e. Fig. 5 of the paper for our data.
``z_sweep_*.csv``
    for a grid of ``z``: number of locations, compression, and how much
    trajectory overlap the partitioning buys (locations visited by both
    algorithms, and by more than one run).
``sample_size_*.csv``
    the same statistics over growing subsamples of ``S(T)``, which separates a
    real effect from an artefact of a small sample.

Figures to ``reports/rq1_entropy/figures/`` in PNG and PDF.

Usage::

    python -m mowflop.diagnose_entropy --instance ns101 --config p100_i50 \
        --control-pmed7 ../STNs/pmed7 --figs
"""

from __future__ import annotations

import argparse
import glob
import math
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import entropy as entropy_mod
from . import io_raw

AREA_PERCENTS = (50, 60, 70, 80, 90)
DEFAULT_SAMPLE_SIZES = (50, 500, 5000, 50000)


# --------------------------------------------------------------------------
# data assembly
# --------------------------------------------------------------------------
def solution_index(df: pd.DataFrame) -> dict[str, dict]:
    """For each distinct layout: which algorithms and runs visited it."""
    index: dict[str, dict] = {}
    for occupied, algorithm, run in zip(
        df["occupied"], df["algorithm"], df["run_id"], strict=True
    ):
        entry = index.get(occupied)
        if entry is None:
            entry = index[occupied] = {
                "solution": entropy_mod.from_index_list(occupied),
                "algorithms": set(),
                "runs": set(),
                "recordings": 0,
            }
        entry["algorithms"].add(str(algorithm))
        entry["runs"].add((str(algorithm), int(run)))
        entry["recordings"] += 1
    return index


def load_pmed7(folder: str | Path) -> tuple[list[entropy_mod.Solution], int]:
    """Control: the authors' own p-median data, where the scheme works."""
    unique: set[str] = set()
    for path in sorted(glob.glob(str(Path(folder) / "*.out"))):
        with open(path, "r", encoding="utf-8") as handle:
            next(handle, None)  # header
            for line in handle:
                parts = line.split()
                if len(parts) >= 5:
                    unique.add(parts[2])
                    unique.add(parts[4])
    if not unique:
        raise FileNotFoundError(f"no *.out trajectories under {folder}")
    n = len(next(iter(unique)))
    return [entropy_mod.from_binary_string(s) for s in unique], n


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def curve_stats(entropy: list[float]) -> dict:
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


def z_grid(n: int, extra: list[int]) -> list[int]:
    grid = {1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, n}
    grid.update(z for z in extra if 0 < z <= n)
    return sorted(z for z in grid if 0 < z <= n)


def sweep_z(
    index: dict[str, dict], order: list[int], zs: list[int]
) -> pd.DataFrame:
    """Locations and overlap as a function of the number of retained positions."""
    total_solutions = len(index)
    present = {algorithm for entry in index.values() for algorithm in entry["algorithms"]}
    # with a single algorithm logged, "shared between algorithms" is vacuously
    # zero and would read as evidence; report it as missing instead
    comparable = len(present) > 1
    rows = []
    for z in zs:
        keep = frozenset(order[:z])
        algorithms: dict[frozenset, set] = defaultdict(set)
        runs: dict[frozenset, set] = defaultdict(set)
        for entry in index.values():
            key = entry["solution"] & keep
            algorithms[key] |= entry["algorithms"]
            runs[key] |= entry["runs"]
        locations = len(algorithms)
        rows.append(
            {
                "z": z,
                "locations": locations,
                "solutions": total_solutions,
                "compression": locations / total_solutions,
                "shared_algorithms": (
                    sum(1 for v in algorithms.values() if len(v) > 1)
                    if comparable
                    else pd.NA
                ),
                "shared_runs": sum(1 for v in runs.values() if len(v) > 1),
            }
        )
    return pd.DataFrame(rows)


def sample_size_curves(
    solutions: list[entropy_mod.Solution],
    n: int,
    sizes: tuple[int, ...] = DEFAULT_SAMPLE_SIZES,
    seed: int = 0,
) -> pd.DataFrame:
    """Entropy curve over growing subsamples of ``S(T)``.

    A small sample flattens the curve on its own -- most positions are never
    touched, so their entropy is exactly zero and the ranking is a pile of ties.
    Recomputing over growing subsamples is what separates that artefact from a
    property of the problem.
    """
    import random

    rng = random.Random(seed)
    pool = list(solutions)
    rows = []
    for size in sorted({min(size, len(pool)) for size in (*sizes, len(pool))}):
        sample = pool if size == len(pool) else rng.sample(pool, size)
        ordered = sorted(entropy_mod.position_entropy(sample, n), reverse=True)
        for rank, value in enumerate(ordered, start=1):
            rows.append({"sample_size": size, "rank": rank, "entropy": value})
    return pd.DataFrame(rows)


def analyse(
    solutions: list[entropy_mod.Solution],
    n: int,
    tie_break: str = "index",
    seed: int = 0,
) -> tuple[list[float], list[int], dict]:
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


def ranking_stability(
    index: dict[str, dict], n: int, zs: list[int]
) -> pd.DataFrame:
    """Top-``z`` agreement between the two algorithms' own entropy rankings."""
    per_algorithm: dict[str, list[entropy_mod.Solution]] = defaultdict(list)
    for entry in index.values():
        for algorithm in entry["algorithms"]:
            per_algorithm[algorithm].append(entry["solution"])
    if len(per_algorithm) < 2:
        return pd.DataFrame(columns=["z", "overlap", "expected_by_chance"])
    rankings = {
        algorithm: entropy_mod.rank_positions(
            entropy_mod.position_entropy(sols, n), tie_break="index"
        )
        for algorithm, sols in per_algorithm.items()
    }
    first, second = sorted(rankings)
    rows = []
    for z in zs:
        a = set(rankings[first][:z])
        b = set(rankings[second][:z])
        rows.append(
            {
                "z": z,
                "algorithm_a": first,
                "algorithm_b": second,
                "overlap": len(a & b),
                "expected_by_chance": z * z / n,
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------
def _save(fig, folder: Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        fig.savefig(folder / f"{name}.{extension}", dpi=150, bbox_inches="tight")


def figure_entropy_curve(
    ordered: list[float], stats: dict, label: str, folder: Path, name: str
) -> None:
    """Fig. 5 of the paper for our data: the ranked entropy curve."""
    import matplotlib.pyplot as plt

    ranks = range(1, len(ordered) + 1)
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.fill_between(ranks, ordered, color="tab:blue", alpha=0.20)
    ax.plot(ranks, ordered, color="tab:blue", lw=1.4)
    colors = plt.cm.viridis([i / len(AREA_PERCENTS) for i in range(len(AREA_PERCENTS))])
    for color, percent in zip(colors, AREA_PERCENTS, strict=True):
        z = stats.get(f"z_{percent}")
        if z:
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


def figure_controls(curves: dict[str, list[float]], folder: Path, name: str) -> None:
    """Campaign against the controls, on a normalised rank axis."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    campaign = {k: v for k, v in curves.items() if k.startswith("MoWFLOP")}
    controls = {k: v for k, v in curves.items() if not k.startswith("MoWFLOP")}

    # One legend entry for the whole campaign once there are too many curves to
    # tell apart -- the point of the figure is that they all collapse together.
    lumped = len(campaign) > 4
    for i, (label, ordered) in enumerate(campaign.items()):
        n = len(ordered)
        ax.plot(
            [r / n for r in range(1, n + 1)],
            ordered,
            lw=1.0 if lumped else 1.5,
            color="tab:blue" if lumped else None,
            alpha=0.45 if lumped else 1.0,
            label=(f"campanha MoWFLOP ({len(campaign)} combinações)"
                   if lumped and i == 0 else
                   (None if lumped else f"{label} (n={n})")),
        )
    for label, ordered in controls.items():
        n = len(ordered)
        ax.plot([r / n for r in range(1, n + 1)], ordered, lw=2.0,
                color="tab:red", label=f"{label} (n={n})")
    ax.set_xlabel("posto normalizado em L  (posto / n)")
    ax.set_ylabel("H(x_i)  [bits]")
    ax.set_title("Curva de entropia: campanha real vs. controles")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    _save(fig, folder, name)
    plt.close(fig)


def figure_sample_size(curves: pd.DataFrame, label: str, folder: Path, name: str) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    for size, group in curves.groupby("sample_size"):
        ax.plot(group["rank"], group["entropy"], lw=1.3, label=f"|S(T)| = {size}")
    ax.set_xscale("log")
    ax.set_xlabel("posto em L")
    ax.set_ylabel("H(x_i)  [bits]")
    ax.set_title(f"Efeito do tamanho da amostra na curva de entropia — {label}")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    _save(fig, folder, name)
    plt.close(fig)


def figure_tradeoff(
    sweep: pd.DataFrame, stats: dict, label: str, folder: Path, name: str
) -> None:
    """Resolution against overlap: the figure that answers RQ1."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    solutions = int(sweep["solutions"].iloc[0])

    zs = [stats.get(f"z_{p}") for p in AREA_PERCENTS if stats.get(f"z_{p}")]
    if zs:
        ax.axvspan(min(zs), max(zs), color="grey", alpha=0.15, zorder=0)
        ax.text(
            math.sqrt(min(zs) * max(zs)),
            0.45,
            "faixa do critério de área (50%–90%)",
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="center",
            rotation=90,
            fontsize=8,
            color="dimgrey",
        )

    ax.plot(sweep["z"], sweep["locations"], color="tab:blue", marker="o", ms=3, lw=1.4,
            label="nº de localizações")
    ax.axhline(solutions, color="tab:blue", ls=":", lw=1.0,
               label=f"|S(T)| = {solutions} (sem particionar)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("z (posições retidas)")
    ax.set_ylabel("nº de localizações", color="tab:blue")
    ax.tick_params(axis="y", labelcolor="tab:blue")
    ax.grid(alpha=0.3)

    twin = ax.twinx()
    shared = pd.to_numeric(sweep["shared_algorithms"], errors="coerce")
    if shared.notna().any():
        twin.plot(sweep["z"], shared, color="tab:red", marker="s", ms=3,
                  lw=1.4, label="localizações visitadas pelos dois algoritmos")
    twin.plot(sweep["z"], sweep["shared_runs"], color="tab:orange", marker="^", ms=3,
              lw=1.2, ls="--", label="localizações visitadas por mais de uma run")
    twin.set_yscale("symlog", linthresh=1)
    twin.set_ylabel("nº de localizações compartilhadas", color="tab:red")
    twin.tick_params(axis="y", labelcolor="tab:red")

    ax.set_title(f"Resolução × sobreposição — {label}")
    handles = ax.get_lines() + twin.get_lines()
    ax.legend(
        handles,
        [h.get_label() for h in handles],
        fontsize=8,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=2,
        frameon=False,
    )
    _save(fig, folder, name)
    plt.close(fig)


def figure_distribution(entropy: list[float], label: str, folder: Path, name: str) -> None:
    import matplotlib.pyplot as plt

    values = sorted(entropy)
    n = len(values)
    zero = sum(1 for value in values if value == 0.0) / n
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.step(values, [i / n for i in range(1, n + 1)], where="post", lw=1.5)
    ax.axhline(zero, color="tab:red", ls="--", lw=1.0)
    ax.annotate(f"H = 0: {zero:.1%} das posições", xy=(0.02, zero), fontsize=9,
                color="tab:red", va="bottom")
    ax.set_xlabel("H(x_i)  [bits]")
    ax.set_ylabel("fração acumulada de posições")
    ax.set_title(f"Distribuição da entropia por posição — {label}")
    ax.grid(alpha=0.3)
    _save(fig, folder, name)
    plt.close(fig)


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------
def diagnose(args) -> pd.DataFrame:
    out = Path(args.out_root) / "reports" / "rq1_entropy"
    figures = out / "figures"
    out.mkdir(parents=True, exist_ok=True)

    inv = io_raw.inventory(args.raw_root)
    if args.all:
        targets = [(str(i), str(c)) for i, c in inv.set_index(["instance", "config"]).index.unique()]
    else:
        targets = [(args.instance, args.config)]

    summaries = []
    control_curves: dict[str, list[float]] = {}

    for instance, config in targets:
        df = io_raw.load_trajectories(instance, config, root=args.raw_root)
        n = io_raw.n_positions(instance, root=args.raw_root)
        index = solution_index(df)
        solutions = [entry["solution"] for entry in index.values()]
        tau = len(next(iter(solutions)))
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
        zs = z_grid(n, [stats[f"z_{p}"] for p in AREA_PERCENTS])
        sweep = sweep_z(index, order, zs)
        sweep.to_csv(out / f"z_sweep_{key}.csv", index=False)
        stability = ranking_stability(index, n, [z for z in zs if z <= max(zs)][:12])
        if not stability.empty:
            stability.to_csv(out / f"ranking_stability_{key}.csv", index=False)
        samples = sample_size_curves(solutions, n, seed=args.seed)
        samples.to_csv(out / f"sample_size_{key}.csv", index=False)

        if args.figs:
            figure_entropy_curve(ordered, stats, label, figures, f"entropy_curve_{key}")
            figure_tradeoff(sweep, stats, label, figures, f"tradeoff_{key}")
            figure_sample_size(samples, label, figures, f"sample_size_{key}")
            figure_distribution(entropy, label, figures, f"entropy_distribution_{key}")
        control_curves[f"MoWFLOP {label}"] = ordered

    if args.control_pmed7:
        solutions, n = load_pmed7(args.control_pmed7)
        entropy, order, stats = analyse(solutions, n, args.tie_break, args.seed)
        ordered = [entropy[i] for i in order]
        stats.update(
            {
                "instance": "pmed7",
                "config": "control",
                "tau": -1,
                "density": -1.0,
                "recordings": -1,
                "unique_solutions": len(solutions),
                "algorithms": "ACO|BRKGA|ILS",
            }
        )
        summaries.append(stats)
        pd.DataFrame({"rank": range(1, n + 1), "entropy": ordered}).to_csv(
            out / "entropy_curve_pmed7.csv", index=False
        )
        control_curves["controle pmed7 (Ochoa et al. 2021)"] = ordered
        if args.figs:
            figure_entropy_curve(ordered, stats, "pmed7 (controle)", figures, "entropy_curve_pmed7")

    if args.figs and len(control_curves) > 1:
        figure_controls(control_curves, figures, "entropy_curve_controls")

    summary = pd.DataFrame(summaries)
    front = ["instance", "config", "algorithms", "n", "tau", "density",
             "recordings", "unique_solutions"]
    summary = summary[front + [c for c in summary.columns if c not in front]]
    summary.to_csv(out / "summary.csv", index=False)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instance")
    parser.add_argument("--config")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--tie-break", choices=["index", "random"], default="index")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--raw-root")
    parser.add_argument(
        "--control-pmed7",
        nargs="?",
        const=str(io_raw.repo_root().parent / "STNs" / "pmed7"),
        help="folder with the authors' p-median traces (default ../STNs/pmed7)",
    )
    parser.add_argument("--out-root", default=str(io_raw.repo_root()))
    parser.add_argument("--figs", action="store_true", help="also render the figures")
    args = parser.parse_args(argv)

    if not args.all and not (args.instance and args.config):
        parser.error("give --instance and --config, or --all")

    summary = diagnose(args)
    with pd.option_context("display.width", 200, "display.max_columns", 40):
        print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
