#!/usr/bin/env bash
# Roda o pipeline partition.py -> run_scripts/run_create_r.py ->
# run_scripts/run_plot_r.py -> run_scripts/run_stn_metrics_r.py (MOEAD e
# NSGA2) -> run_scripts/run_shared_alg_r.py para o esquema entropy, um
# PERCENT de cada vez, no supercomputador. Adapta o
# idioma de STN_MoWFLOP/source_code/meta_heuristics/scripts/batch.sh: um
# `nohup ... &> log &` por unidade de trabalho, sem scheduler, sem limite de
# concorrência. Diferença daquele script: lá cada unidade (instância) é
# independente; aqui as etapas de um mesmo PERCENT formam uma cadeia (cada
# uma precisa da saída da anterior), então cada PERCENT roda suas etapas em
# sequência dentro do seu próprio processo -- só os PERCENTs entre si é que
# rodam em paralelo.
#
# Idempotente por etapa: nenhum desses scripts tem skip interno por
# instância (diferente de run_one.sh), então a granularidade de retomada é
# a etapa inteira -- um marcador em status/x<percent>/.done_<stage> é
# criado só depois que a etapa termina com sucesso. Relançar o script pula o
# que já terminou. Se o código de uma etapa anterior (ex.: partition.py ou
# create .R) mudou desde a última campanha, apagar só o .done_plot/.done_metrics
# não basta -- vale a receita "refazer um PERCENT inteiro do zero" do
# COMO_RODAR_CAMPANHA_ENTROPIA.md (S4).
#
# Uso (a partir de scripts/): ./run_entropy_campaign.sh [percents] [layout] [external_front]
# Ex.: ./run_entropy_campaign.sh                  # 60 70 80, layout both, com wflopcec26
#      ./run_entropy_campaign.sh 60 of            # só x60, só o layout rápido
#      ./run_entropy_campaign.sh "60 70 80" fd    # só o layout força-dirigido
#      ./run_entropy_campaign.sh 80 of 0          # x80noext, sem o histórico do wflopcec26
#
# external_front (default 1): repassado como MOWFLOP_EXTERNAL_FRONT pro
# partition.py (ver reference_front.external_points); 0 sufixa a tag com
# "noext" (x80 -> x80noext), então cai em pastas/status/log próprios --
# nunca sobrescreve a campanha "com" wflopcec26.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"   # scripts/

percents="${1:-60 70 80}"
layout="${2:-both}"   # of | fd | both
external_front="${3:-1}"   # 1 (default, com wflopcec26) | 0 (sem)

mkdir -p ../logs ../status

for percent in $percents; do
  tag="x${percent}"
  if [[ "$external_front" != "1" ]]; then
    tag="${tag}noext"
  fi
  log="../logs/entropy_${tag}.log"
  status_dir="../status/${tag}"
  mkdir -p "$status_dir"
  nohup bash -c '
    set -euo pipefail
    percent="$1"; tag="$2"; layout="$3"; status_dir="$4"; external_front="$5"

    if [[ ! -f "$status_dir/.done_partition" ]]; then
      echo "[partition] scheme=entropy percent=$percent external_front=$external_front $(date -Is)"
      MOWFLOP_SCHEME=entropy MOWFLOP_PERCENT="$percent" MOWFLOP_ALL=1 \
        MOWFLOP_EXTERNAL_FRONT="$external_front" \
        ../.venv/bin/python -m mowflop.partition
      touch "$status_dir/.done_partition"
    else
      echo "[skip] partition já feito para $tag"
    fi

    if [[ ! -f "$status_dir/.done_create" ]]; then
      echo "[create] tag=$tag $(date -Is)"
      ../.venv/bin/python -m mowflop.run_scripts.run_create_r --tag "$tag"
      touch "$status_dir/.done_create"
    else
      echo "[skip] create já feito para $tag"
    fi

    if [[ ! -f "$status_dir/.done_plot" ]]; then
      echo "[plot] tag=$tag layout=$layout $(date -Is)"
      ../.venv/bin/python -m mowflop.run_scripts.run_plot_r --tag "$tag" --layout "$layout"
      touch "$status_dir/.done_plot"
    else
      echo "[skip] plot já feito para $tag"
    fi

    if [[ ! -f "$status_dir/.done_metrics" ]]; then
      echo "[metrics] tag=$tag $(date -Is)"
      ../.venv/bin/python -m mowflop.run_scripts.run_stn_metrics_r --tag "$tag" --algo MOEAD
      ../.venv/bin/python -m mowflop.run_scripts.run_stn_metrics_r --tag "$tag" --algo NSGA2
      ../.venv/bin/python -m mowflop.run_scripts.run_shared_alg_r --tag "$tag"
      touch "$status_dir/.done_metrics"
    else
      echo "[skip] metrics já feito para $tag"
    fi

    echo "[done] tag=$tag $(date -Is)"
  ' _ "$percent" "$tag" "$layout" "$status_dir" "$external_front" &> "$log" &
  echo "[batch] percent=$percent tag=$tag pid=$! log=$log"
done
