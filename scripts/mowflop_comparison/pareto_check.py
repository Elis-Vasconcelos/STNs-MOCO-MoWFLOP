"""Pareto-front correctness check: this work's wind-corrected runs vs CEC 2025.

Primary output: one figure per (instance, algorithm), a small-multiple grid
of the RUN-MATCHED comparisons -- panel k overlays this work's run k Pareto
front against CEC's matching run, both using the *identical* (angle, wind)
draw. This is the visual "do our results match CEC" check Prof. Islame
asked for, generalising the single-run proof in `plot_corrected_comparison.py`
(now superseded -- see README.md) to every matched run of all 10 instances.

Why run-matched and not pooled: wind is drawn per run and power scales
~wind^3, so pooling unequal run sets (10 runs here, 20 at CEC) compares
wind distributions, not algorithm behaviour. Matched runs share the wind,
so the achievable frontier is the same and any gap is a real difference.

Objective convention (STN_MoWFLOP/README.md, CLAUDE.md): construction cost
is minimised, power output is maximised, both reported as positive numbers.
Both objective values are columns of each run's final-population dump
`<inst>_<algo>_1000000.txt` (col 1 = cost, col 2 = power).

Data sources and naming conventions: see README.md in this directory.

Usage:
    <venv>/bin/python pareto_check.py                 # all 10 instances, both algos
    <venv>/bin/python pareto_check.py --instances 178 # subset
    <venv>/bin/python pareto_check.py --pool p10_i50  # which STN p-config to read
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]          # STNs-MOCO-MoWFLOP/
TCC_ROOT = REPO_ROOT.parent                              # TCC/
OUR_ROOT = TCC_ROOT / "supercomputer_backup" / "raw_results" / "meta_heuristics_stn_windcorrected"
CEC_ROOT = REPO_ROOT / "raw_results" / "wflopcec26"
OUT_DIR = REPO_ROOT / "plots" / "pareto_check"
WIND_MAP = TCC_ROOT / "STN_MoWFLOP" / "source_code" / "meta_heuristics" / "wind_corrected" / "cec_wind_map.csv"

# Cazzaro & Pisinger "New Sites" instances. Bare integers here; the STN_MoWFLOP
# tree and the vendored CEC tree prefix them "ns" at the directory level (see
# README.md -- the prefix disambiguates from the 300 synthetic instances/site/<n>).
INSTANCES = ["41", "48", "101", "178", "192", "202", "203", "440", "465", "488"]
ALGOS = ["moead", "nsga2"]
ALGO_LABEL = {"moead": "MOEA/D", "nsga2": "NSGA-II"}
N_MATCHED_RUNS = 10   # this work's STN campaign: run_id 0..9

C_OURS = "#1f4e9c"    # this work
C_CEC = "#c8781a"     # CEC 2025


def set_style() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman", "Nimbus Roman", "serif"],
        "mathtext.fontset": "dejavuserif",
        "axes.linewidth": 0.6,
        "axes.titlesize": 9,
        "axes.labelsize": 10,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "legend.fontsize": 7.5,
        "legend.frameon": False,
        "figure.dpi": 140,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })


def load_population(path: Path) -> np.ndarray:
    """(N, 2) array of [cost, power] from a final-population dump."""
    df = pd.read_csv(path, sep=r"\s+", header=None, names=["cost", "power"])
    return df[["cost", "power"]].to_numpy(dtype=float)


def nd_mask(F: np.ndarray) -> np.ndarray:
    """Non-dominated mask for (cost minimised, power maximised). O(n^2)."""
    n = len(F)
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        dominated = (
            (F[:, 0] <= F[i, 0]) & (F[:, 1] >= F[i, 1])
            & ((F[:, 0] < F[i, 0]) | (F[:, 1] > F[i, 1]))
        )
        if dominated.any():
            keep[i] = False
    return keep


def front_of(path: Path) -> np.ndarray:
    """Non-dominated front of one run's final population, sorted by cost."""
    if not path.exists():
        return np.empty((0, 2))
    F = load_population(path)
    nd = F[nd_mask(F)]
    return nd[np.argsort(nd[:, 0])]


def load_wind_map() -> pd.DataFrame:
    df = pd.read_csv(WIND_MAP, dtype={"instance": str})
    return df.set_index(["instance", "algo", "run_id"])


def set_coverage(A: np.ndarray, B: np.ndarray) -> float:
    """C(A, B): fraction of front B weakly dominated by >=1 point of front A
    (Zitzler & Thiele, 1998). Not symmetric; C(A,B) + C(B,A) != 1 in general."""
    if len(A) == 0 or len(B) == 0:
        return float("nan")
    dom = np.zeros(len(B), dtype=bool)
    for a in A:
        dom |= (a[0] <= B[:, 0]) & (a[1] >= B[:, 1]) & ((a[0] < B[:, 0]) | (a[1] > B[:, 1]))
    return float(dom.mean())


def our_run_file(algo: str, inst: str, pool: str, run_id: int) -> Path:
    return OUR_ROOT / algo / f"ns{inst}" / pool / str(run_id) / f"ns{inst}_{algo}_1000000.txt"


def cec_run_file(algo: str, inst: str, run_id: int) -> Path:
    # CEC's runner numbers run directories 1..20 (1-based); this work's STN
    # runner numbers them 0..9 (0-based). cec_wind_map.csv is 0-based to match
    # this work, so wind-map run_id k corresponds to CEC directory k+1 -- the
    # same wind scenario, differing only in the runners' indexing base.
    return CEC_ROOT / algo / f"ns{inst}" / str(run_id + 1) / f"{inst}_{algo}_1000000.txt"


def rel_pct(ours: float, cec: float) -> float:
    return 100.0 * (ours - cec) / cec if cec else float("nan")


def plot_instance_algo(inst: str, algo: str, pool: str, wind: pd.DataFrame,
                       rows: list[dict]) -> None:
    ncol = 5
    nrow = -(-N_MATCHED_RUNS // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.6 * ncol, 3.3 * nrow), squeeze=False)

    for k in range(N_MATCHED_RUNS):
        ax = axes[k // ncol][k % ncol]
        ours = front_of(our_run_file(algo, inst, pool, k))
        cec = front_of(cec_run_file(algo, inst, k))

        try:
            w = wind.loc[(inst, algo, k)]
            wtxt = fr"{w['angle']:.0f}$^\circ$, {w['wind']:.0f} m/s"
        except KeyError:
            wtxt = "wind unknown"

        if len(cec):
            ax.plot(cec[:, 0], cec[:, 1], marker="^", ms=3.5, mew=0, lw=1.0,
                    c=C_CEC, label=fr"CEC 2025   $|\mathrm{{ND}}|={len(cec)}$", zorder=2)
        if len(ours):
            ax.plot(ours[:, 0], ours[:, 1], marker="o", ms=3, mew=0, lw=1.0,
                    c=C_OURS, label=fr"This work   $|\mathrm{{ND}}|={len(ours)}$", zorder=3)

        c_cec_ours = set_coverage(cec, ours)
        c_ours_cec = set_coverage(ours, cec)
        ax.set_title(
            f"Run {k}   ·   {wtxt}\n"
            fr"$\mathcal{{C}}$(CEC, ours) $= {c_cec_ours:.2f}$   "
            fr"$\mathcal{{C}}$(ours, CEC) $= {c_ours_cec:.2f}$"
        )
        ax.margins(0.08)
        ax.grid(True, lw=0.3, alpha=0.4)
        ax.legend(loc="lower right", handlelength=1.4)
        ax.xaxis.get_offset_text().set_fontsize(6.5)
        ax.yaxis.get_offset_text().set_fontsize(6.5)

        rows.append(dict(
            instance=f"ns{inst}", algo=algo, pool=pool, run=k, wind=wtxt.replace("$^\\circ$", "deg"),
            our_nd=len(ours), cec_nd=len(cec),
            our_cost_min=_safe(ours, 0, np.min), cec_cost_min=_safe(cec, 0, np.min),
            our_power_max=_safe(ours, 1, np.max), cec_power_max=_safe(cec, 1, np.max),
            d_cost_min_abs=_safe(ours, 0, np.min) - _safe(cec, 0, np.min),
            d_cost_min_pct=rel_pct(_safe(ours, 0, np.min), _safe(cec, 0, np.min)),
            d_power_max_abs=_safe(ours, 1, np.max) - _safe(cec, 1, np.max),
            d_power_max_pct=rel_pct(_safe(ours, 1, np.max), _safe(cec, 1, np.max)),
            C_cec_ours=c_cec_ours, C_ours_cec=c_ours_cec,
        ))

    for j in range(N_MATCHED_RUNS, nrow * ncol):
        axes[j // ncol][j % ncol].axis("off")

    fig.supylabel(r"Power output  $f_{\mathrm{power}}$  (maximised)", fontsize=10)
    fig.suptitle(
        f"Run-matched Pareto fronts — this work vs. CEC 2025 — ns{inst}, {ALGO_LABEL[algo]}",
        fontsize=12, y=0.995,
    )
    fig.text(0.5, 0.055, r"Construction cost  $f_{\mathrm{cost}}$  (minimised)",
             ha="center", fontsize=10)
    fig.text(
        0.5, 0.012,
        r"$\mathcal{C}(X, Y)$: fraction of front $Y$ weakly dominated by front $X$ "
        r"(Zitzler & Thiele, 1998).  Each front is the per-run non-dominated set of "
        r"the final population after $10^6$ evaluations.",
        ha="center", fontsize=7.5, style="italic",
    )
    fig.tight_layout(rect=(0.015, 0.085, 1, 0.955))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"pareto_ns{inst}_{algo}_{pool}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"saved {out}")


def _safe(F: np.ndarray, col: int, fn) -> float:
    return float(fn(F[:, col])) if len(F) else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--instances", nargs="+", default=INSTANCES)
    ap.add_argument("--pool", default="p100_i50",
                    help="STN p-config directory to read (p10_i50 / p50_i50 / p100_i50)")
    args = ap.parse_args()

    set_style()
    wind = load_wind_map()
    rows: list[dict] = []
    for inst in args.instances:
        for algo in ALGOS:
            plot_instance_algo(inst, algo, args.pool, wind, rows)

    summ = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv = OUT_DIR / f"pareto_check_summary_{args.pool}.csv"
    summ.to_csv(csv, index=False)
    print(f"\nsaved {csv}\n")

    agg = (summ.groupby(["instance", "algo"])
           .agg(runs=("run", "count"),
                mean_dcost_pct=("d_cost_min_pct", "mean"),
                mean_dpower_pct=("d_power_max_pct", "mean"),
                mean_C_cec_ours=("C_cec_ours", "mean"),
                mean_C_ours_cec=("C_ours_cec", "mean"))
           .reset_index())
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
