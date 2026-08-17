"""Interchangeable partitioning schemes.

A scheme is anything that maps a solution to a location id.  Keeping this the
single point of variation is what makes the comparison fair: every scheme
downstream produces the same file format, so the R pipeline is byte-identical
across schemes and any metric difference comes from the partitioning alone.

Implemented here: ``entropy`` (Ochoa, Malan & Blum 2021) and ``raw`` (no
partitioning, Ochoa et al. 2023).  The occupancy-signature scheme and the
Hamming variants slot in by implementing the same two methods.
"""

from __future__ import annotations

from hashlib import blake2b

from . import entropy as entropy_mod
from .entropy import Solution

RAW_PREFIX = "R"


class RawScheme:
    """No partitioning: one location per distinct solution (the identity)."""

    name = "raw"

    def assign(self, solution: Solution) -> str:
        key = ",".join(str(position) for position in sorted(solution))
        return f"{RAW_PREFIX}{blake2b(key.encode('utf-8'), digest_size=8).hexdigest()}"

    def project(self, solution: Solution) -> Solution:
        return solution

    def describe(self) -> dict:
        return {"scheme": self.name}


class EntropyScheme:
    """Shannon-entropy partitioning; thin adapter over :class:`Partition`."""

    name = "entropy"

    def __init__(self, partition: entropy_mod.Partition) -> None:
        self.partition = partition

    @classmethod
    def build(
        cls,
        solutions: list[Solution],
        n: int,
        percent: float | None = None,
        z: int | None = None,
        tie_break: str = "index",
        seed: int | None = None,
    ) -> "EntropyScheme":
        return cls(
            entropy_mod.build_partition(
                solutions, n, percent=percent, z=z, tie_break=tie_break, seed=seed
            )
        )

    def assign(self, solution: Solution) -> str:
        return self.partition.assign(solution)

    def project(self, solution: Solution) -> Solution:
        return self.partition.project(solution)

    def describe(self) -> dict:
        return self.partition.describe()


def build_scheme(
    name: str,
    solutions: list[Solution],
    n: int,
    percent: float | None = None,
    z: int | None = None,
    tie_break: str = "index",
    seed: int | None = None,
):
    if name == "raw":
        return RawScheme()
    if name == "entropy":
        return EntropyScheme.build(
            solutions, n, percent=percent, z=z, tie_break=tie_break, seed=seed
        )
    raise ValueError(f"unknown scheme: {name!r}")
