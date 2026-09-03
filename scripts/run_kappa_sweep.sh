#!/usr/bin/env bash
# Kappa sweep (0.5 / 1.0 / 2.0) x instances (ns101, ns178) x configs (p10/p50/p100_i50)
# for STNs-MOCO-MoWFLOP's grid-partitioning pipeline.
#
# Run from inside STNs-MOCO-MoWFLOP/scripts/. Reads the wind-corrected
# campaign logs from this repo's own raw_results/meta_heuristics_stn_windcorrected/
# (the pipeline default). Override with MOWFLOP_RAW=<path> if the logs live
# elsewhere.

set -euo pipefail

export MOWFLOP_RAW="${MOWFLOP_RAW:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/raw_results/meta_heuristics_stn_windcorrected}"

if [ ! -d "$MOWFLOP_RAW" ]; then
  echo "MOWFLOP_RAW not found at $MOWFLOP_RAW -- set MOWFLOP_RAW to the campaign-log root and rerun" >&2
  exit 1
fi

echo "=== resources on this node ==="
nproc
free -h
echo "==============================="

JOBS="${JOBS:-$(( $(nproc) - 1 ))}"
[ "$JOBS" -lt 1 ] && JOBS=1
echo "using JOBS=$JOBS parallel workers (override with JOBS=n before running this script)"

PY=../.venv/bin/python
INSTANCES=(ns101 ns178)
CONFIGS=(p10_i50 p50_i50 p100_i50)
KAPPAS=(0.5 1.0 2.0)
TAGS=(g0.5 g1.0 g2.0)

# ---- stage 1: partition.py (grid scheme), one call per (instance, config, kappa) ----
# Cheap (pandas + entropy calc), but parallelized anyway since it's independent per combo.
for inst in "${INSTANCES[@]}"; do
  for cfg in "${CONFIGS[@]}"; do
    for k in "${KAPPAS[@]}"; do
      printf '%s\t%s\t%s\n' "$inst" "$cfg" "$k"
    done
  done
done | xargs -P "$JOBS" -L 1 bash -c '
  inst="$1"; cfg="$2"; kappa="$3"
  '"$PY"' -c "
from mowflop import partition as p
p.INSTANCE = \"$inst\"
p.CONFIG = \"$cfg\"
p.SCHEME = \"grid\"
p.KAPPA = $kappa
raise SystemExit(p.main())
"
' _

echo "=== stage 1 (partition) done ==="

# ---- stage 2: create .R per tag/kappa (both algorithms in one call) ----
printf '%s\n' "${TAGS[@]}" | xargs -P "$JOBS" -I{} "$PY" -m mowflop.run_create_r --tag {}

echo "=== stage 2 (create .R) done ==="

# ---- stage 3: metrics.R (per tag x algo) and plot.R (per tag, both layouts) ----
for tag in "${TAGS[@]}"; do
  for algo in MOEAD NSGA2; do
    printf '%s\t%s\n' "$tag" "$algo"
  done
done | xargs -P "$JOBS" -L 1 bash -c '
  "'"$PY"'" -m mowflop.run_metrics_r --tag "$1" --algo "$2"
' _

printf '%s\n' "${TAGS[@]}" | xargs -P "$JOBS" -I{} "$PY" -m mowflop.run_plot_r --tag {} --layout both

echo "=== stage 3 (metrics + plot) done ==="

# ---- stage 4: 2x3 comparison tile per instance (needs all 3 tags' plots done) ----
for inst in "${INSTANCES[@]}"; do
  "$PY" -m mowflop.run_compare_r --instance "$inst" --layout both &
done
wait

echo "=== stage 4 (compare) done -- sweep complete ==="
echo "outputs: ../data, ../pf, ../locations, ../stns, ../metrics, ../plots (under STNs-MOCO-MoWFLOP/)"
