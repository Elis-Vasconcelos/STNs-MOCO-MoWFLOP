"""CLI: turn the raw campaign logs into input for ``create .R``.

Examples::

    # Shannon entropy partitioning at the authors' area criterion
    python -m mowflop.partition --instance ns101 --config p100_i50 \
        --scheme entropy --percent 60

    # the unpartitioned baseline, same pipeline
    python -m mowflop.partition --instance ns101 --config p100_i50 --scheme raw

    # everything that has both algorithms logged
    python -m mowflop.partition --all --scheme entropy --percent 60

Run it from ``scripts/`` (or with ``PYTHONPATH=scripts``) so that ``mowflop`` is
importable, using the repo's virtualenv interpreter.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import entropy as entropy_mod
from . import io_raw
from .emit import emit
from .reference_front import pareto_front
from .schemes import build_scheme


def default_tag(scheme: str, percent: float | None, z: int | None) -> str:
    if scheme == "raw":
        return "raw"
    if z is not None:
        return f"z{z}"
    return f"x{int(percent)}"


def unique_solutions(df) -> list[entropy_mod.Solution]:
    """``S(T)``: the *unique* solutions of every trajectory, as the paper asks."""
    return [entropy_mod.from_index_list(text) for text in df["occupied"].unique()]


def run_one(args, instance: str, config: str) -> dict:
    df = io_raw.load_trajectories(instance, config, root=args.raw_root)
    n = io_raw.n_positions(instance, root=args.raw_root)
    solutions = unique_solutions(df)
    scheme = build_scheme(
        args.scheme,
        solutions,
        n,
        percent=None if args.scheme == "raw" else args.percent,
        z=None if args.scheme == "raw" else args.z,
        tie_break=args.tie_break,
        seed=args.seed,
    )
    tag = args.tag or default_tag(args.scheme, args.percent, args.z)
    front = pareto_front(df)
    summary = emit(
        df,
        scheme,
        instance=instance,
        config=config,
        tag=tag,
        out_root=args.out_root,
        front=front,
    )
    summary["algorithms"] = sorted(df["algorithm"].unique().tolist())
    summary["unique_solutions"] = len(solutions)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instance")
    parser.add_argument("--config")
    parser.add_argument(
        "--all",
        action="store_true",
        help="process every (instance, config) that has at least one log",
    )
    parser.add_argument(
        "--both-algorithms",
        action="store_true",
        help="with --all, keep only pairs that already have MOEA/D and NSGA-II",
    )
    parser.add_argument("--scheme", choices=["entropy", "raw"], default="entropy")
    parser.add_argument(
        "--percent",
        type=float,
        default=60.0,
        help="X%% partitioning of the area criterion (0 means no partitioning)",
    )
    parser.add_argument("--z", type=int, help="fixed number of retained positions")
    parser.add_argument("--tie-break", choices=["index", "random"], default="index")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--tag", help="file name tag; default x<percent>/z<z>/raw")
    parser.add_argument("--raw-root", help="campaign root; default $MOWFLOP_RAW")
    parser.add_argument(
        "--out-root",
        default=str(io_raw.repo_root()),
        help="where data/, pf/ and locations/ are written",
    )
    args = parser.parse_args(argv)

    if args.z is not None:
        args.percent = None

    targets: list[tuple[str, str]]
    if args.all:
        inv = io_raw.inventory(args.raw_root)
        if args.both_algorithms:
            counts = inv.groupby(["instance", "config"])["algorithm"].nunique()
            pairs = counts[counts >= 2].index
        else:
            pairs = inv.set_index(["instance", "config"]).index.unique()
        targets = [(str(i), str(c)) for i, c in pairs]
    else:
        if not args.instance or not args.config:
            parser.error("give --instance and --config, or --all")
        targets = [(args.instance, args.config)]

    if not targets:
        print("nothing to do: no (instance, config) matched", file=sys.stderr)
        return 1

    summaries = []
    for instance, config in targets:
        summary = run_one(args, instance, config)
        summaries.append(summary)
        print(
            f"{instance}/{config} [{summary['scheme']}"
            + (f" z={summary['z']}" if "z" in summary else "")
            + f"] {summary['recordings']} recordings, "
            f"{summary['solutions']} solutions -> {summary['locations']} locations, "
            f"front={summary['front_size']}"
        )
    out = Path(args.out_root) / "reports" / "partition_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(f"summary -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
