#!/usr/bin/env bash
# Roda o pipeline partition.py -> run_scripts/run_create_r.py ->
# run_scripts/run_plot_r.py para o esquema entropy, um PERCENT de cada vez,
# no supercomputador. Adapta o
# idioma de STN_MoWFLOP/source_code/meta_heuristics/scripts/batch.sh: um
# `nohup ... &> log &` por unidade de trabalho, sem scheduler, sem limite de
# concorrência. Diferença daquele script: lá cada unidade (instância) é
# independente; aqui as 3 etapas de um mesmo PERCENT formam uma cadeia
# (create.R precisa da saída do partition.py, plot.R precisa da saída do
# create.R), então cada PERCENT roda suas 3 etapas em sequência dentro do seu
# próprio processo -- só os PERCENTs entre si é que rodam em paralelo.
#
# Idempotente por etapa: partition.py/create.R/plot.R não têm skip interno
# por instância (diferente de run_one.sh), então a granularidade de retomada
# é a etapa inteira -- um marcador em status/x<percent>/.done_<stage> é
# criado só depois que a etapa termina com sucesso. Relançar o script pula o
# que já terminou.
#
# Uso (a partir de scripts/): ./run_entropy_campaign.sh [percents] [layout]
# Ex.: ./run_entropy_campaign.sh                # 60 70 80, layout both
#      ./run_entropy_campaign.sh 60 of          # só x60, só o layout rápido
#      ./run_entropy_campaign.sh "60 70 80" fd  # só o layout força-dirigido

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"   # scripts/

percents="${1:-60 70 80}"
layout="${2:-both}"   # of | fd | both

mkdir -p ../logs ../status

for percent in $percents; do
  tag="x${percent}"
  log="../logs/entropy_${tag}.log"
  status_dir="../status/${tag}"
  mkdir -p "$status_dir"
  nohup bash -c '
    set -euo pipefail
    percent="$1"; tag="$2"; layout="$3"; status_dir="$4"

    if [[ ! -f "$status_dir/.done_partition" ]]; then
      echo "[partition] scheme=entropy percent=$percent $(date -Is)"
      MOWFLOP_SCHEME=entropy MOWFLOP_PERCENT="$percent" MOWFLOP_ALL=1 \
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

    echo "[done] tag=$tag $(date -Is)"
  ' _ "$percent" "$tag" "$layout" "$status_dir" &> "$log" &
  echo "[batch] percent=$percent tag=$tag pid=$! log=$log"
done
