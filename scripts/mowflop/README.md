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
| `grid` | `papers/STN_MoWFLOP.pdf` §6-7 (this thesis's contribution) | occupation signature `o_ℓ(γ)`: turbine count per cell of a grid of side `ℓ = κ√(A/τ)` overlaid on the site |

The Hamming variants would slot in the same way, by implementing
`assign()`/`project()` in `schemes.py`; nothing downstream changes.

## `grid` scheme: geometry and κ (paper §6-7, §9 Etapa 3)

`geometry.py` computes, per instance, the three inputs eq. 12 (`ℓ = max(κ√(A/τ), σ)`) needs:

- **A**: shoelace formula over `instances/site/<inst>/geometry.txt` (site boundary polygon).
- **τ**: sum of `instances/site/<inst>/turbines_per_zone.txt` — this file can hold
  multiple zone counts on *one* whitespace-separated line (e.g. `ns203`: `"16 25"`,
  τ=41), so summing only the first token undercounts; sum every token.
- **σ**: the paper defines it (§10.4 step 2, `ℓ ≥ σ`) but never publishes a number,
  and the campaign's C++ (`STN_MoWFLOP/source_code/meta_heuristics`) has **no**
  minimum-distance feasibility check anywhere (`calculate_interference` uses the
  240m rotor diameter only for the Jensen wake model, never to reject two candidate
  positions for being too close). We use `ROTOR_DIAMETER = 240.0` (hardcoded in
  `geometry.py`, matching `generate_rSolution.cpp:163`) as σ — the one physically
  grounded distance that exists in the codebase. Diagnostic-only note: the real
  candidate-grid spacing for `ns101` is ~159.6m (true nearest-neighbor Euclidean
  distance, verified, not just axis-aligned gap), i.e. *finer* than the rotor
  diameter — so the candidate grid is **not** pre-spaced to satisfy σ "for free"
  the way `landscape-mo/CLAUDE.md` assumes. Exposed as `SiteGeometry.candidate_spacing`
  for anyone who wants to revisit this choice.

### Choosing the three κ regimes (fino / adequado / grosseiro)

The paper is explicit on two constraints the naive approach (sweep κ, eyeball one
instance) violates:

1. **§7.3 "κ deve ser o mesmo para todas as instâncias?" — Sim.** κ is a global
   meta-parameter; calibrating it per-instance defeats the adaptive rule's whole
   purpose (cross-instance comparability of `n_total`/`n_shared` breaks otherwise).
2. **§9 Etapa 3 / §10.5**: pick exactly **three** values, chosen *before* running
   anything, via the closed-form degeneracy ceiling (§7.2 eq. 8, stars-and-bars):

   `#assinaturas ≤ C(τ+G-1, τ)`, with `G ≈ τ/κ²`

   validated against **the smallest-τ instance** ("validar contra degeneração no
   menor τ", §10.5) — smaller τ degenerates fastest for a given κ, so it's the
   binding constraint.

τ across the 10 instances with campaign data (`STN_MoWFLOP/instances/site/ns*/turbines_per_zone.txt`):

```
ns48=21  ns178=23  ns192=31  ns488=40  ns203=41  ns202=47  ns101=63  ns465=79  ns41=123  ns440=140
```

`ns48` (τ=21) is smallest. Eq. 8 on `ns48` across candidate κ:

| κ | G=τ/κ² | signature ceiling `C(τ+G-1,τ)` |
|---|---|---|
| 0.5 | 84 | ~5×10²¹ (unconstrained) |
| 1.0 | 21 | ~3×10¹¹ (unconstrained) |
| **2.0** | 5 | **12,650** (tightening, still safe) |
| 2.5 | 3 | 253 (destructive) |
| 3.0 | 2 | 22 (destructive) |
| 4.0 | 1 | 1 (total collapse — one cell covers the whole site) |

The ceiling cliffs between κ=2.0 and κ=3.0. That fixes the three regimes at
**κ=0.5 (fino), κ=1.0 (adequado), κ=2.0 (grosseiro)** — each 2× the last, all
comfortably clear of the collapse threshold on every instance we have (larger-τ
instances have more headroom, since `G` grows with τ for fixed κ; `ns48` is
always the tightest case). Reproduce this check:

```bash
cd scripts
../.venv/bin/python3 -c "
import math
def log10_comb(n, k):
    return (math.lgamma(n+1) - math.lgamma(k+1) - math.lgamma(n-k+1)) / math.log(10)
tau = 21  # ns48, smallest tau in our data
for kappa in [0.5, 1.0, 2.0, 2.5, 3.0, 4.0]:
    G = max(1, round(tau / kappa**2))
    print(kappa, G, 10 ** log10_comb(tau + G - 1, tau))
"
```

This is a diagnostic *ceiling* only (§7.2 Observação 1) — the real node count is
always lower, since it also depends on which signatures the trajectories actually
visit. The empirical reduction for each regime (raw solutions → grid locations,
`ns101/p100_i50`, 52,683 unique raw solutions) is: κ=0.5 → 46,481 (11.8%
reduction), κ=1.0 → 36,724 (30.3%), κ=2.0 → 20,318 (61.4%).

Tie-breaking for the entropy ranking defaults to `tie_break="random"` (seeded,
so a given `seed` is still reproducible), which is what the paper does. The
deterministic `tie_break="index"` variant exists only for the regression
tests, which check against numbers the authors published for one specific,
deterministic ranking.

## Usage: the full pipeline, one command per stage

Prerequisites (once): `$MOWFLOP_RAW` pointing at
`STN_MoWFLOP/raw_results/meta_heuristics_stn` (see `io_raw.raw_root`), and
`raw_results/wflopcec26_results/` populated with the group's MOEA/D and
NSGA-II runs (see "Reference front" below) -- needed by every step from
`partition.py` onward, since the reference front is computed there now.

1. **`partition.py`** -- no CLI, a block of constants at the top of the file
   (`INSTANCE`, `CONFIG`, `SCHEME`, `PERCENT` [entropy], `KAPPA` [grid], ...).
   Edit them, then run once per `(instance, config, scheme, param)` you want:

   ```bash
   cd scripts
   # edit scripts/mowflop/partition.py (INSTANCE, CONFIG, SCHEME, PERCENT/KAPPA), then:
   ../.venv/bin/python -m mowflop.partition
   ```

   Writes `data/mowflop_<tag>/{MOEAD,NSGA2}/`, `pf/mowflop/`,
   `locations/mowflop_<tag>/`, and computes the reference front (this
   campaign's own points *and* `reference_front.external_points` -- see
   below).

2. **`run_create_r.py`** -- runs Ochoa's unmodified `create .R` for a tag
   (both algorithms in one call):

   ```bash
   ../.venv/bin/python -m mowflop.run_create_r --tag g1.0
   ```

   Writes `stns/mowflop_<tag>/{MOEAD,NSGA2}/*.RData`.

3. **`run_metrics_r.py`** -- runs Ochoa's unmodified `metrics.R`, one call per algorithm:

   ```bash
   ../.venv/bin/python -m mowflop.run_metrics_r --tag g1.0 --algo MOEAD
   ../.venv/bin/python -m mowflop.run_metrics_r --tag g1.0 --algo NSGA2
   ```

   Writes `metrics/mowflop_<tag>_<algo>_metrics.csv`.

4. **`run_plot_r.py`** -- one PNG per `(algo, P)`, both layouts:

   ```bash
   ../.venv/bin/python -m mowflop.run_plot_r --tag g1.0 --layout both
   ```

   Writes `plots/mowflop_<tag>/<ALGO>_..._<of|fd>.png`.

5. **`run_compare_r.py`** -- the 2x3 (algo x P) comparison tile per tag, with
   a Count scale shared across every tag/κ available for that instance (see
   "Reading the output" below). `--tags` defaults to auto-discovering every
   tag with data for `--instance` -- almost always what you want, since a
   narrower manual list risks a Count scale that doesn't actually span
   everything being compared:

   ```bash
   ../.venv/bin/python -m mowflop.run_compare_r --instance ns101 --layout both
   ```

   Writes `plots/mowflop_<tag>/compare_<instance>_<of|fd>.png`, one per tag.

Steps 2-5 never modify `create .R`/`metrics.R`/`plot.R` -- each wrapper
copies the relevant prefix, rewrites only the folder/loop constants, diffs
against the original to refuse running if anything else changed, then
deletes the temp file. Rerunning the whole chain for a new tag or a new
instance is exactly repeating steps 1-5 with different constants/`--tag`.

Other utility scripts, run standalone as needed:

```bash
# check the emitted files against create .R's assumptions before running R
../.venv/bin/python -m mowflop.validate_r_input --data-dir ../data/mowflop_x60

# RQ1 diagnostic: the entropy curve (paper's Fig. 5) and the z of each area criterion
../.venv/bin/python -m mowflop.diagnose_entropy --instance ns101 --config p100_i50 --figs

# tests, including the regression against the paper's published numbers
../.venv/bin/python -m unittest mowflop.test_partition mowflop.test_grid mowflop.test_run_compare_r -v
```

## Reference front: our campaign + the group's best-known (wflopcec26)

`partition.py` no longer computes the reference front from only this
campaign's own logged points -- `reference_front.pareto_front` is generic
(non-dominated over whatever it's given), and `partition.py` now feeds it
this campaign's points *unioned with* `reference_front.external_points(instance)`
before filtering, so `Position="Pareto"` reflects the best the group has
found, not just what our own MOEA/D and NSGA-II happened to reach. Concretely
for `ns101`: our own campaign's front alone has 414 points; merged with the
group's, 385 of the 387 final points come from the group's runs, which
reached power values (~559) far below anything our own campaign logged
(~1.85e5) -- our own-only front was a real underestimate, not a defensible
simplification.

Only one external source is used, deliberately:

* **wflopcec26** -- **verified**, not assumed: its
  `instances/sites/<N>/{geometry.txt,turbines_per_zone.txt}` are byte-identical
  (module `\r\n`) to our own `STN_MoWFLOP/instances/site/ns<N>/`, checked for
  all 10 instances we have data for. Its numeric `<N>` is exactly our `ns<N>`.
  MOEA/D and NSGA-II runs are vendored at `raw_results/wflopcec26_results/`
  (gitignored -- copy them in from the `wflopcec26` repo if missing, with
  instance folders renamed to our `ns<N>`). `COMOLSD`, a third algorithm the
  group also ran, isn't vendored there yet.

* **BRACIS** (Silva & Fernandes, already on disk at `STN_MoWFLOP/raw_results/
  meta_heuristics/`, no clone needed) is **deliberately excluded**: its
  numeric instance IDs do *not* correspond to ours (checked: its `101` has a
  completely different cost/power scale than our `ns101` -- ~4.7x the cost,
  ~78x the power -- unlike CEC's `101`, which matches almost exactly). Its
  numbering comes from a larger, unrelated instance catalog. Note that
  `STN_MoWFLOP`'s own instances are still properly CEC-sourced (confirmed by
  the geometry match above) regardless of this -- BRACIS's raw_results being
  present there is a separate, unrelated fact about that repo's history, not
  a sign the instances themselves are compromised.

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

## Reading the output: tags, titles, layouts

**Folder/file tags** (`stns/mowflop_<tag>/`, `plots/mowflop_<tag>/`, filenames'
`_<tag>_` field): `x60` = entropy scheme, 60% area criterion. `g0.5`/`g1.0`/`g2.0`
= grid scheme at that κ value. `raw` = no partitioning. One tag = one scheme +
parameter choice; everything under it is comparable to everything else under
it, but not directly to a different tag without accounting for what changed.

**Plot titles say `"ALGO r = instance"`** (e.g. `"MOEAD r = ns101"`), the same
string for every P and every κ. This is *not* a bug, and it will keep
happening no matter which of our scripts renders it, because `run_plot_r.py`
(Arthur's own wrapper, not something this session added) deliberately
reuses `plot_stn` **unmodified**: `plot.R:47`
(`tit <- paste0(t[1]," r = ",t[3])`) is untouched Ochoa upstream code, where
`t[3]` was her rmnk benchmark's correlation parameter ρ ("rho" -- see the
commented-out fuller title on `plot.R:46`: `r=,m=,n=,k=`). Our filenames just
happen to put the instance name in that same `t[3]` slot, so the leftover
`"r ="` label gets reused for something it was never about. Fixing it would
mean editing `plot.R` itself, which breaks the byte-identical-upstream
guarantee this whole package is built to preserve -- not worth it for a
title string. P and κ aren't in the title at all either; rely on the
filename / which `plots/mowflop_<tag>/` folder a PNG came from.

**`of` vs `fd`** (`plot.R`'s two layouts, both untouched upstream code):
`of` = *objective-space* -- node x/y are the real `f1`/`f2` values, so the
plot is directly readable as cost-vs-power; partitioning only changes how many
points are drawn, not where, so its effect is subtle to the eye here (see
below). `fd` = *force-directed* (`graphopt`) -- node position comes purely
from graph topology, no relationship to the objectives; illegible past a few
thousand nodes, but the one layout where node-count reduction is visually
obvious.

**Axis scale in `of` plots is consistent across P/κ/tag, but not because
anything pins it.** Neither `plot.R` nor `create.R` sets an explicit
`xlim`/`ylim`/shared scale anywhere (checked: no such call in either file,
upstream or ours) -- each `of` plot is ggplot's default per-plot autoscale
over whatever nodes that one STN has. In practice the ranges still line up
(verified by inspecting rendered `ns101`/MOEAD/p100 at κ=1.0 and κ=2.0 side
by side: same ~1.3e8-1.55e8 / ~2e5-6e5 span) because the axis extremes are
always set by `Begin`/`End`/`Pareto`/reference-front nodes, and
`emit.canonical_objectives` always assigns those a genuinely visited
solution's `f1`/`f2` -- never an invented centroid. Partitioning only
changes how the interior (`Medium`) points get grouped; it can't move where
a trajectory starts, ends, or touches the Pareto front. So the shared scale
here is an emergent consequence of that invariant, not a setting anyone
(Ochoa, Arthur, or this thesis) configured -- worth knowing so you don't go
looking for a `coord_cartesian()` call that isn't there.

## Grid vs entropy: what the numbers actually show

Real node/edge counts from the `.RData` (not the coarser combined-S(T)
location count `partition.py` logs at emission time -- that one pools both
algorithms before `create.R` runs; this table is the final per-algorithm STN,
what's actually plotted):

| scheme | MOEAD nodes (ns101, p100i50) | edges | reduction from 52,683 raw solutions |
|---|---|---|---|
| entropy `x60` | 22,009 | 42,623 | 58.2% |
| grid `g0.5` | 23,247 | 42,666 | 55.9% |
| grid `g1.0` | 14,573 | 30,433 | 72.3% |
| grid `g2.0` | 6,111 | 14,094 | 88.4% |

Entropy `x60`'s aggregation strength lands almost exactly between grid's
`g0.5` and `g1.0` -- not engineered (κ was chosen from the eq. 8 check, not
by matching entropy), but a real finding: **grid spans a wider, continuously
tunable range of aggregation than entropy's single `X%` lever gives you.**
This is the strongest evidence-based comparison point available; the visual
`of` plots mostly don't show it (same real f1/f2 coordinates regardless of
partitioning, so a 4-9x drop in node count along one dense curve is subtle at
plot resolution) -- the `fd` layout and this table are where it's visible.

We do not have this same node/edge table for entropy on `ns178` (only ran
grid there ourselves; the entropy `ns178` images are Arthur's own prior run,
whose underlying `.RData` we don't have access to) -- any `ns178` comparison
should stay qualitative/visual, not numeric.

## Known non-blocking caveats

* σ (eq. 6's floor on cell size) has no published numeric value in the paper
  or BRACIS/Silva papers, and the campaign's C++ never enforces any minimum
  turbine spacing at runtime either -- so there's no "correct" σ to be loyal
  to in the first place; the campaign simply doesn't have that constraint,
  and no σ choice on our end retroactively gives it one. σ only controls how
  fine the *grid* is allowed to get, not whether the underlying solutions are
  physically valid. In practice it's moot for every result in this repo: at
  all three chosen κ (0.5/1.0/2.0), `ell` (705m/1409m/2819m for ns101) is far
  above any candidate σ value, so the floor `ell >= sigma` never binds --
  `ROTOR_DIAMETER = 240.0` in `geometry.py` is a documented placeholder, not
  a load-bearing choice.
* CoMOLS/D (the paper's third algorithm) isn't in the campaign data
  (`raw_results/` only has `moead/`, `nsga2/`) or implemented anywhere in
  `STN_MoWFLOP/source_code`. Out of scope for now.
