"""Writing the partitioned trajectories in the format ``create .R`` reads.

Target format (``data/n16_m2/MOEAD/MOEAD_rmnk_-0.4_2_16_1_0_post.txt``)::

    f1 f2 Solution1 Solution2 Run Gen Vector Weight1 Weight2

Column *order* matters: the R script does a positional ``select(df, f1:Vector)``
and fixes nine column types in ``bdf_col_types``.  File *name* matters too:
``create .R`` splits it on ``_`` and reads the number of objectives from the
fourth field, then builds the reference-front name out of fields 2 to 7 -- hence
``MOEAD_mowflop_ns101_2_x60_p100i50_0_post.txt`` and the matching
``pf/mowflop/mowflop_ns101_2_x60_p100i50_0_ref.txt``.  No field may contain an
underscore, which is why the config tag is written ``p100i50``.

Two things need care beyond the column mapping:

*Canonical objective per location.*  ``create .R`` groups nodes by
``(f1, f2, Solution1, Vector)``.  With a partitioned space a location carries
many objective vectors, so that grouping would silently split one location into
several nodes and undo the partitioning.  Every location therefore gets a single
representative objective, chosen among the solutions that actually visited it --
the multi-objective reading of the paper's ``f(s_z) := min{f(s')}``: membership
in the reference front first, then lexicographic ``(f_cost, -f_power)``.  This
also makes the R ``Position="Pareto"`` tag coincide with the metric of S8.

*Self-loop on the last recording.*  ``Solution2`` is the next location of the
same ``(Run, Vector)`` trajectory; the last recording points at itself.  That is
the convention of the original rho-mnk data and it keeps every edge endpoint
present in ``nodes`` (otherwise ``graph_from_data_frame`` errors with "Some
vertex names in `d` are not listed in `vertices`").
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import entropy as entropy_mod
from .io_raw import ALGO_LABELS
from .reference_front import DEC, FLOAT_FMT, front_keys, pareto_front, write_front

OUTPUT_COLUMNS = [
    "f1",
    "f2",
    "Solution1",
    "Solution2",
    "Run",
    "Gen",
    "Vector",
    "Weight1",
    "Weight2",
]


def config_tag(config: str) -> str:
    """``p100_i50`` -> ``p100i50``: file name fields cannot hold underscores."""
    return config.replace("_", "")


def output_name(algo_label: str, instance: str, tag: str, cfg_tag: str) -> str:
    for field in (algo_label, instance, tag, cfg_tag):
        if "_" in field:
            raise ValueError(f"file name field cannot contain '_': {field!r}")
    return f"{algo_label}_mowflop_{instance}_2_{tag}_{cfg_tag}_0_post.txt"


def front_name(instance: str, tag: str, cfg_tag: str) -> str:
    return f"mowflop_{instance}_2_{tag}_{cfg_tag}_0_ref.txt"


def assign_locations(df: pd.DataFrame, scheme) -> tuple[pd.DataFrame, dict, dict]:
    """Add ``Solution1`` (location id) and the projection, memoised per layout."""
    distinct = df["occupied"].drop_duplicates()
    ids, projections = {}, {}
    for text in distinct:
        solution = entropy_mod.from_index_list(text)
        projection = scheme.project(solution)
        ids[text] = scheme.assign(solution)
        projections[text] = projection
    out = df.copy()
    out["Solution1"] = out["occupied"].map(ids)
    return out, projections, ids


def canonical_objectives(df: pd.DataFrame, front: pd.DataFrame) -> pd.DataFrame:
    """One representative objective vector per location.

    Ranking key: in the reference front first, then ``f_cost`` ascending and
    ``f_power`` descending.  The representative is always a solution that was
    really visited, never a synthetic ideal point.
    """
    keys = front_keys(front)
    candidates = df[["Solution1", "f_cost", "f_power"]].drop_duplicates()
    obj_key = (
        candidates["f_cost"].map(lambda v: FLOAT_FMT % v)
        + "_"
        + candidates["f_power"].map(lambda v: FLOAT_FMT % v)
    )
    candidates = candidates.assign(not_in_front=~obj_key.isin(keys).to_numpy())
    candidates = candidates.sort_values(
        ["Solution1", "not_in_front", "f_cost", "f_power"],
        ascending=[True, True, True, False],
        ignore_index=True,
    )
    best = candidates.drop_duplicates("Solution1", keep="first")
    best = best.assign(in_front=~best["not_in_front"].to_numpy())
    return best.rename(columns={"f_cost": "f1", "f_power": "f2"})[
        ["Solution1", "f1", "f2", "in_front"]
    ]


def build_table(df: pd.DataFrame, objectives: pd.DataFrame) -> pd.DataFrame:
    """Map the raw log onto the nine columns, adding the ``Solution2`` lag."""
    out = df.merge(objectives, on="Solution1", how="left", validate="many_to_one")
    out["Run"] = out["run_id"].astype("int64") + 1
    out["Gen"] = out["iteration"].astype("int64")
    out["Vector"] = "V" + (out["vector_id"].astype("int64") + 1).astype(str)
    out["Weight1"] = out["weight1"].map(lambda v: FLOAT_FMT % v)
    out["Weight2"] = out["weight2"].map(lambda v: FLOAT_FMT % v)
    out = out.sort_values(["Run", "vector_id", "Gen"], ignore_index=True)
    nxt = out.groupby(["Run", "vector_id"], sort=False)["Solution1"].shift(-1)
    out["Solution2"] = nxt.fillna(out["Solution1"])  # self-loop on the last one
    return out[OUTPUT_COLUMNS]


def check_vectors(table: pd.DataFrame) -> None:
    """``create .R`` derives the vector count from distinct (Vector, weights).

    If a vector ever changed its weights that count would exceed the number of
    pivot columns and the script's column arithmetic (``i <- m + 2``) would
    silently read the wrong columns.
    """
    triples = table[["Vector", "Weight1", "Weight2"]].drop_duplicates()
    if len(triples) != table["Vector"].nunique():
        raise ValueError(
            "a Vector appears with more than one weight pair; "
            "create .R would miscount the vector columns"
        )


def write_table(path: str | Path, table: pd.DataFrame) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, sep=" ", index=False, float_format=FLOAT_FMT)
    return path


def locations_table(
    df: pd.DataFrame,
    projections: dict[str, frozenset],
    ids: dict[str, str],
    objectives: pd.DataFrame,
) -> pd.DataFrame:
    """Side table: location id -> retained positions, size, representative."""
    per_id: dict[str, frozenset] = {}
    for text, location in ids.items():
        per_id.setdefault(location, projections[text])
    counts = (
        df.groupby("Solution1")
        .agg(
            solutions=("occupied", "nunique"),
            recordings=("occupied", "size"),
            algorithms=("algorithm", lambda s: "|".join(sorted(set(s)))),
        )
        .reset_index()
    )
    counts["kept_positions"] = counts["Solution1"].map(lambda k: len(per_id[k]))
    counts["positions"] = counts["Solution1"].map(
        lambda k: " ".join(str(p) for p in sorted(per_id[k]))
    )
    return counts.merge(objectives, on="Solution1", how="left").sort_values(
        "recordings", ascending=False, ignore_index=True
    )


def emit(
    df: pd.DataFrame,
    scheme,
    instance: str,
    config: str,
    tag: str,
    out_root: str | Path,
    front: pd.DataFrame | None = None,
) -> dict:
    """Full emission for one (instance, config): data files, front, side table."""
    out_root = Path(out_root)
    cfg = config_tag(config)
    if front is None:
        front = pareto_front(df)

    located, projections, ids = assign_locations(df, scheme)
    objectives = canonical_objectives(located, front)

    data_dir = out_root / "data" / f"mowflop_{tag}"
    written = []
    for algorithm, group in located.groupby("algorithm", sort=True):
        label = ALGO_LABELS.get(str(algorithm), str(algorithm).upper())
        table = build_table(group, objectives)
        check_vectors(table)
        path = write_table(
            data_dir / label / output_name(label, instance, tag, cfg), table
        )
        written.append({"algorithm": label, "path": str(path), "rows": len(table)})

    front_path = write_front(
        out_root / "pf" / "mowflop" / front_name(instance, tag, cfg), front
    )
    loc_path = out_root / "locations" / f"mowflop_{tag}" / f"{instance}_{cfg}_locations.csv"
    loc_path.parent.mkdir(parents=True, exist_ok=True)
    locations_table(located, projections, ids, objectives).to_csv(
        loc_path, index=False, float_format=FLOAT_FMT
    )

    return {
        "instance": instance,
        "config": config,
        "tag": tag,
        "files": written,
        "front": str(front_path),
        "front_size": len(front),
        "locations_table": str(loc_path),
        "locations": located["Solution1"].nunique(),
        "solutions": located["occupied"].nunique(),
        "recordings": len(located),
        "decimals": DEC,
        **scheme.describe(),
    }
