"""Particionamento do espaço de busca por grade de ocupação (STN_MoWFLOP.pdf, S6-7).

Definição 1 (assinatura de ocupação): sobrepõe uma grade regular de lado
``ell`` à área do parque e conta quantas turbinas do layout caem em cada
célula.  Definição 2 (localização induzida): duas soluções compartilham
localização sse têm a mesma assinatura ``o_ell``.

``kappa`` é o único parâmetro do modelo (S7): ``ell = max(kappa*sqrt(A/tau),
sigma)`` (eq. 6) -- ver :mod:`mowflop.geometry`.

Diferente de ``entropy.EntropyScheme`` (que projeta a solução num subconjunto
de posições retidas), aqui a "projeção" é a assinatura esparsa
``{célula: contagem}``, só com células ocupadas -- suficiente porque tau é
pequeno perto do número de células ``G``, então guardar um vetor denso de
tamanho ``G`` por localização seria desperdício.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from hashlib import blake2b

from .entropy import Solution
from .geometry import SiteGeometry, cell_side, load_site_geometry
from .io_raw import load_candidates

LOCATION_PREFIX = "G"

# assinatura esparsa: só as células com pelo menos uma turbina
Signature = frozenset[tuple[int, int]]


def cell_of(x: float, y: float, geometry: SiteGeometry, ell: float, ncols: int) -> int:
    """Id da célula (linha-major) que contém o ponto ``(x, y)``.

    Args:
        x: coordenada x do ponto.
        y: coordenada y do ponto.
        geometry: geometria da instância (para a origem da grade).
        ell: lado da célula.
        ncols: número de colunas da grade.

    Returns:
        Id inteiro da célula, ``row * ncols + col``.
    """
    col = int((x - geometry.xmin) // ell)
    row = int((y - geometry.ymin) // ell)
    return row * ncols + col


def signature(
    solution: Solution,
    coords: dict[int, tuple[float, float]],
    geometry: SiteGeometry,
    ell: float,
    ncols: int,
) -> Signature:
    """Assinatura de ocupação ``o_ell`` de uma solução (Def. 1), em forma esparsa.

    Args:
        solution: conjunto de índices globais de candidatos ocupados.
        coords: índice global -> ``(x, y)`` (ver :func:`mowflop.io_raw.load_candidates`).
        geometry: geometria da instância.
        ell: lado da célula.
        ncols: número de colunas da grade.

    Returns:
        Conjunto congelado de pares ``(célula, contagem)``, só células ocupadas.
    """
    counts: dict[int, int] = {}
    for idx in solution:
        x, y = coords[idx]
        cid = cell_of(x, y, geometry, ell, ncols)
        counts[cid] = counts.get(cid, 0) + 1
    return frozenset(counts.items())


def location_id(sig: Signature) -> str:
    """Id curto e estável para uma localização (assinatura de ocupação).

    Args:
        sig: assinatura esparsa (ver :func:`signature`).

    Returns:
        Id no formato ``"G<16 hex>"``.
    """
    key = ",".join(f"{cell}:{count}" for cell, count in sorted(sig))
    digest = blake2b(key.encode("utf-8"), digest_size=8).hexdigest()
    return f"{LOCATION_PREFIX}{digest}"


@dataclass
class GridPartition:
    """Um particionamento por grade de ocupação concreto do espaço de busca de uma instância."""

    instance: str
    geometry: SiteGeometry
    kappa: float
    ell: float
    ncols: int
    nrows: int
    coords: dict[int, tuple[float, float]] = field(repr=False)

    @property
    def n_cells(self) -> int:
        """Número de células da grade pela fórmula do artigo, ``G ~= ceil(A/ell^2)`` (eq. 7).

        Usa a área real do parque (``self.geometry.A``, shoelace sobre
        ``geometry.txt``), não ``ncols * nrows`` -- essa última é derivada da
        caixa delimitadora do polígono, que para sítios irregulares
        (triangulares, com zonas/obstáculos) superestima a área real coberta,
        exatamente a armadilha que o artigo aponta em S10.5 ("a caixa
        envolvente é enganosa"). ``ncols``/``nrows`` continuam existindo só
        como esquema de endereçamento para :func:`cell_of` (linha-major sobre
        a caixa delimitadora) -- um jeito de transformar ``(x, y)`` num id
        inteiro, não uma contagem de células "reais"; nunca são usados para
        alocar ou recortar a grade, que é sempre esparsa.

        Quando ``ell`` não está no piso sigma, isso se reduz algebricamente a
        ``tau / kappa^2`` (a forma da eq. 7 no artigo): ``ell^2 = kappa^2 *
        A/tau``, logo ``A/ell^2 = tau/kappa^2``. Quando o piso sigma *está*
        ativo (``ell = sigma``), esta fórmula em termos de A continua correta;
        a forma ``tau/kappa^2`` não estaria.
        """
        return math.ceil(self.geometry.A / self.ell**2)

    def project(self, solution: Solution) -> Signature:
        """Assinatura de ocupação de uma solução (ver :func:`signature`)."""
        return signature(solution, self.coords, self.geometry, self.ell, self.ncols)

    def assign(self, solution: Solution) -> str:
        """Id da localização em que a solução cai (ver :func:`location_id`)."""
        return location_id(self.project(solution))

    def describe(self) -> dict:
        """Resumo serializável do particionamento, para relatórios e logs.

        Returns:
            Dicionário com as estatísticas do particionamento.
        """
        return {
            "scheme": "grid",
            "kappa": self.kappa,
            "ell": self.ell,
            "sigma": self.geometry.sigma,
            "candidate_spacing": self.geometry.candidate_spacing,
            "ell_at_sigma_floor": abs(self.ell - self.geometry.sigma) < 1e-9,
            "A": self.geometry.A,
            "tau": self.geometry.tau,
            "W": self.geometry.W,
            "H": self.geometry.H,
            "n_cells": self.n_cells,
            "ncols": self.ncols,
            "nrows": self.nrows,
        }


def build_partition(
    instance: str,
    kappa: float,
    instances_root: str | os.PathLike | None = None,
    candidates_root: str | os.PathLike | None = None,
) -> GridPartition:
    """Constrói o particionamento por grade de ocupação de uma instância.

    Args:
        instance: nome da instância.
        kappa: parâmetro único do modelo (eq. 6).
        instances_root: raiz de ``instances/site``; ver
            :func:`mowflop.geometry.instances_root`.
        candidates_root: raiz da campanha (candidatos); ver
            :func:`mowflop.io_raw.raw_root`.

    Returns:
        O :class:`GridPartition` resultante.
    """
    geometry = load_site_geometry(
        instance, instances_root_=instances_root, candidates_root=candidates_root
    )
    ell = cell_side(kappa, geometry)
    ncols = max(1, math.ceil(geometry.W / ell))
    nrows = max(1, math.ceil(geometry.H / ell))
    candidates = load_candidates(instance, root=candidates_root)
    coords = {
        int(row.global_index): (float(row.x), float(row.y))
        for row in candidates.itertuples()
    }
    return GridPartition(
        instance=instance, geometry=geometry, kappa=kappa,
        ell=ell, ncols=ncols, nrows=nrows, coords=coords,
    )
