# external_pf/

Vendored data from the group's own `wflopcec26` repository (the paper "Meta-Learning-Based
Algorithm Selection for Multi-Objective Wind Farm Layout Optimization" — see
`wflopcec26/README.md` for their original documentation). This was previously a loose,
undocumented sibling clone (`~/Projects/TCC/external_pf/`); it's vendored here instead so
the STN pipeline never depends on an external clone existing on whoever's machine runs it.

## What's kept, and why

`wflopcec26/` here is **not a full copy** of the group's original repo — only the parts our
pipeline actually needs:

- `wflopcec26/instances/` and `wflopcec26/source_code/` — the group's original instance
  definitions and algorithm source code, kept for provenance/reproducibility. **Not read by
  any script in this repo** — if you ever need to re-run their algorithms from source,
  it's here, but nothing here does that automatically.
- `wflopcec26/results/` — the actual data our pipeline *does* read: pre-extracted per-run
  result checkpoints (`scripts/mowflop/reference_front.py`'s `external_points()`), used to
  build the external reference front for the original 10 CEC instances. This used to live
  at `raw_results/wflopcec26_results/` — moved here so all "external group" data (their
  instances, their code, their results) lives under one root, instead of being split across
  two unrelated top-level directories.

Everything else from their original README's repository structure
(`algorithms_raw_results/`, `metafeatures_raw/`, `regression_metrics/`, `metadataset_final/`,
`correlation_matrix/`, `gap_spearman_tables/`) was **not vendored** — `results/` here is a
much smaller, already-extracted subset of their `algorithms_raw_results/`, not the full
original folder.

## What's *not* here

`raw_results/` at the repo root is a completely separate thing: **our own** campaign's
output (`meta_heuristics_stn/`, and eventually the wind-corrected and sparse-instance
campaigns), read by default by `scripts/mowflop/io_raw.py`. If you're looking for our
results, they're there, not here.
