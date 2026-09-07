#!/usr/bin/env bash
# Roda o pipeline partition.py -> run_scripts/run_create_r.py ->
# run_scripts/run_plot_r.py -> run_scripts/run_stn_metrics_r.py (MOEAD e
# NSGA2) -> run_scripts/run_shared_alg_r.py para as três variantes de STN
# pedidas pelo professor, cruzadas com os três esquemas de particionamento.
# Mesmo idioma do run_entropy_campaign.sh: um `nohup ... &> log &` por unidade
# de trabalho, sem scheduler; as etapas de uma variante formam uma cadeia
# (cada uma precisa da saída da anterior) e rodam em sequência dentro do seu
# próprio processo, só as variantes entre si é que rodam em paralelo.
#
# As variantes (ver mowflop/partition.py:datasets_to_emit e mowflop/wind.py):
#
#   agg-raw    agregada, escala bruta.  A linha de base histórica: une as 10
#              runs numa frente só, ou seja, une CENÁRIOS DE VENTO DIFERENTES.
#              É o comportamento que reports/frente_referencia_vento.md
#              documenta como quebrado -- mantido para comparação.
#   agg-norm   agregada, f_power na régua do cenário de cada run.  As faixas
#              horizontais colapsam umas sobre as outras.       (caso 1)
#   run-raw    uma STN por cenário, escala bruta.               (caso 3)
#   run-norm   uma STN por cenário, normalizada.  Mesmo grafo da run-raw (a
#              normalização é afim dentro de uma run), mas todas no eixo
#              [1, 2] e portanto comparáveis entre si.          (caso 2)
#
# Cada variante x esquema tem a sua própria tag, e a tag é o único eixo que o
# lado R enxerga (data/mowflop_<tag>/, stns/, plots/), então o R roda sem
# alteração. Ex.: entropy x agg-norm -> x80norm; grid x run-norm -> g2.0runnorm.
#
# Idempotente por etapa, como o run_entropy_campaign.sh: um marcador em
# status/<tag>/.done_<stage> é criado só depois que a etapa termina com
# sucesso, então relançar o script pula o que já terminou. Se o código de uma
# etapa anterior mudou, apague o status/<tag>/ inteiro.
#
# Uso (a partir de scripts/): ./run_stn_variants.sh [esquemas] [variantes] [instância]
# Ex.: ./run_stn_variants.sh                                      # tudo
#      ./run_stn_variants.sh entropy "agg-norm run-norm" ns178    # o piloto
#      ./run_stn_variants.sh "entropy grid raw" agg-norm          # uma variante, 3 esquemas
#
# PERCENT (entropy) e KAPPA (grid) saem das variáveis de ambiente de mesmo
# nome do partition.py; os defaults abaixo valem se não estiverem setadas.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"   # scripts/

schemes="${1:-entropy grid raw}"
variants="${2:-agg-raw agg-norm run-raw run-norm}"
instance="${3:-}"        # vazio = todas as instâncias (MOWFLOP_ALL=1)

percent="${MOWFLOP_PERCENT:-80}"
kappa="${MOWFLOP_KAPPA:-2.0}"
layout="${LAYOUT:-of}"   # of | fd | both -- "fd" é lento e vira bola de lã

mkdir -p ../logs ../status

for scheme in $schemes; do
  case "$scheme" in
    entropy|grid|raw) ;;
    *) echo "esquema desconhecido: $scheme" >&2; exit 1 ;;
  esac

  for variant in $variants; do
    case "$variant" in
      agg-raw)  per_run=0; normalize=0 ;;
      agg-norm) per_run=0; normalize=1 ;;
      run-raw)  per_run=1; normalize=0 ;;
      run-norm) per_run=1; normalize=1 ;;
      *) echo "variante desconhecida: $variant" >&2; exit 1 ;;
    esac

    # a tag vem do próprio partition.py (mowflop.partition.current_tag), nunca
    # remontada aqui -- é a única forma de as etapas do R olharem exatamente a
    # pasta em que o partition.py escreveu
    tag=$(MOWFLOP_SCHEME="$scheme" MOWFLOP_PERCENT="$percent" MOWFLOP_KAPPA="$kappa" \
          MOWFLOP_PER_RUN="$per_run" MOWFLOP_NORMALIZE="$normalize" \
          ../.venv/bin/python -c \
          "from mowflop.partition import current_tag; print(current_tag())")
    log="../logs/stn_${tag}.log"
    status_dir="../status/${tag}"
    mkdir -p "$status_dir"

    nohup bash -c '
      set -euo pipefail
      scheme="$1"; tag="$2"; status_dir="$3"; layout="$4"
      per_run="$5"; normalize="$6"; percent="$7"; kappa="$8"; instance="$9"

      export MOWFLOP_SCHEME="$scheme" MOWFLOP_PERCENT="$percent" MOWFLOP_KAPPA="$kappa"
      export MOWFLOP_PER_RUN="$per_run" MOWFLOP_NORMALIZE="$normalize"
      # partition.py com ALL=0 processa um par (instância, config) por chamada,
      # então restringir a uma instância é um laço sobre as 3 configs
      if [[ -n "$instance" ]]; then
        export MOWFLOP_ALL=0 MOWFLOP_INSTANCE="$instance"
      else
        export MOWFLOP_ALL=1
      fi

      if [[ ! -f "$status_dir/.done_partition" ]]; then
        echo "[partition] scheme=$scheme tag=$tag per_run=$per_run normalize=$normalize $(date -Is)"
        if [[ -n "$instance" ]]; then
          for cfg in p10_i50 p50_i50 p100_i50; do
            MOWFLOP_CONFIG="$cfg" ../.venv/bin/python -m mowflop.partition
          done
        else
          ../.venv/bin/python -m mowflop.partition
        fi
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
    ' _ "$scheme" "$tag" "$status_dir" "$layout" \
        "$per_run" "$normalize" "$percent" "$kappa" "$instance" &> "$log" &
    echo "[batch] scheme=$scheme variant=$variant tag=$tag pid=$! log=$log"
  done
done

wait
echo "[batch] todas as variantes terminaram"
