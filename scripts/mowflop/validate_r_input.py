"""Check that an emitted dataset is what ``create .R`` expects, before running R.

The R script fails late and obscurely when its assumptions are broken (a missing
reference front stops at ``read.table``; an edge endpoint absent from ``nodes``
stops at ``graph_from_data_frame`` with "Some vertex names in `d` are not listed
in `vertices`").  This replays its critical steps in pandas so the problems
surface here instead:

* the nine column names, in order, and nine fields on every row;
* ``nGen <- max(df$Gen) + 1`` / ``nRun <- max(df$Run)`` keep every row;
* ``group_by(f1, f2, Solution1, Vector)`` does not split a location into
  several nodes -- the trap that would quietly undo the partitioning;
* every edge endpoint from ``filter(Gen < nGen)`` exists in ``nodes``;
* the reference front sits exactly at the path the R script computes from the
  file name, and its values match node objectives as strings at ``dec = 6``;
* one weight pair per vector, so the script's column arithmetic holds.

Usage::

    python -m mowflop.validate_r_input --data-dir ../data/mowflop_x60
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .emit import OUTPUT_COLUMNS
from .reference_front import DEC, FLOAT_FMT

FLOAT_COLUMNS = ("f1", "f2")


def front_path_as_r_computes(data_file: Path, pf_root: Path) -> Path:
    """Mirror of ``create .R`` lines 59-63."""
    fields = data_file.name.split("_")
    if len(fields) < 8:
        raise ValueError(f"file name has too few '_' fields for create .R: {data_file.name}")
    return pf_root / ("_".join(fields[1:7]) + "_ref.txt")


def check_file(data_file: Path, pf_root: Path) -> dict:
    problems: list[str] = []

    with open(data_file, "r", encoding="utf-8") as handle:
        header = handle.readline().split()
    if header != OUTPUT_COLUMNS:
        problems.append(f"header is {header}, expected {OUTPUT_COLUMNS}")

    df = pd.read_csv(data_file, sep=" ")
    if df.isna().any().any():
        problems.append("file has missing values; read.table would misalign columns")

    # create .R: nGen <- max(df$Gen) + 1 ; nRun <- max(df$Run)
    n_gen, n_run = int(df["Gen"].max()) + 1, int(df["Run"].max())
    kept = df[(df["Gen"] <= n_gen) & (df["Run"] <= n_run)]
    if len(kept) != len(df):
        problems.append(f"{len(df) - len(kept)} rows dropped by the Gen/Run filter")
    if int(df["Run"].min()) < 1:
        problems.append("Run is not one-based; create .R would drop run 0")

    # the group_by(f1, f2, Solution1, Vector) trap
    per_location = df.groupby("Solution1")[["f1", "f2"]].nunique()
    fragmented = int(((per_location > 1).any(axis=1)).sum())
    if fragmented:
        problems.append(
            f"{fragmented} locations carry more than one objective vector and "
            "would be split into several nodes by create .R"
        )

    # graph_from_data_frame(edges, vertices = nodes)
    nodes = set(df["Solution1"])
    edges = df[df["Gen"] < n_gen]
    dangling = (set(edges["Solution1"]) | set(edges["Solution2"])) - nodes
    if dangling:
        problems.append(f"{len(dangling)} edge endpoints are missing from nodes")

    # one weight pair per vector, or the vector-column arithmetic breaks
    triples = df[["Vector", "Weight1", "Weight2"]].drop_duplicates()
    n_vec = df["Vector"].nunique()
    if len(triples) != n_vec:
        problems.append("a Vector appears with more than one weight pair")

    # reference front, at the exact path create .R builds from the file name
    front_file = front_path_as_r_computes(data_file, pf_root)
    pareto_nodes = -1
    if not front_file.is_file():
        problems.append(f"reference front not found where create .R looks: {front_file}")
    else:
        front = pd.read_csv(front_file, sep="\t", header=None, names=["f1", "f2"])
        keys = {
            f"{FLOAT_FMT % a}_{FLOAT_FMT % b}"
            for a, b in front.itertuples(index=False)
        }
        node_keys = (
            df.drop_duplicates("Solution1")
            .apply(lambda r: f"{FLOAT_FMT % r['f1']}_{FLOAT_FMT % r['f2']}", axis=1)
        )
        pareto_nodes = int(node_keys.isin(keys).sum())
        if pareto_nodes == 0:
            problems.append("no node matches the reference front; Position='Pareto' would be empty")
        if pareto_nodes == len(node_keys):
            problems.append("every node matches the reference front, which is the overflow bug's symptom")

    return {
        "file": data_file.name,
        "rows": len(df),
        "nodes": len(nodes),
        "edges": len(edges),
        "vectors": n_vec,
        "runs": int(df["Run"].nunique()),
        "nGen": n_gen,
        "pareto_nodes": pareto_nodes,
        "front": front_file.name,
        "decimals": DEC,
        "problems": problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", required=True, help="e.g. data/mowflop_x60")
    parser.add_argument("--pf-root", help="default: <repo>/pf/mowflop")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir).resolve()
    pf_root = Path(args.pf_root) if args.pf_root else data_dir.parents[1] / "pf" / "mowflop"

    files = sorted(data_dir.glob("*/*.txt"))
    if not files:
        print(f"no data files under {data_dir}")
        return 1

    failed = 0
    for data_file in files:
        result = check_file(data_file, pf_root)
        status = "OK  " if not result["problems"] else "FAIL"
        print(
            f"{status} {result['file']}: {result['rows']} rows, {result['nodes']} nodes, "
            f"{result['edges']} edges, {result['vectors']} vectors, {result['runs']} runs, "
            f"nGen={result['nGen']}, nós no front={result['pareto_nodes']}"
        )
        for problem in result["problems"]:
            print(f"       - {problem}")
        failed += bool(result["problems"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
