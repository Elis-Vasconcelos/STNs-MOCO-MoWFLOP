# Ambiente da campanha de STN (Python + R) para servidores sem sudo, via podman.
# Só pacotes do apt do Debian trixie -- mesmas versões de igraph/pandas do laptop.
#
#   podman build -t mowflop-stn .
#
# O repo não entra na imagem: é montado em /repo no `podman run`
FROM docker.io/library/debian:trixie

RUN apt-get update && apt-get install -y --no-install-recommends \
      r-base-core r-cran-igraph r-cran-dplyr r-cran-tidyr r-cran-ggplot2 \
      r-cran-ggraph r-cran-tidygraph r-cran-rcolorbrewer r-cran-reshape2 \
      python3 python3-pandas python3-numpy python3-matplotlib python3-scipy \
      git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# run_entropy_campaign.sh usa $PYTHON no lugar de ../.venv/bin/python
ENV PYTHON=python3
