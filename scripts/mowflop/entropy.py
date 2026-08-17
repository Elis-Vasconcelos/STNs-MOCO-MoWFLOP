"""Shannon-entropy search space partitioning (Ochoa, Malan & Blum 2021, S5.4).

The scheme, verbatim from the paper:

1. ``T`` is a set of search trajectories for the same instance, each one
   possibly produced by a different algorithm.  ``S(T)`` is the set of *unique*
   solutions contained in them.
2. From ``S(T)``, estimate ``p(x_i = d)`` for every position ``i`` and compute
   the Shannon entropy ``H(x_i) = -sum_d p log2 p``.  The domain is binary
   here, so ``H <= 1`` bit.
3. Rank the positions by non-increasing entropy into a list ``L``.  The paper
   breaks ties at random (see its Example 1).
4. Keep the first ``z`` positions, ``L_z``.  The location of a solution ``s`` is
   its projection ``s_z`` onto ``L_z``; ``s`` and ``s'`` share a location iff
   ``s_z == s'_z``.
5. The objective value of a location is the best objective among the solutions
   that fall in it: ``f(s_z) := min{f(s') : s' in S(T), s'_z = s_z}``.
6. ``z`` follows the *area criterion*: an ``X%`` partitioning is the **largest**
   ``z`` in ``{1..n}`` such that the area under the entropy curve from the
   ``z``-th variable to the last one is at least ``X%`` of the total area.
   ``X = 0%`` therefore means no partitioning at all (``z = n``).

Regression target, reproduced by :func:`area_partition_z` and
:func:`Partition.locations`: on the authors' own ``pmed7`` data (ACO + BRKGA +
ILS pooled), ``|S(T)| = 423``, ``z(60%) = 19`` and the partitioned space has
``312`` locations -- the three numbers reported in the paper (Table 8 and the
text of S6.2).

Solutions are handled as the *set of positions holding a 1*, which is the
natural form of both inputs we care about: MoWFLOP logs a sorted list of
occupied candidate indices, and the p-median data a dense binary string.  For a
binary domain the two representations carry the same information, and two
solutions agree on all retained positions exactly when their sets of ones
intersected with the retained positions coincide.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from hashlib import blake2b

Solution = frozenset[int]

LOCATION_PREFIX = "E"


def from_index_list(text: str) -> Solution:
    """``"17 227 270"`` (MoWFLOP ``occupied``) -> set of positions."""
    return frozenset(int(token) for token in text.split())


def from_binary_string(text: str) -> Solution:
    """``"0101..."`` (p-median trace) -> set of positions holding a 1."""
    return frozenset(i for i, char in enumerate(text) if char == "1")


def position_entropy(solutions: list[Solution], n: int) -> list[float]:
    """Shannon entropy of every position over a set of *unique* solutions."""
    total = len(solutions)
    if total == 0:
        raise ValueError("cannot compute entropy of an empty solution set")
    # ones[i] = quantas soluções têm 1 na posição i
    ones = Counter()
    for solution in solutions:
        # para da ID de turbina em solution, incrementa o contador de 1s correspondente
        ones.update(solution)
    entropy = []
    for position in range(n):
        k = ones.get(position, 0)
        value = 0.0
        if k:
            # calcula a probabilidade de 1 na posição i
            p = k / total
            value -= p * math.log2(p)
        if total - k:
            # calcula a probabilidade de 0 na posição i
            p = (total - k) / total
            value -= p * math.log2(p)
        entropy.append(value)
    return entropy


def rank_positions(
    entropy: list[float], tie_break: str = "index", seed: int | None = None
) -> list[int]:
    """Positions ordered by non-increasing entropy.

    ``tie_break="random"`` follows the paper (ties broken at random, seeded so
    the run is reproducible); ``tie_break="index"`` is the deterministic
    variant, which is what the regression tests use.
    """
    if tie_break not in {"index", "random"}:
        raise ValueError(f"unknown tie_break: {tie_break!r}")
    order = list(range(len(entropy)))
    if tie_break == "random":
        random.Random(seed).shuffle(order)
        return sorted(order, key=lambda i: -entropy[i])
    return sorted(order, key=lambda i: (-entropy[i], i))


def area_partition_z(entropy_desc: list[float], percent: float) -> int:
    """``z`` for an ``X%`` partitioning, from the non-increasing entropy curve.

    Largest ``z`` such that the area from the ``z``-th variable to the last is
    at least ``X%`` of the total area.  The suffix sums are non-increasing in
    ``z``, so the feasible set is a prefix and the answer is its last element.
    """
    if not 0 <= percent <= 100:
        raise ValueError(f"percent must be in [0, 100], got {percent}")
    n = len(entropy_desc)
    total = sum(entropy_desc)
    if total <= 0:
        # Não há curva pra trabalhar
        return n
    target = percent / 100.0 * total
    suffix = 0.0
    # soma acumulada de trás pra frente = área sob a curva da posição z até a última
    for z in range(n, 0, -1):
        suffix += entropy_desc[z - 1] 
        if suffix >= target:
            return z  # decrescente, então o primeiro z que satisfaz a condição é o maior
    return 0


def location_id(projection: Solution) -> str:
    """Short stable id for a location.

    The projection can hold hundreds of positions; writing it verbatim into the
    trajectory files would blow them up, so the id is a 64 bit digest and the
    full projection is kept in the side table written by :mod:`mowflop.emit`.
    """
    key = ",".join(str(position) for position in sorted(projection))
    digest = blake2b(key.encode("utf-8"), digest_size=8).hexdigest()
    return f"{LOCATION_PREFIX}{digest}"


@dataclass
class Partition:
    """A concrete entropy partitioning of one instance's search space."""

    n: int
    entropy: list[float]
    order: list[int]
    z: int
    percent: float | None = None
    tie_break: str = "index"
    seed: int | None = None
    keep: frozenset[int] = field(init=False) # posições de maior entropia que serão usadas no particionamento

    def __post_init__(self) -> None:
        if not 0 <= self.z <= self.n:
            raise ValueError(f"z must be in [0, {self.n}], got {self.z}")
        self.keep = frozenset(self.order[: self.z])

    def project(self, solution: Solution) -> Solution:
        """``s_z``: the solution restricted to the retained positions."""
        return solution & self.keep

    def assign(self, solution: Solution) -> str:
        return location_id(self.project(solution))

    def locations(self, solutions: list[Solution]) -> set[Solution]:
        """Distinct locations reached by a set of solutions."""
        return {self.project(solution) for solution in solutions}

    @property
    def entropy_desc(self) -> list[float]:
        return [self.entropy[i] for i in self.order]

    def tie_size_at_z(self) -> int:
        """How many positions share the entropy of the ``z``-th one.

        A ``z`` landing inside a large tie block means the retained set is
        largely arbitrary -- the paper breaks those ties at random.
        """
        if self.z == 0:
            return 0
        cutoff = self.entropy[self.order[self.z - 1]]
        return sum(1 for value in self.entropy if math.isclose(value, cutoff))

    def describe(self) -> dict:
        values = self.entropy_desc
        return {
            "scheme": "entropy",
            "n": self.n,
            "z": self.z,
            "percent": self.percent,
            "tie_break": self.tie_break,
            "seed": self.seed,
            "entropy_total": sum(values),
            "entropy_max": max(values) if values else 0.0,
            "positions_nonzero": sum(1 for value in values if value > 0.0),
            "tie_size_at_z": self.tie_size_at_z(),
        }


def build_partition(
    solutions: list[Solution],
    n: int,
    percent: float | None = None,
    z: int | None = None,
    tie_break: str = "index",
    seed: int | None = None,
) -> Partition:
    """Entropy partitioning of ``S(T)``; give either ``percent`` or ``z``."""
    if (percent is None) == (z is None):
        raise ValueError("give exactly one of percent or z")
    entropy = position_entropy(solutions, n)
    order = rank_positions(entropy, tie_break=tie_break, seed=seed)
    if z is None:
        z = area_partition_z([entropy[i] for i in order], percent)
    return Partition(
        n=n, entropy=entropy, order=order, z=z, percent=percent,
        tie_break=tie_break, seed=seed,
    )
