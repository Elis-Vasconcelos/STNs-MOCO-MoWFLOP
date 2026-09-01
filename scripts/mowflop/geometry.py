"""Geometria da instância para a fórmula de calibração de kappa (STN_MoWFLOP.pdf, S7).

Lê arquivos de instância do repositório STN_MoWFLOP (irmão deste, não versão
deste repo): ``geometry.txt`` (polígono do contorno do parque) e
``turbines_per_zone.txt`` (tau).  ``$MOWFLOP_INSTANCES`` sobrescreve a raiz;
senão usa ``../STN_MoWFLOP/instances/site`` relativo à raiz deste repo.

sigma (o piso de ell na eq. 6, ``ell >= sigma``) é o espaçamento mínimo entre
turbinas -- a restrição d_ij <= sigma do BRACIS 2025 e do Silva & Fernandes.
Nenhum dos dois papers publica um valor numérico, só a definem
simbolicamente; e o código C++ da campanha (source_code/meta_heuristics) não
tem *nenhuma* checagem de distância mínima em tempo de execução --
`calculate_interference` só usa o diâmetro do rotor (240m, hardcoded em
generate_rSolution.cpp) pro modelo de esteira de Jensen, nunca pra rejeitar
um par de posições candidatas por estarem perto demais.

Medimos também o espaçamento real da grade de candidatos (nearest-neighbor
euclidiano, não só diferença de eixo): ~159.6m pra ns101, *menor* que o
diâmetro do rotor (240m). Ou seja, a grade **não** é pré-espaçada para
respeitar essa distância "de graça" -- ao contrário do que
`landscape-mo/CLAUDE.md` supõe --, e dois candidatos adjacentes podem gerar
rotores fisicamente sobrepostos sem que nada no código impeça isso. Usamos
``ROTOR_DIAMETER`` (240m) como sigma por ser a única distância fisicamente
significativa presente no código, não o espaçamento da grade (exposto à
parte em ``SiteGeometry.candidate_spacing``, só como diagnóstico). Vale
revisar no estudo se essa lacuna é uma omissão do fork ou decisão deliberada
dos autores originais -- e se 1xD é o multiplicador certo ou se a literatura
sugere algo maior (3-5xD é comum).
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

from .io_raw import load_candidates, repo_root


def instances_root(root: str | os.PathLike | None = None) -> Path:
    """Raiz de ``instances/site`` no STN_MoWFLOP.

    Args:
        root: caminho explícito que sobrescreve o padrão; se ``None``, tenta
            ``$MOWFLOP_INSTANCES`` e depois ``../STN_MoWFLOP/instances/site``.

    Returns:
        Caminho absoluto da raiz das instâncias.

    Raises:
        FileNotFoundError: se nenhum caminho válido for encontrado.
    """
    if root is not None:
        return Path(root).resolve()
    env = os.environ.get("MOWFLOP_INSTANCES")
    if env:
        return Path(env).resolve()
    path = (repo_root() / ".." / "STN_MoWFLOP" / "instances" / "site").resolve()
    if not path.is_dir():
        raise FileNotFoundError(
            f"instance geometry not found at {path}; "
            "set MOWFLOP_INSTANCES or pass root explicitly"
        )
    return path


def _polygon_points(path: Path) -> list[tuple[float, float]]:
    points = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        x, y = line.split()[:2]
        points.append((float(x), float(y)))
    # geometry.txt repete o primeiro ponto no fim, pra fechar o polígono
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    return points


def polygon_area(points: list[tuple[float, float]]) -> float:
    """Área de um polígono simples pela fórmula do shoelace.

    Args:
        points: vértices do polígono, em ordem (sem repetir o primeiro no fim).

    Returns:
        Área em unidades ao quadrado das coordenadas de entrada.
    """
    n = len(points)
    total = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


@dataclass
class SiteGeometry:
    """Geometria de uma instância, para a fórmula de calibração (eq. 6)."""

    A: float  # área útil do parque (m^2), shoelace sobre geometry.txt
    W: float  # largura da caixa delimitadora (m)
    H: float  # altura da caixa delimitadora (m)
    xmin: float
    ymin: float
    tau: int  # número de turbinas móveis (soma de turbines_per_zone.txt)
    sigma: float  # piso de ell (eq. 6) -- ver ROTOR_DIAMETER
    candidate_spacing: float  # diagnóstico: espaçamento real da grade de candidatos


# Diâmetro do rotor das turbinas móveis, hardcoded em
# generate_rSolution.cpp:163 (`t.diameter = 240`), reference NREL-15-240.
# É a única distância fisicamente significativa presente no código -- os
# papers (BRACIS 2025, Silva & Fernandes) definem sigma como "um múltiplo do
# diâmetro do rotor" sem publicar o multiplicador; usamos aqui o próprio
# diâmetro (multiplicador 1) como piso conservador mínimo, não uma
# calibração fina do multiplicador real usado por Cazzaro & Pisinger.
#
# Importante: para ns101, o espaçamento real da grade de candidatos é
# ~159.6m (nearest-neighbor euclidiano medido, não só a diferença de eixo),
# menor que este diâmetro (240m) -- ou seja, a grade NÃO é pré-espaçada
# para respeitar essa distância "de graça", ao contrário do que
# landscape-mo/CLAUDE.md supõe: dois candidatos adjacentes podem ambos ser
# ocupados e gerar rotores com sobreposição física, e nada no código C++
# impede isso (ver docstring do módulo). Ponto a revisar/mencionar no
# estudo -- é uma lacuna real do pipeline upstream, não um bug nosso.
ROTOR_DIAMETER = 240.0


def estimate_candidate_spacing(instance: str, root: str | os.PathLike | None = None) -> float:
    """Espaçamento real da grade de candidatos (diagnóstico, não usado como sigma).

    Distância euclidiana ao vizinho mais próximo, por força bruta, calculada
    **separadamente dentro de cada zona** e depois combinada com um mínimo --
    zonas são áreas geograficamente distintas do parque (ver
    ``candidates.csv``'s coluna ``zone``), então combinar as coordenadas de
    todas antes de medir distância mistura pares de candidatos que nunca
    estão fisicamente próximos, mesmo que suas coordenadas coincidam por
    acaso num eixo (ex.: ns203, duas zonas -- combinar dava ~0.34m, um
    artefato; por zona dá o valor real).

    Args:
        instance: nome da instância.
        root: raiz da campanha (candidatos); ver :func:`mowflop.io_raw.raw_root`.

    Returns:
        Menor distância entre vizinhos mais próximos, entre todas as zonas.
        Verificado para ``ns101`` (zona única): 159.598m, idêntico ao valor
        que o método anterior (diferença de eixo, sem separar zonas) dava
        para essa instância -- a correção só muda o resultado quando há mais
        de uma zona.

    Raises:
        ValueError: se nenhuma zona tiver ao menos dois candidatos.
    """
    import numpy as np

    candidates = load_candidates(instance, root=root)
    best = math.inf
    for _, zone_df in candidates.groupby("zone"):
        xy = zone_df[["x", "y"]].to_numpy()
        n = len(xy)
        if n < 2:
            continue
        chunk = 500
        for i in range(0, n, chunk):
            d = np.sqrt(((xy[i : i + chunk, None, :] - xy[None, :, :]) ** 2).sum(-1))
            for local_i in range(d.shape[0]):
                gi = i + local_i
                row = d[local_i].copy()
                row[gi] = np.inf
                best = min(best, float(row.min()))
    if not math.isfinite(best):
        raise ValueError(f"could not estimate spacing for {instance}: every zone has <2 candidates")
    return best


def load_site_geometry(
    instance: str,
    instances_root_: str | os.PathLike | None = None,
    candidates_root: str | os.PathLike | None = None,
) -> SiteGeometry:
    """Geometria completa de uma instância, pronta para a eq. 6.

    Args:
        instance: nome da instância.
        instances_root_: raiz de ``instances/site``; ver :func:`instances_root`.
        candidates_root: raiz da campanha (candidatos); ver
            :func:`mowflop.io_raw.raw_root`.

    Returns:
        :class:`SiteGeometry` com ``A``, ``W``, ``H``, ``tau`` e ``sigma``.
    """
    base = instances_root(instances_root_)
    points = _polygon_points(base / instance / "geometry.txt")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    A = polygon_area(points)

    tau_path = base / instance / "turbines_per_zone.txt"
    tau = sum(int(tok) for tok in tau_path.read_text(encoding="utf-8").split())

    candidate_spacing = estimate_candidate_spacing(instance, root=candidates_root)

    return SiteGeometry(
        A=A, W=max(xs) - min(xs), H=max(ys) - min(ys),
        xmin=min(xs), ymin=min(ys), tau=tau, sigma=ROTOR_DIAMETER,
        candidate_spacing=candidate_spacing,
    )


def cell_side(kappa: float, geometry: SiteGeometry) -> float:
    """``ell = kappa * sqrt(A/tau)``, sujeito a ``ell >= sigma`` (eq. 6).

    Args:
        kappa: parâmetro único do modelo (quantos espaçamentos médios cabem
            no lado da célula).
        geometry: geometria da instância (ver :func:`load_site_geometry`).

    Returns:
        Lado da célula ``ell``, em metros.

    Raises:
        ValueError: se ``kappa`` não for positivo.
    """
    if kappa <= 0:
        raise ValueError(f"kappa must be > 0, got {kappa}")
    return max(kappa * math.sqrt(geometry.A / geometry.tau), geometry.sigma)
