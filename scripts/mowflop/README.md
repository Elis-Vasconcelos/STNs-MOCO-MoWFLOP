# `mowflop`: search space partitioning for MoWFLOP STNs

This package sits **upstream** of the R pipeline. It reads the raw campaign logs,
maps every logged solution to a *location* of a partitioned search space, and
writes files in exactly the format `scripts/create .R` already reads.

No `*.R` file is modified. The partitioned model and the unpartitioned baseline
therefore traverse byte-identical R code, and any difference in the metrics is
attributable to the partitioning alone.

## Setup

```bash
python3 -m venv --without-pip .venv     # this environment has no ensurepip
curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python -
.venv/bin/pip install -r requirements.txt
```

## Schemes

| scheme | reference | location of a solution |
|---|---|---|
| `entropy` | Ochoa, Malan & Blum, *Applied Soft Computing* 2021, §5.4 | projection onto the `z` positions of highest Shannon entropy, `z` from the area criterion |
| `raw` | Ochoa et al. 2023 | the solution itself (no partitioning) |

The occupancy-signature scheme and the Hamming variants slot in by implementing
`assign()`/`project()` in `schemes.py`; nothing downstream changes.

## Usage

```bash
cd scripts

# partition and emit (entropy, 60% area criterion)
../.venv/bin/python -m mowflop.partition --instance ns101 --config p100_i50 \
    --scheme entropy --percent 60

# unpartitioned baseline
../.venv/bin/python -m mowflop.partition --instance ns101 --config p100_i50 --scheme raw

# check the emitted files against create .R's assumptions before running R
../.venv/bin/python -m mowflop.validate_r_input --data-dir ../data/mowflop_x60

# RQ1 diagnostic: tables and figures
../.venv/bin/python -m mowflop.diagnose_entropy --instance ns101 --config p100_i50 \
    --control-pmed7 --figs

# tests, including the regression against the paper's published numbers
../.venv/bin/python -m unittest mowflop.test_partition -v
```

Outputs land in `data/mowflop_<tag>/{MOEAD,NSGA2}/`, `pf/mowflop/`,
`locations/mowflop_<tag>/` and `reports/rq1_entropy/`.

Then, unchanged, the R side: point `infolder`/`parfolder`/`outfolder` in
`scripts/create .R` at `data/mowflop_<tag>/`, `pf/mowflop/` and `stns/mowflop_<tag>/`.

## Why the implementation can be trusted

`mowflop.test_partition.TestPmed7Regression` runs the scheme over the authors'
own `pmed7` traces (`../STNs/pmed7`) and checks three numbers they published:
`|S(T)| = 423` and 423 nodes unpartitioned (Table 8), `z = 19` for a 60%
partitioning (§6.2), and 312 nodes partitioned (Table 8). All three reproduce
exactly, which also settles the wording of the area criterion: an `X%`
partitioning is the largest `z` such that the entropy area **from the z-th
variable to the last** is at least `X%` of the total.

## Two traps worth remembering

* `create .R:141` groups nodes by `(f1, f2, Solution1, Vector)`. A location
  carries many objective vectors, so without a single canonical objective per
  location that grouping would silently split one location into several nodes and
  undo the partitioning. `emit.canonical_objectives` picks a really visited
  solution — reference-front membership first, then lexicographic
  `(f_cost, -f_power)` — which is the multi-objective reading of the paper's
  `f(s_z) := min{f(s')}`.
* Every edge endpoint must exist in `nodes`, so the last recording of each
  `(Run, Vector)` trajectory points at itself. That is the convention of the
  original rho-mnk data too.
