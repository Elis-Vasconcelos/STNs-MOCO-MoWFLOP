"""Search space partitioning for MoWFLOP Search Trajectory Networks.

This package is an *upstream* stage: it reads the raw trajectory logs produced
by the C++ campaign, maps each logged solution to a *location* of a partitioned
search space, and writes files in exactly the format that ``scripts/create .R``
already reads.  No R script is modified, so the partitioned and unpartitioned
models traverse byte-identical R code and any metric difference is attributable
to the partitioning alone.

Schemes implemented here:

``entropy``
    Shannon-entropy partitioning of Ochoa, Malan & Blum (Applied Soft
    Computing, 2021), Section 5.4.

``raw``
    No partitioning (Ochoa et al. 2023): one location per distinct solution.
    The identity function, kept because it is the denominator of every claim of
    the form "did aggregation happen at all?".
"""

__all__ = [
    "io_raw",
    "entropy",
    "schemes",
    "reference_front",
    "emit",
]
