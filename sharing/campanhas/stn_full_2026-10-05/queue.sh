#!/usr/bin/env bash
# Runs entropy then grid for one front, one container at a time, and stops on any sign of trouble.
# usage: queue.sh <orig|sparse> <noext|ext> <memory cap> <JOBS>
set -uo pipefail
fam=$1 front=$2 mem=$3 jobs=$4
W=$HOME/stn_full_2026-10-05
Q=$W/queue_${front}_${fam}.log
for scheme in entropy grid; do
  name=stn_${front}_${scheme}_${fam}
  camp=$HOME/STNs-MOCO-MoWFLOP/campanhas/full_${front}_${scheme}_${fam}_2026-10-05
  echo "$(date -Is) start $name" >> "$Q"
  "$W/launch.sh" "$fam" "$front" "$scheme" "$mem" "$jobs" >> "$Q" 2>&1 || { echo "$(date -Is) STOP: launch failed" >> "$Q"; exit 1; }
  rc=$(podman wait "$name")
  oom=$(podman inspect "$name" --format '{{.State.OOMKilled}}')
  png=$(find "$camp/plots" -name '*.png' 2>/dev/null | wc -l)
  zero=$(find "$camp/plots" -name '*.png' -size 0 2>/dev/null | wc -l)
  done_plot=$(find "$camp/status" -name .done_plot 2>/dev/null | wc -l)
  echo "$(date -Is) end $name rc=$rc oom=$oom png=$png zero_png=$zero done_plot=$done_plot/6" >> "$Q"
  if [[ "$rc" != 0 || "$oom" != false || "$zero" != 0 || "$done_plot" != 6 ]]; then
    echo "$(date -Is) STOP: check $name before continuing" >> "$Q"; exit 1
  fi
done
echo "$(date -Is) queue done" >> "$Q"
