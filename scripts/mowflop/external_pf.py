"""Pontos de fora da campanha para a frente de referência (melhor conhecida do grupo).

``reference_front.py`` calcula o não-dominado só sobre o que a nossa própria
campanha logou. Isso é "a melhor frente que os *nossos* MOEA/D e NSGA-II
acharam", não "a melhor frente que o grupo já conhece". Só uma das duas
fontes externas do grupo entra aqui:

- **CEC 2026** (``mowflopcec/wflopcec26``): ``algorithms_raw_results/`` do
  clone em ``external_pf/wflopcec26`` (sparse checkout -- só esse diretório e
  ``instances/``, para não trazer o repo inteiro, ~3GB em vez de ~13GB). Tem
  um terceiro algoritmo, ``COMOLSD``, que não roda em lugar nenhum do nosso
  lado, mas conta para "melhor conhecida do grupo" -- por isso entra aqui
  também. **Verificado, não assumido**: ``instances/sites/<N>/geometry.txt``
  e ``turbines_per_zone.txt`` são idênticos, byte a byte (módulo ``\\r\\n``),
  aos nossos ``STN_MoWFLOP/instances/site/ns<N>/`` para as 10 instâncias que
  temos -- ``<N>`` na CEC é sempre o mesmo site que o nosso ``ns<N>``.
- **BRACIS** (Silva & Fernandes, ``STN_MoWFLOP/raw_results/meta_heuristics/``)
  **foi excluído deliberadamente**: seu ``101`` não é o nosso ``ns101`` --
  faixas de ``f_cost``/``f_power`` completamente diferentes das nossas (custo
  ~4.7x maior, potência ~78x maior), quando a CEC bate quase exatamente com a
  nossa. A numeração do BRACIS vem de um catálogo de instâncias bem maior e
  anterior (dezenas de pastas numéricas em ``meta_heuristics/``, não as 10
  que usamos), sem correspondência 1:1 com o nosso ``ns<N>``. Misturar essa
  fonte teria corrompido a frente de referência silenciosamente.

Cada run despeja um arquivo por checkpoint de geração (``<num>_<algo>_<ger>.txt``).
Como a convergência evolutiva faz gerações intermediárias raramente
contribuírem um ponto não-dominado que a população final não tenha, só o
checkpoint de maior geração por run é lido -- middle ground deliberado entre
"barato" e "capturar praticamente todo ponto real da frente", dado que ler os
~12GB inteiros da CEC só para isso seria desproporcional.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd

from .io_raw import repo_root

INSTANCE_RE = re.compile(r"^ns(\d+)$")

CEC_ALGO_DIRS = {"MOEAD": "MOEAD", "NSGA2": "NSGA2", "COMOLSD": "COMOLSD"}


def instance_number(instance: str) -> str:
    """``"ns101"`` -> ``"101"``: o número que as duas fontes externas usam como nome de instância.

    Args:
        instance: nome da instância no nosso formato (``"ns<N>"``).

    Returns:
        O ``N`` como string.

    Raises:
        ValueError: se ``instance`` não seguir o formato ``ns<N>``.
    """
    m = INSTANCE_RE.match(instance)
    if not m:
        raise ValueError(f"unexpected instance name: {instance!r}")
    return m.group(1)


def cec_root(root: str | os.PathLike | None = None) -> Path:
    """``external_pf/wflopcec26/algorithms_raw_results`` -- as runs do CEC 2026 (``wflopcec26``).

    Args:
        root: caminho explícito que sobrescreve o padrão; se ``None``, tenta
            ``$MOWFLOP_CEC_RAW`` e depois o caminho padrão, irmão deste
            repositório dentro de ``TCC/``.

    Returns:
        Caminho absoluto.

    Raises:
        FileNotFoundError: se nenhum caminho válido for encontrado.
    """
    if root is not None:
        return Path(root).resolve()
    env = os.environ.get("MOWFLOP_CEC_RAW")
    if env:
        return Path(env).resolve()
    path = repo_root().parent / "external_pf" / "wflopcec26" / "algorithms_raw_results"
    if not path.is_dir():
        raise FileNotFoundError(f"CEC raw results not found at {path}")
    return path


def _final_checkpoint(run_dir: Path, num: str, algo_lower: str) -> Path | None:
    """Arquivo de maior geração (``<num>_<algo>_<ger>.txt``) dentro de uma pasta de run.

    Args:
        run_dir: pasta de uma run (``<fonte>/<ALGO>/<num>/<run>/``).
        num: número da instância (nome de arquivo).
        algo_lower: nome do algoritmo em minúsculo, como aparece no arquivo.

    Returns:
        Caminho do checkpoint final, ou ``None`` se nenhum arquivo bater com o padrão.
    """
    pattern = re.compile(rf"^{re.escape(num)}_{re.escape(algo_lower)}_(\d+)\.txt$")
    best_n, best_path = -1, None
    for f in run_dir.iterdir():
        m = pattern.match(f.name)
        if m and int(m.group(1)) > best_n:
            best_n, best_path = int(m.group(1)), f
    return best_path


def _read_points(path: Path) -> list[tuple[float, float]]:
    """Lê um checkpoint (``f_cost f_power`` por linha, sem cabeçalho) como pares."""
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) >= 2:
                out.append((float(parts[0]), float(parts[1])))
    return out


def _source_points(source_root: Path, algo_dirs: dict[str, str], num: str) -> list[tuple[float, float]]:
    """Todo ponto do checkpoint final de toda run, de todo algoritmo, de uma fonte, para uma instância."""
    points = []
    for algo_dir_name in algo_dirs.values():
        inst_dir = source_root / algo_dir_name / num
        if not inst_dir.is_dir():
            continue
        algo_lower = algo_dir_name.lower()
        for run_dir in inst_dir.iterdir():
            if not run_dir.is_dir():
                continue
            final = _final_checkpoint(run_dir, num, algo_lower)
            if final is not None:
                points.extend(_read_points(final))
    return points


def external_points(
    instance: str,
    cec_dir: str | os.PathLike | None = None,
) -> pd.DataFrame:
    """Todo ponto (``f_cost``, ``f_power``) do histórico do grupo (CEC) para uma instância.

    União do checkpoint final de toda run, dos três algoritmos da CEC
    (MOEA/D, NSGA-II, COMOLSD) -- ainda não filtrado pelo não-dominado; passe
    o resultado, concatenado com os pontos da nossa própria campanha, para
    :func:`reference_front.pareto_front`. BRACIS fica de fora -- ver o
    docstring do módulo.

    Args:
        instance: nome da instância (``"ns101"``, ...).
        cec_dir: sobrescreve :func:`cec_root`.

    Returns:
        DataFrame com colunas ``f_cost``, ``f_power``; vazio (sem erro) se a
        CEC não tiver a instância -- ela pode simplesmente não ter sido
        testada por ninguém antes.
    """
    num = instance_number(instance)
    try:
        points = _source_points(cec_root(cec_dir), CEC_ALGO_DIRS, num)
    except FileNotFoundError:
        points = []
    return pd.DataFrame(points, columns=["f_cost", "f_power"])
