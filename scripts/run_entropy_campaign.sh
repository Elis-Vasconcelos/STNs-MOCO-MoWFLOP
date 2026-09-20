#!/usr/bin/env bash
# Roda o pipeline partition.py -> run_scripts/run_create_r.py ->
# run_scripts/run_stn_metrics_r.py (MOEAD e NSGA2) ->
# run_scripts/run_shared_alg_r.py -> partition_metrics.py ->
# run_scripts/run_plot_r.py para o esquema entropy, no supercomputador: STNs
# (.RData), todas as métricas de STN e os plots (of/fd), para cada PERCENT
# (nível de particionamento) e cada tipo de STN (agregada ou por run). Só as
# instâncias ns* e só normalizado.
#
# Adapta o idioma do batch.sh da campanha C++: um `nohup ... &> log &` por
# unidade de trabalho, sem scheduler, sem limite de concorrência. Aqui a
# unidade é o par (PERCENT, variante): as etapas de um par formam uma cadeia
# (cada uma precisa da saída da anterior) e rodam em sequência dentro do seu
# próprio processo -- só os pares entre si é que rodam em paralelo.
#
# Toda a saída cai em campanhas/<CAMPAIGN>/ (via $MOWFLOP_OUT), nunca nas
# pastas data/, stns/, plots/, metrics/... da raiz do repo -- a campanha volta
# para o laptop com um tar só dessa pasta, sem misturar com o que já existe.
#
# Idempotente por etapa: um marcador em campanhas/<CAMPAIGN>/status/<tag>/.done_<stage>
# é criado só depois que a etapa termina com sucesso. Relançar com o mesmo
# CAMPAIGN pula o que já terminou. Se o código de uma etapa anterior mudou,
# use um CAMPAIGN novo (ou apague o status/<tag>/ inteiro).
#
# Uso (a partir de scripts/):
#   [CAMPAIGN=<nome>] ./run_entropy_campaign.sh [percents] [layout] [external_front] [variants]
# Ex.: ./run_entropy_campaign.sh                       # 60 70 80, of+fd, com wflopcec26, agg e run
#      ./run_entropy_campaign.sh 60 of                 # só x60, só o layout rápido
#      ./run_entropy_campaign.sh "60 70 80" fd         # só o layout força-dirigido
#      ./run_entropy_campaign.sh 80 of 0 agg           # x80noextnorm, sem o histórico do wflopcec26
#      CAMPAIGN=entropy_2026-09-18 ./run_entropy_campaign.sh   # retoma essa campanha
#
# CAMPAIGN (default entropy_<hoje>): nome da pasta em campanhas/.
# layout: of | fd | both.
# external_front (default 1): repassado como MOWFLOP_EXTERNAL_FRONT pro
#   partition.py (ver reference_front.external_points); 0 sufixa a tag com
#   "noext" (x80norm -> x80noextnorm).
# JOBS (default 4): figuras desenhadas em paralelo por cadeia (MOWFLOP_JOBS do
#   run_plot_r.py). Com 6 cadeias, ~6 x JOBS núcleos ocupados (24 de 62 no
#   bambu3, ~1 GB de RAM por worker).
# WAIT=1: espera as cadeias terminarem antes de sair -- necessário quando o
#   script é o processo principal de um contêiner (podman run -d), senão o
#   contêiner termina e leva as cadeias junto.
# PYTHON (default ../.venv/bin/python): o Containerfile põe PYTHON=python3.
# variants (default "agg run"): agg = uma STN agregando as runs (x<p>norm);
#   run = uma STN por cenário de vento (x<p>runnorm). As duas normalizadas --
#   as variantes em escala bruta não entram nesta campanha.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"   # scripts/
repo="$(cd .. && pwd)"

percents="${1:-60 70 80}"
layout="${2:-both}"          # of | fd | both
external_front="${3:-1}"     # 1 (default, com wflopcec26) | 0 (sem)
variants="${4:-agg run}"     # agg | run

case "$layout" in
  of|fd|both) ;;
  *) echo "layout desconhecido: $layout (of | fd | both)" >&2; exit 1 ;;
esac
for variant in $variants; do
  case "$variant" in
    agg|run) ;;
    *) echo "variante desconhecida: $variant (agg | run; só normalizado)" >&2; exit 1 ;;
  esac
done

campaign="${CAMPAIGN:-entropy_$(date +%F)}"
out="$repo/campanhas/$campaign"
mkdir -p "$out/logs" "$out/status"

# comuns a todas as cadeias: saída isolada, só ns*, só normalizado
export MOWFLOP_OUT="$out"
export MOWFLOP_INSTANCE_PATTERN='^ns'
export MOWFLOP_SCHEME=entropy MOWFLOP_ALL=1 MOWFLOP_NORMALIZE=1
export MOWFLOP_EXTERNAL_FRONT="$external_front"
export MOWFLOP_JOBS="${JOBS:-4}"
export PYTHON="${PYTHON:-../.venv/bin/python}"

# proveniência: um bloco por lançamento (relançar acrescenta, não apaga)
{
  echo "== lançamento $(date -Is)"
  echo "host:     $(hostname)"
  echo "commit:   $(git -C "$repo" rev-parse --short HEAD 2>/dev/null || echo '?') ($(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?'))"
  git -C "$repo" diff --quiet HEAD 2>/dev/null || echo "AVISO:    árvore com alterações não commitadas"
  echo "percents: $percents"
  echo "layout:   $layout"
  echo "external_front: $external_front"
  echo "variants: $variants"
  echo "jobs:     $MOWFLOP_JOBS por cadeia"
  echo
} >> "$out/CAMPANHA.txt"

for percent in $percents; do
  for variant in $variants; do
    if [[ "$variant" == run ]]; then per_run=1; else per_run=0; fi

    # a tag vem do próprio partition.py (mowflop.partition.current_tag), nunca
    # remontada aqui: é a única forma de as etapas do R olharem exatamente a
    # pasta em que o partition.py escreveu
    tag=$(MOWFLOP_PERCENT="$percent" MOWFLOP_PER_RUN="$per_run" \
          "$PYTHON" -c \
          "from mowflop.partition import current_tag; print(current_tag())")
    log="$out/logs/entropy_${tag}.log"
    status_dir="$out/status/${tag}"
    mkdir -p "$status_dir"

    nohup bash -c '
      set -euo pipefail
      percent="$1"; per_run="$2"; tag="$3"; layout="$4"; status_dir="$5"; out="$6"
      export MOWFLOP_PERCENT="$percent" MOWFLOP_PER_RUN="$per_run"

      if [[ ! -f "$status_dir/.done_partition" ]]; then
        echo "[partition] tag=$tag percent=$percent per_run=$per_run external_front=$MOWFLOP_EXTERNAL_FRONT $(date -Is)"
        "$PYTHON" -m mowflop.partition
        touch "$status_dir/.done_partition"
      else
        echo "[skip] partition já feito para $tag"
      fi

      # partition pode não emitir nada de propósito (ver os [aviso] acima); aí
      # não há o que o R ler, e a cadeia termina limpa
      if [[ -z "$(find "$out/data/mowflop_$tag" -type f -print -quit 2>/dev/null)" ]]; then
        echo "[skip] partition não emitiu nada para $tag; etapas seguintes puladas"
        echo "[done] tag=$tag $(date -Is)"
        exit 0
      fi

      if [[ ! -f "$status_dir/.done_create" ]]; then
        echo "[create] tag=$tag $(date -Is)"
        "$PYTHON" -m mowflop.run_scripts.run_create_r --tag "$tag"
        touch "$status_dir/.done_create"
      else
        echo "[skip] create já feito para $tag"
      fi

      # métricas antes do plot: as três etapas leem só stns/, nenhuma lê plots/,
      # e o plot é o que leva horas. Assim os CSVs -- o produto da campanha --
      # saem nos primeiros minutos, a salvo de uma queda no meio das figuras.
      if [[ ! -f "$status_dir/.done_metrics" ]]; then
        echo "[metrics] tag=$tag $(date -Is)"
        "$PYTHON" -m mowflop.run_scripts.run_stn_metrics_r --tag "$tag" --algo MOEAD
        "$PYTHON" -m mowflop.run_scripts.run_stn_metrics_r --tag "$tag" --algo NSGA2
        "$PYTHON" -m mowflop.run_scripts.run_shared_alg_r --tag "$tag"
        touch "$status_dir/.done_metrics"
      else
        echo "[skip] metrics já feito para $tag"
      fi

      # step_len, R e D: refaz a partição em Python (o R não tem a assinatura
      # nem os objetivos crus de cada nó)
      if [[ ! -f "$status_dir/.done_partition_metrics" ]]; then
        echo "[partition_metrics] tag=$tag $(date -Is)"
        "$PYTHON" -m mowflop.partition_metrics
        touch "$status_dir/.done_partition_metrics"
      else
        echo "[skip] partition_metrics já feito para $tag"
      fi

      # por último, a etapa cara: o run_plot_r.py pula as figuras que já
      # existem, então um relançamento retoma de onde a anterior parou
      if [[ ! -f "$status_dir/.done_plot" ]]; then
        echo "[plot] tag=$tag layout=$layout $(date -Is)"
        "$PYTHON" -m mowflop.run_scripts.run_plot_r --tag "$tag" --layout "$layout"
        touch "$status_dir/.done_plot"
      else
        echo "[skip] plot já feito para $tag"
      fi

      echo "[done] tag=$tag $(date -Is)"
    ' _ "$percent" "$per_run" "$tag" "$layout" "$status_dir" "$out" &> "$log" &
    echo "[batch] percent=$percent variant=$variant tag=$tag pid=$! log=$log"
  done
done

echo
echo "[batch] saída em campanhas/$campaign/"
echo "[batch] para trazer de volta (no laptop, a partir da raiz do repo):"
echo "  ssh -p 4522 <usuario>@<host> 'tar czf - -C ~/STNs-MOCO-MoWFLOP campanhas/$campaign' | tar xzf -"

if [[ "${WAIT:-0}" == 1 ]]; then
  echo "[batch] WAIT=1: esperando as cadeias terminarem"
  wait
  echo "[batch] todas as cadeias terminaram $(date -Is)"
fi
