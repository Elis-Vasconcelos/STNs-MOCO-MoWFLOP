"""Conjunto de referência de Pareto para uma instância do MoWFLOP.

O ``create .R`` precisa de uma frente de referência para marcar nós com
``Position="Pareto"``, e não existe uma pronta para o MoWFLOP.
:func:`pareto_front` só calcula o não-dominado sobre o que recebe -- é
``partition.py`` quem decide o que entra: nossa própria campanha (os dois
algoritmos, toda run, todo vetor observador, todo registro) *e* o histórico
do grupo (:func:`external_points`), para que a frente seja a melhor
conhecida, não só a melhor que os nossos próprios MOEA/D e NSGA-II acharam.

Os dois objetivos puxam em direções opostas: ``f_cost`` é minimizado e
``f_power`` maximizado.  É calculado uma vez por instância e reaproveitado em
todo esquema e todo ``z``, o que é o que torna as métricas comparáveis entre
regimes diferentes.

:func:`external_points` lê os resultados de MOEA/D e NSGA-II do grupo
(``wflopcec26``), vendorizados em ``raw_results/wflopcec26/<algo>/
<instância>/`` (pastas de instância já renomeadas para o nosso ``ns<N>``, não
só o que os nossos próprios algoritmos acharam). Cada run despeja um arquivo
por checkpoint de geração (``..._<algo>_<ger>.txt``); só o checkpoint de
maior geração por run é lido.

:func:`own_archive_points` lê o equivalente da nossa própria campanha
(``raw_results/meta_heuristics_stn/<algo>/<instância>/<config>/<run>/``). É o
conjunto aproximativo (``pareto``, um ``BoundedParetoSet`` acumulado desde a
primeira avaliação -- ``pareto->addSol`` em todo filho gerado por
crossover/mutação, ver ``STN_MoWFLOP/source_code/meta_heuristics/src/
global_modules/genetic_operators/``), não a população corrente amostrada em
``<instância>_<algo>_stn.csv`` (essa é uma foto parcial da busca a cada
``STN_LOGGER_INTERVAL`` gerações, via ``select_representatives`` em
``stn_logger.cpp`` -- usada por ``emit.py`` pra montar a trajetória/STN, mas
não deve alimentar a frente de referência).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .io_raw import raw_root, repo_root

DEC = 6  # casas decimais; deve bater com `dec` em "create .R"
FLOAT_FMT = f"%.{DEC}f"

ALGO_DIRS = {"MOEAD": "moead", "NSGA2": "nsga2"}
WFLOPCEC26_ROOT = repo_root() / "raw_results" / "wflopcec26"


def _final_checkpoint(run_dir: Path, algo_lower: str) -> Path | None:
    """Arquivo de maior geração (``<algo>_<ger>.txt``) dentro de uma pasta de run.

    Args:
        run_dir: pasta de uma run (``<fonte>/<algo>/<instância>/<run>/``).
        algo_lower: nome do algoritmo em minúsculo, como aparece no arquivo.

    Returns:
        Caminho do checkpoint final, ou ``None`` se nenhum arquivo bater com o padrão.
    """
    pattern = re.compile(rf"_{re.escape(algo_lower)}_(\d+)\.txt$")
    best_n, best_path = -1, None
    for f in run_dir.iterdir():
        m = pattern.search(f.name)
        if m and int(m.group(1)) > best_n:
            best_n, best_path = int(m.group(1)), f
    return best_path


def external_points(instance: str) -> pd.DataFrame:
    """Todo ponto (``f_cost``, ``f_power``) do histórico do grupo (wflopcec26) para uma instância.

    União do checkpoint final de toda run, de MOEA/D e NSGA-II, lidos de
    ``raw_results/wflopcec26/<algo>/<instance>/`` -- ainda não
    filtrado pelo não-dominado; passe o resultado, concatenado com os pontos
    da nossa própria campanha, para :func:`pareto_front`.

    Args:
        instance: nome da instância (``"ns101"``, ...).

    Returns:
        DataFrame com colunas ``f_cost``, ``f_power``; vazio (sem erro) se a
        instância, o algoritmo ou a raiz não existirem.
    """
    points = []
    for algo_dir_name in ALGO_DIRS.values():
        inst_dir = WFLOPCEC26_ROOT / algo_dir_name / instance
        if not inst_dir.is_dir():
            continue
        for run_dir in inst_dir.iterdir():
            if not run_dir.is_dir():
                continue
            final = _final_checkpoint(run_dir, algo_dir_name)
            if final is None:
                continue
            # lê um checkpoint (`f_cost f_power` por linha, sem cabeçalho) como pares
            with final.open(encoding="utf-8") as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) >= 2:
                        points.append((float(parts[0]), float(parts[1])))
    return pd.DataFrame(points, columns=["f_cost", "f_power"])


def own_archive_points(
    instance: str, config: str, root: str | None = None
) -> pd.DataFrame:
    """Todo ponto (``f_cost``, ``f_power``) do conjunto aproximativo da própria campanha.

    Espelha :func:`external_points`, mas para ``raw_results/meta_heuristics_stn``
    (um nível a mais de pasta que o wflopcec26, porque aqui existe ``config``
    -- p10/p50/p100 são execuções independentes, não a mesma busca com
    amostragem diferente). União do checkpoint final de toda run, de MOEA/D e
    NSGA-II -- ainda não filtrado pelo não-dominado; passe o resultado,
    concatenado com :func:`external_points`, para :func:`pareto_front`.

    Args:
        instance: nome da instância (``"ns101"``, ...).
        config: config no formato ``p<P>_i<k>``.
        root: raiz explícita da campanha; se ``None``, usa
            :func:`mowflop.io_raw.raw_root` (respeita ``$MOWFLOP_RAW``).

    Returns:
        DataFrame com colunas ``f_cost``, ``f_power``; vazio (sem erro) se a
        instância, o config, o algoritmo ou a raiz não existirem.
    """
    base = raw_root(root)
    points = []
    for algo_dir_name in ALGO_DIRS.values():
        inst_dir = base / algo_dir_name / instance / config
        if not inst_dir.is_dir():
            continue
        for run_dir in inst_dir.iterdir():
            if not run_dir.is_dir():
                continue
            final = _final_checkpoint(run_dir, algo_dir_name)
            if final is None:
                continue
            with final.open(encoding="utf-8") as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) >= 2:
                        points.append((float(parts[0]), float(parts[1])))
    return pd.DataFrame(points, columns=["f_cost", "f_power"])


def pareto_front(
    df: pd.DataFrame, cost: str = "f_cost", power: str = "f_power"
) -> pd.DataFrame:
    """Pontos não dominados, minimizando ``cost`` e maximizando ``power``.

    Args:
        df: DataFrame com as colunas ``cost`` e ``power``.
        cost: nome da coluna a minimizar.
        power: nome da coluna a maximizar.

    Returns:
        DataFrame só com os pontos não dominados, colunas ``[cost, power]``.
    """
    points = df[[cost, power]].drop_duplicates()
    # ordena por custo crescente (e potência decrescente para desempatar);
    # varrendo nessa ordem, um ponto é não dominado sse supera o melhor potência visto até aqui
    points = points.sort_values([cost, power], ascending=[True, False], ignore_index=True)
    keep = []
    best_power = float("-inf")
    for c, p in points.itertuples(index=False):
        # até aqui, foram visitados todos os pontos com custo menor que c
        # então p > best_power -> não existe ponto com custo menor que c e potência maior que p
        # logo, (c, p) é não dominado
        if p > best_power:
            keep.append((c, p))
            best_power = p
    return pd.DataFrame(keep, columns=[cost, power])


def front_keys(front: pd.DataFrame, cost: str = "f_cost", power: str = "f_power") -> set[str]:
    """Chaves em string da frente, do mesmo jeito que o ``create .R`` compara valores.

    Args:
        front: frente de referência (ver :func:`pareto_front`).
        cost: nome da coluna de custo.
        power: nome da coluna de potência.

    Returns:
        Conjunto de chaves ``"<custo>_<potência>"``, formatadas com
        :data:`FLOAT_FMT`.
    """
    return {
        f"{FLOAT_FMT % c}_{FLOAT_FMT % p}"
        for c, p in front[[cost, power]].itertuples(index=False)
    }


def write_front(path: str | Path, front: pd.DataFrame) -> Path:
    """Escreve no layout dos ``pf/*_ref.txt`` do repositório: TSV, sem cabeçalho.

    Args:
        path: caminho de saída.
        front: frente de referência a escrever.

    Returns:
        O caminho escrito, como :class:`Path`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    front.to_csv(path, sep="\t", header=False, index=False, float_format=FLOAT_FMT)
    return path
