# `scripts/mowflop_comparison/`

Scripts that compare **this work's** MoWFLOP metaheuristic runs against the
**CEC 2025 / wflopcec26** reference results, to check that our executions are
correct (i.e. that we reproduce the published benchmark once the wind
protocol is matched).

## Background: why a "wind-corrected" comparison

CEC's runner samples a `(angle, wind)` pair **per run** from a wind rose.
An earlier version of `STN_MoWFLOP` instead hardcoded `angle=30, wind=10`
for every run, which made our fronts diverge sharply from CEC's (power
scales roughly with the cube of wind speed, so a fixed wind pins a single
achievable power ceiling). The fix replays CEC's *exact recorded*
`(angle, wind)` per run, read from a version-controlled map instead of
CEC's original runtime sampler (that sampler's code is lost). Our results
then reproduce CEC's almost exactly — this is what these scripts show.

Our wind-corrected runs live in a parallel output tree,
`raw_results/meta_heuristics_stn_windcorrected/`, leaving the old
fixed-wind tree (`meta_heuristics_stn/`) untouched.

## `pareto_check.py`

One figure per `(instance, algorithm)`: a 2×5 small-multiple grid of the
**run-matched** comparisons. Panel *k* overlays our run *k* Pareto front
against CEC's matching run, both under the **identical** `(angle, wind)`
draw. Also writes a per-run summary CSV.

Run-matched, not pooled: wind varies per run, and we have 10 runs per
instance while CEC has 20, so pooling would compare wind *distributions*,
not algorithm behaviour. Matched runs share the wind, so the achievable
frontier is identical and any gap between the two fronts is a real
algorithmic difference.

```
../../.venv/bin/python pareto_check.py                 # all 10 instances, both algos
../../.venv/bin/python pareto_check.py --instances 178 # subset
../../.venv/bin/python pareto_check.py --pool p10_i50  # which STN p-config to read (default p100_i50)
```

### Output — where it goes and what to keep

The script writes to `plots/pareto_check/`
(`pareto_ns<ID>_<algo>_<pool>.png` + `pareto_check_summary_<pool>.csv`).
That folder is **gitignored, disposable scratch** — it is fully
regenerated on every run, so delete it whenever (`rm -rf
plots/pareto_check/`); nothing depends on it.

The **kept** copy is under `sharing/pareto_front_vs_cec/` (curated,
committed, with its own README). Repo convention: analysis scripts write
only to `plots/`, and hand-picked results are copied into `sharing/` — so
re-running a script, here or on a server, can never skip execution
("output already exists") or clobber a committed/under-review result.

## History

`plot_corrected_comparison.py` (removed on branch
`verificacao-pareto-vs-cec`) was the original single-run proof-of-concept
that produced the `sharing/meeting_2026-08-27/02_our_vs_cec/` figures.
By the time it was removed it was non-functional (dead `CEC_ROOT` path,
`NOSSO_RUN_ID = 50` which never existed, missing output dir) and only
covered `ns101` / `ns178` as a raw scatter. `pareto_check.py` is a strict
superset; the meeting figures it made are already in `sharing/`, and the
script is recoverable from history (last present at commit `22476d44`'s
parent).

## Data sources (canonical paths, no local copies)

| Role | Path | Layout |
|---|---|---|
| This work | `../../supercomputer_backup/raw_results/meta_heuristics_stn_windcorrected/<algo>/ns<ID>/<pool>/<run 0..9>/ns<ID>_<algo>_1000000.txt` | 10 runs/instance |
| CEC 2025 | `../../STNs-MOCO-MoWFLOP/raw_results/wflopcec26/<algo>/ns<ID>/<run 1..20>/<ID>_<algo>_1000000.txt` | 20 runs/instance |
| Wind map | `../../STN_MoWFLOP/source_code/meta_heuristics/wind_corrected/cec_wind_map.csv` | `instance,algo,run_id,angle,wind` |

- `pareto_check.py` reads **this work's** side from `supercomputer_backup/`,
  not the live `STN_MoWFLOP/raw_results/` tree, so results do not depend on
  the sibling repo's current sync state. Point it elsewhere by editing
  `OUR_ROOT` if a fresher tree is available.
- The `*_1000000.txt` files are the final population after `10^6`
  evaluations: two whitespace-separated columns, **col 1 = construction
  cost** (minimised), **col 2 = power output** (maximised), both positive.
  These are the two MoWFLOP objective values, *not* runtime or any
  by-product of the STN construction.

## Naming / indexing conventions (the two friction points)

1. **`ns` prefix.** CEC names instances with bare integers (`178`,
   file `178_moead_1000000.txt`). This workspace prefixes them `ns`
   ("New Sites", the Cazzaro & Pisinger set) at the directory level —
   deliberately, to avoid colliding with the 300 synthetic instances at
   `STN_MoWFLOP/instances/site/<n>` that reuse the same integers for
   unrelated wind farms (`instances/site/178` ≠ `ns178`). The vendored CEC
   tree is itself mixed: `ns178/` directory, `178_*` files inside. Bridge
   scripts therefore carry both forms (`f"ns{inst}"` for directories,
   `f"{inst}_{algo}"` for CEC file names).

2. **Run-index base.** CEC's runner numbers run directories `1..20`
   (1-based). This work's STN runner numbers them `0..9` (0-based).
   `cec_wind_map.csv` is 0-based to match this work, so **wind-map
   `run_id` k ⇒ CEC directory k+1** — the same wind scenario, differing
   only in the runners' indexing base. Verified against CEC's `log.txt`
   `Angle`/`Wind` fields for `ns178` (all 10 matched runs agree exactly).

Neither convention alters CEC's data; the re-indexing happens only when
building `cec_wind_map.csv`.

## Reading the output

Per-run columns in `pareto_check_summary_<pool>.csv`:

- `our_nd`, `cec_nd` — size of each side's non-dominated front for that run.
- `our_cost_min` vs `cec_cost_min`, `our_power_max` vs `cec_power_max` —
  the front extremes. `d_cost_min_pct` / `d_power_max_pct` give the signed
  relative gap; for a correct execution these are a fraction of a percent
  (e.g. `ns178` MOEA/D: mean `d_cost_min_pct ≈ 0.001 %`).
- `C_cec_ours`, `C_ours_cec` — **set coverage** `C(X, Y)` = fraction of
  front `Y` weakly dominated by at least one point of front `X`
  (Zitzler & Thiele, 1998). Not symmetric; `C(X,Y) + C(Y,X) ≠ 1`. Both
  bouncing in `0.2–0.9` with neither systematically at 1 is the expected
  signature of two well-converged stochastic fronts interleaving along
  the same frontier. A run where `C(cec, ours) ≈ 1` and `C(ours, cec) ≈ 0`
  would flag a genuinely worse (or mis-configured) run.

The front extremes are the strong evidence; the coverage metric is a
weaker secondary check.

## Caveats

- 10 matched runs only (this work's `run_id 0..9`), because that is what
  the STN campaign produced; CEC's runs `11..20` have no counterpart here.
- `--pool` selects the STN observer config (`p10/p50/p100`). `p` is the
  number of STN observer vectors, *not* the MOEA population size, so it
  does not affect the final Pareto front — `p100_i50` is the default only
  because it is the richest logged set.
- Instances without a CEC counterpart (the sparse `*_r1e-04` / `*_r1e-05`
  families, and `506–513`) cannot be checked this way — they need an
  internally-pooled reference set instead.
