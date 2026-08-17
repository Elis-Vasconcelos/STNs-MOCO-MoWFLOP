"""Reading of the raw campaign logs.

The campaign lives in ``raw_results/meta_heuristics_stn`` inside this
repository; ``$MOWFLOP_RAW`` overrides it.  Directory layout produced by the
C++ campaign::

    <raw_root>/<algorithm>/<instance>/<config>/<run>/<instance>_<algorithm>_stn.csv
    <raw_root>/candidates/<instance>_candidates.csv

``config`` is ``p<P>_i<k>``: P observer vectors, one recording every k
generations.  Each ``*_stn.csv`` holds a single run and has the columns

    algorithm,instance,run_id,vector_id,generation,iteration,
    f_cost,f_power,weight1,weight2,occupied

``occupied`` is the space separated list of global candidate indices holding a
turbine -- one entry per mobile turbine, already sorted.  The candidate index
is the row order of ``<instance>_candidates.csv``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

STN_COLUMNS = [
    "algorithm",
    "instance",
    "run_id",
    "vector_id",
    "generation",
    "iteration",
    "f_cost",
    "f_power",
    "weight1",
    "weight2",
    "occupied",
]

# The R pipeline names the algorithm folders MOEAD/NSGA2; the C++ campaign
# writes them lowercase.
ALGO_LABELS = {"moead": "MOEAD", "nsga2": "NSGA2"}


def repo_root() -> Path:
    """Root of the STNs-MOCO-MoWFLOP checkout."""
    return Path(__file__).resolve().parents[2]


def raw_root(root: str | os.PathLike | None = None) -> Path:
    """Locate the campaign logs: ``raw_results/meta_heuristics_stn`` in the repo.

    An explicit argument or ``$MOWFLOP_RAW`` overrides it.
    """
    if root is not None:
        return Path(root).resolve()
    env = os.environ.get("MOWFLOP_RAW")
    if env:
        return Path(env).resolve()
    path = repo_root() / "raw_results" / "meta_heuristics_stn"
    if not path.is_dir():
        raise FileNotFoundError(
            f"campaign logs not found at {path}; set MOWFLOP_RAW or pass root explicitly"
        )
    return path


def discover(root: str | os.PathLike | None = None) -> pd.DataFrame:
    """Inventory of every ``*_stn.csv`` available, one row per run."""
    base = raw_root(root)
    rows = []
    for path in sorted(base.glob("*/*/*/*/*_stn.csv")):
        algorithm, instance, config, run = path.relative_to(base).parts[:4]
        rows.append(
            {
                "algorithm": algorithm,
                "instance": instance,
                "config": config,
                "run": run,
                "path": str(path),
            }
        )
    return pd.DataFrame(rows, columns=["algorithm", "instance", "config", "run", "path"])


def inventory(root: str | os.PathLike | None = None) -> pd.DataFrame:
    """Runs available per (instance, config, algorithm), for progress reports."""
    found = discover(root)
    if found.empty:
        return found
    return (
        found.groupby(["instance", "config", "algorithm"], as_index=False)
        .agg(runs=("run", "nunique"))
        .sort_values(["instance", "config", "algorithm"], ignore_index=True)
    )


def load_trajectories(
    instance: str,
    config: str,
    algorithms: list[str] | None = None,
    root: str | os.PathLike | None = None,
) -> pd.DataFrame:
    """All recordings of one (instance, config), across algorithms and runs."""
    found = discover(root)
    if found.empty:
        raise FileNotFoundError("no *_stn.csv files under the campaign root")
    sel = found[(found["instance"] == instance) & (found["config"] == config)]
    if algorithms is not None:
        sel = sel[sel["algorithm"].isin(algorithms)]
    if sel.empty:
        raise FileNotFoundError(f"no logs for instance={instance} config={config}")

    frames = [
        pd.read_csv(
            path,
            dtype={
                "algorithm": "string",
                "instance": "string",
                "run_id": "int32",
                "vector_id": "int32",
                "generation": "int64",
                "iteration": "int32",
                "f_cost": "float64",
                "f_power": "float64",
                "weight1": "float64",
                "weight2": "float64",
                "occupied": "string",
            },
        )
        for path in sel["path"]
    ]
    df = pd.concat(frames, ignore_index=True)
    missing = set(STN_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"unexpected log format, missing columns: {sorted(missing)}")
    return df[STN_COLUMNS]


def load_candidates(
    instance: str, root: str | os.PathLike | None = None
) -> pd.DataFrame:
    """Decode table mapping global candidate index to zone and coordinates."""
    path = raw_root(root) / "candidates" / f"{instance}_candidates.csv"
    df = pd.read_csv(path)
    expected = ["global_index", "zone", "zone_index", "x", "y"]
    if list(df.columns) != expected:
        raise ValueError(f"unexpected candidate format in {path}: {list(df.columns)}")
    if not (df["global_index"].to_numpy() == range(len(df))).all():
        raise ValueError(f"global_index is not row order in {path}")
    return df


def n_positions(instance: str, root: str | os.PathLike | None = None) -> int:
    """Number of candidate positions, i.e. the length of the binary string."""
    path = raw_root(root) / "candidates" / f"{instance}_candidates.csv"
    with open(path, "r", encoding="utf-8") as handle:
        return sum(1 for _ in handle) - 1
