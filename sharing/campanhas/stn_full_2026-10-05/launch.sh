#!/usr/bin/env bash
# One campaign of Arthur's scripts/run_entropy_campaign.sh (unchanged), in its own container.
# usage: launch.sh <orig|sparse> <noext|ext> <entropy|grid> <memory cap> <JOBS>
set -euo pipefail
fam=$1 front=$2 scheme=$3 mem=$4 jobs=$5
W=$HOME/stn_full_2026-10-05
case $scheme in entropy) levels="60 70 80" ;; grid) levels="0.5 1.0 2.0" ;; *) exit 2 ;; esac
case $front in
  noext) ef=0; extmount=() ;;
  ext)   ef=1; extmount=(-v "$W/wflopcec26_ext:/repo/raw_results/wflopcec26:ro") ;;
  *) exit 2 ;;
esac
podman run -d --name "stn_${front}_${scheme}_${fam}" --userns=keep-id --memory "$mem" \
  -e WAIT=1 -e JOBS="$jobs" -e SCHEME="$scheme" \
  -e CAMPAIGN="full_${front}_${scheme}_${fam}_2026-10-05" -e MOWFLOP_RAW="/work/raw10_${fam}" \
  -v "$HOME/STNs-MOCO-MoWFLOP:/repo" -v "$W:/work" \
  -v "$W/wind_runs0-9:/repo/raw_results/wind_corrected:ro" ${extmount[@]+"${extmount[@]}"} \
  -w /repo/scripts localhost/mowflop-stn ./run_entropy_campaign.sh "$levels" both "$ef" "agg run"
