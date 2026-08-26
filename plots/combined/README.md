# Combined/tiled plots

Composite images built from `plots/mowflop_<tag>/*.png` by ad hoc tiling
scripts (not part of the versioned `mowflop` package -- these live in the
session scratchpad). Not regenerated automatically; rerun the tiling scripts
if the underlying per-panel plots change.

- **`final/`** -- one image per (scheme/kappa, instance, layout): 2x3 grid
  (rows=MOEAD/NSGA2, cols=P=10/50/100 crescent), with real node/edge counts
  annotated under each panel (pulled from `metrics/mowflop_<tag>_<algo>_metrics.csv`,
  not estimated). The current, correct version -- use these.
- **`compare/`** -- one image per (instance, layout), all regimes stacked
  vertically for direct comparison: `ns101_of.png` (entropy x60 + grid
  0.5/1.0/2.0), `ns178_of.png` and `ns178_fd.png` (grid 0.5/1.0/2.0 only,
  no entropy baseline available for ns178). `ns101` has no `fd` compare
  image -- only `g2.0` was ever rendered there (`final/grid_g2.0_ns101_fd.png`),
  0.5/1.0 were too large to attempt.
- **`archive/`** -- superseded earlier versions: wrong P column order
  (alphabetical p100/p10/p50 instead of crescent 10/50/100), one row-level
  node/edge stat instead of per-panel (misleading, since counts differ by P),
  or no stats at all. Kept for reference, not for presenting.
  
## What `x60` means (keep forgetting this one)

`x60` = the **entropy** scheme (Ochoa, Malan & Blum 2021), at a 60% area
criterion. Not grid, not kappa -- a completely different partitioning method,
kept as a baseline to compare grid against. `g0.5`/`g1.0`/`g2.0` = the **grid**
scheme (this thesis) at kappa=0.5/1.0/2.0. See
`scripts/mowflop/README.md`'s "Schemes" table for the full method comparison.

## Why these three kappa values

Chosen *before* running anything, per STN_MoWFLOP.pdf S7.2/S7.3/S9: pick
exactly 3 regimes (fino/adequado/grosseiro), the same kappa for every
instance (not tuned per instance), validated against the eq. 8 degeneracy
ceiling (`#assinaturas <= C(tau+G-1, tau)`, stars-and-bars, `G ~= tau/kappa^2`)
on the **smallest-tau instance** in our data (`ns48`, tau=21) -- smaller tau
degenerates fastest for a given kappa, so it's the binding constraint.

| kappa | regime | G=tau/kappa^2 (ns48) | signature ceiling (ns48) | ell, ns101 (tau=63) | ell, ns178 (tau=23) | ell, ns48 (tau=21) |
|---|---|---|---|---|---|---|
| 0.5 | fino | 84 | ~5x10^21 (unconstrained) | 704.7m | 1,112.9m | 1,169.0m |
| 1.0 | adequado | 21 | ~3x10^11 (unconstrained) | 1,409.5m | 2,225.8m | 2,337.9m |
| **2.0** | **grosseiro** | **5** | **12,650 (tightening, still safe)** | 2,819.0m | 4,451.5m | 4,675.8m |
| 2.5 | (not used) | 3 | 253 (destructive) | -- | -- | -- |
| 3.0 | (not used) | 2 | 22 (destructive) | -- | -- | -- |
| 4.0 | (not used) | 1 | 1 (total collapse) | -- | -- | -- |

`ell` is the actual grid cell side (eq. 6, `ell = max(kappa*sqrt(A/tau), sigma)`)
for each instance at that kappa -- always far above sigma=240m (rotor
diameter) at every value used, so the sigma floor never binds here (see
`scripts/mowflop/README.md`'s caveats section). The ceiling cliffs sharply
between kappa=2.0 and kappa=3.0, which is why 2.0 is the coarsest of the
three regimes actually used -- one step further and `ns48` would collapse
to double digits regardless of how many raw solutions it visits.

Reproduce the ceiling column:

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
