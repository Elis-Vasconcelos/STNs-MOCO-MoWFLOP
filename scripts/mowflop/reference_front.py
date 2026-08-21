"""Conjunto de referência de Pareto para uma instância do MoWFLOP.

O ``create .R`` precisa de uma frente de referência para marcar nós com
``Position="Pareto"``, e não existe uma pronta para o MoWFLOP.
:func:`pareto_front` só calcula o não-dominado sobre o que recebe -- é
``partition.py`` quem decide o que entra: nossa própria campanha (os dois
algoritmos, toda run, todo vetor observador, todo registro) *e* o histórico
do grupo (CEC 2026, ``external_pf.external_points`` -- ver o docstring desse
módulo para por que só essa fonte externa entra e não BRACIS), para que a
frente seja a melhor conhecida, não só a melhor que os nossos próprios
MOEA/D e NSGA-II acharam.

Os dois objetivos puxam em direções opostas: ``f_cost`` é minimizado e
``f_power`` maximizado.  É calculado uma vez por instância e reaproveitado em
todo esquema e todo ``z``, o que é o que torna as métricas comparáveis entre
regimes diferentes.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DEC = 6  # casas decimais; deve bater com `dec` em "create .R"
FLOAT_FMT = f"%.{DEC}f"


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
    # ordena por custo crescente (e poder decrescente para desempatar);
    # varrendo nessa ordem, um ponto é não dominado sse supera o melhor poder visto até aqui
    points = points.sort_values([cost, power], ascending=[True, False], ignore_index=True)
    keep = []
    best_power = float("-inf")
    for c, p in points.itertuples(index=False):
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
