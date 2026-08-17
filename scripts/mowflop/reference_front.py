"""Pareto reference set for a MoWFLOP instance.

``create .R`` needs a reference front to tag nodes with ``Position="Pareto"``,
and none exists for MoWFLOP.  We take the non-dominated set over every
objective vector logged for the instance -- both algorithms, every run, every
observer vector, every recording.

The two objectives pull in opposite directions: ``f_cost`` is minimised and
``f_power`` maximised.  It is computed once per instance and reused for every
scheme and every ``z``, which is what makes the metrics comparable across
regimes.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DEC = 6  # decimal places; must match `dec` in "create .R"
FLOAT_FMT = f"%.{DEC}f"


def pareto_front(
    df: pd.DataFrame, cost: str = "f_cost", power: str = "f_power"
) -> pd.DataFrame:
    """Non-dominated points, minimising ``cost`` and maximising ``power``."""
    points = df[[cost, power]].drop_duplicates()
    points = points.sort_values([cost, power], ascending=[True, False], ignore_index=True)
    keep = []
    best_power = float("-inf")
    for c, p in points.itertuples(index=False):
        if p > best_power:
            keep.append((c, p))
            best_power = p
    return pd.DataFrame(keep, columns=[cost, power])


def front_keys(front: pd.DataFrame, cost: str = "f_cost", power: str = "f_power") -> set[str]:
    """String keys of the front, matching how ``create .R`` compares values."""
    return {
        f"{FLOAT_FMT % c}_{FLOAT_FMT % p}"
        for c, p in front[[cost, power]].itertuples(index=False)
    }


def write_front(path: str | Path, front: pd.DataFrame) -> Path:
    """Write in the layout of the repo's ``pf/*_ref.txt``: TSV, no header."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    front.to_csv(path, sep="\t", header=False, index=False, float_format=FLOAT_FMT)
    return path
