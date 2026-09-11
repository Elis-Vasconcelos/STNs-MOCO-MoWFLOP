"""Cenário de vento de cada run: o que torna ``f_power`` comparável, ou não.

Cada run da campanha roda sob um par (velocidade, ângulo) diferente, passado
por argv ao binário C++.  Como a potência escala com ``v³``, o ``f_power`` de
runs distintas vive em ordens de grandeza distintas -- em ns178 o máximo vai
de 1.537,4 (4 m/s) a 2.722.764,0 (19 m/s).  Unir pontos de runs diferentes num
mesmo conjunto não dominado é, portanto, unir *problemas* diferentes.

O vento não é logado pela nossa campanha (``infoRun.txt`` só tem geração e
tamanho de grade).  Ele vem do ``log.txt`` das runs do wflopcec26, em
``raw_results/wflopcec26/<algo>/<instância>/<run>/``, e a nossa run ``r``
corresponde à run ``r+1`` de lá.  Essa convenção é uma *premissa*, não um
contrato: ``reports/frente_referencia_vento/check_mapping.py`` a verifica
comparando a potência máxima das duas, e deve ser rodado antes de confiar em
qualquer coisa deste módulo.

A identidade de um cenário é o par ``(vento, ângulo)``, não o índice da run:
em ns41 as runs 3 e 5 rodaram as duas em 7 m/s a 150°, e são o mesmo problema.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import pandas as pd

from .reference_front import (
    ALGO_DIRS,
    WFLOPCEC26_ROOT,
    _final_checkpoint,
    external_points,
    own_archive_points,
    pareto_front,
)

WIND_RE = re.compile(r"^Wind:\s*([\d.]+)\s*$", re.MULTILINE)
ANGLE_RE = re.compile(r"^Angle:\s*([\d.]+)\s*$", re.MULTILINE)

# a nossa run r foi executada com o mesmo cenário da run r + RUN_OFFSET do cec
RUN_OFFSET = 1

Scenario = tuple[float, float]


def _read_log(path: Path) -> Scenario:
    """Lê ``(vento, ângulo)`` de um ``log.txt`` do wflopcec26.

    Args:
        path: caminho do ``log.txt``.

    Returns:
        Par ``(vento, ângulo)``.

    Raises:
        ValueError: se o arquivo não tiver as linhas ``Wind:`` e ``Angle:``.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    wind, angle = WIND_RE.search(text), ANGLE_RE.search(text)
    if wind is None or angle is None:
        raise ValueError(f"no Wind/Angle line in {path}")
    return float(wind.group(1)), float(angle.group(1))


@lru_cache(maxsize=None)
def cec_scenarios(instance: str) -> tuple[tuple[int, float, float], ...]:
    """Cenário de cada run do wflopcec26 para uma instância.

    O ``log.txt`` de MOEA/D e NSGA-II de uma mesma run traz o mesmo cenário,
    então basta o primeiro que existir.

    Args:
        instance: nome da instância (``"ns178"``, ...).

    Returns:
        Tupla de ``(run, vento, ângulo)``, ordenada por ``run``.  Vazia se a
        instância não existir sob ``raw_results/wflopcec26``.
    """
    found: dict[int, Scenario] = {}
    for algo_dir_name in ALGO_DIRS.values():
        inst_dir = WFLOPCEC26_ROOT / algo_dir_name / instance
        if not inst_dir.is_dir():
            continue
        for run_dir in inst_dir.iterdir():
            log = run_dir / "log.txt"
            if run_dir.name.isdigit() and log.is_file():
                # pra cada run associa dois valores float: vento e ângulo
                found.setdefault(int(run_dir.name), _read_log(log))
    return tuple((run, *found[run]) for run in sorted(found))


def scenarios(instance: str) -> dict[int, Scenario]:
    """Cenário de cada run *da nossa* campanha, traduzido das runs do cec.

    Pela convenção ``r -> r - 1``, em que ``r`` é o índice de uma run do
    wflopcec26: a run ``r`` do cec corresponde à nossa run ``r - 1``.

    Args:
        instance: nome da instância (``"ns178"``, ...).

    Returns:
        Mapa ``run da nossa campanha -> (vento, ângulo)``.  Runs do cec sem
        contraparte nossa ficam de fora.
    """
    by_run = {run: (wind, angle) for run, wind, angle in cec_scenarios(instance)}
    return {
        run - RUN_OFFSET: scenario
        for run, scenario in by_run.items()
        if run - RUN_OFFSET >= 0
    }


def cec_runs_of(instance: str, scenario: Scenario) -> list[int]:
    """Runs do cec que rodaram um dado cenário.

    Casar por ``(vento, ângulo)`` -- e não pelo índice -- é o que permite
    aproveitar as runs 11-20 do cec, que não têm contraparte nossa mas podem
    ter caído num cenário que também rodamos.

    Args:
        instance: nome da instância.
        scenario: par ``(vento, ângulo)``.

    Returns:
        Índices das runs do cec com esse cenário, em ordem crescente.
    """
    return [
        run for run, wind, angle in cec_scenarios(instance) if (wind, angle) == scenario
    ]


def _max_power(run_dir: Path, algo_lower: str) -> float:
    """Maior ``f_power`` do checkpoint final de uma pasta de run.

    Args:
        run_dir: pasta da run.
        algo_lower: nome do algoritmo em minúsculo, como aparece no arquivo.

    Returns:
        Maior potência encontrada, ou ``float("-inf")`` se não houver arquivo.
    """
    final = _final_checkpoint(run_dir, algo_lower) if run_dir.is_dir() else None
    if final is None:
        return float("-inf")
    with final.open(encoding="utf-8") as handle:
        values = [float(p[1]) for p in map(str.split, handle) if len(p) >= 2]
    return max(values, default=float("-inf"))


class ScenarioData(NamedTuple):
    """Frente de referência e régua de normalização de um cenário de vento.

    ``lower_power``/``upper_power`` são os extremos de ``f_power``, e
    ``lower_cost``/``upper_cost`` os de ``f_cost``, no *conjunto todo* do
    cenário, não só na frente -- é o que o ``bound.exe`` do professor calcula e
    grava no ``boundddd.out``, e o que o ``normalize.cc`` consome (lá só para
    ``f_power``; ``f_cost`` não depende do vento, mas normalizá-lo pela mesma
    régua por cenário é inofensivo e deixa os dois eixos na mesma escala).
    Como a trajetória logada na STN é uma amostra da população (e não do
    arquivo ``pareto``), ela pode conter pontos piores que qualquer um do
    arquivo -- e aí sai de ``[1, 2]`` depois de normalizada: uma potência
    abaixo do ``lower_power`` cai *abaixo* de 1,0, um custo acima do
    ``upper_cost`` sobe *acima* de 2,0 (é o caso das gerações iniciais, cujo
    custo é pior que o de qualquer ponto do arquivo).  Isso é esperado e
    inofensivo -- a transformação é afim, então nada muda de ordem.

    A régua e a frente são propriedade do *cenário*, não da config nem da run:
    toda ``(config, run)`` que mapeia para o mesmo ``(vento, ângulo)`` recebe o
    mesmo objeto (ver :func:`_scenario_data`).
    """

    scenario: Scenario
    front: pd.DataFrame
    lower_power: float
    upper_power: float
    lower_cost: float
    upper_cost: float

    @staticmethod
    def _normalize(values: pd.Series, lower: float, upper: float) -> pd.Series:
        """Régua afim comum a ``f_cost``/``f_power``, a fórmula do ``normalize.cc:308``.

        Args:
            values: coluna na escala bruta.
            lower: menor valor da coluna no cenário.
            upper: maior valor da coluna no cenário.

        Returns:
            ``1 + (v − lower) / (upper − lower)``, ou 1,0 em toda a coluna se o
            cenário for degenerado (valor constante).
        """
        if upper == lower:
            return pd.Series(1.0, index=values.index)
        return 1.0 + (values - lower) / (upper - lower)

    def normalize_power(self, values: pd.Series) -> pd.Series:
        """Aplica a régua de ``f_power`` deste cenário.

        Args:
            values: coluna de ``f_power`` na escala bruta.

        Returns:
            ``f_power`` normalizada (ver :meth:`_normalize`).
        """
        return self._normalize(values, self.lower_power, self.upper_power)

    def normalize_cost(self, values: pd.Series) -> pd.Series:
        """Aplica a régua de ``f_cost`` deste cenário.

        Args:
            values: coluna de ``f_cost`` na escala bruta.

        Returns:
            ``f_cost`` normalizado (ver :meth:`_normalize`).
        """
        return self._normalize(values, self.lower_cost, self.upper_cost)

    def normalize_objectives(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Cópia de ``frame`` com ``f_cost`` e ``f_power`` na régua deste cenário.

        Vale tanto para a frente do cenário quanto para a trajetória de uma run
        dele: a régua é a mesma, e aplicá-la aos dois é o que os põe no mesmo
        eixo.

        Args:
            frame: tabela com colunas ``f_cost`` e ``f_power`` na escala bruta.

        Returns:
            Cópia de ``frame`` com os dois objetivos normalizados.
        """
        return frame.assign(
            f_cost=self.normalize_cost(frame["f_cost"]),
            f_power=self.normalize_power(frame["f_power"]),
        )


@lru_cache(maxsize=None)
def _scenario_data(instance: str, external: bool = True) -> dict[Scenario, ScenarioData]:
    """Régua e frente de cada cenário de vento da instância, uma por ``(vento, ângulo)``.

    A régua (min/max de cada objetivo) e a frente de um cenário são propriedade
    do *problema* -- o par ``(vento, ângulo)`` -- não da config, da run ou da
    campanha que o amostrou.  O conjunto de pontos de um cenário une, sem
    distinguir config nem run:

    - todo ponto do arquivo aproximativo da nossa campanha cuja run mapeia para
      aquele ``(vento, ângulo)``, varrendo as três configs e os dois algoritmos
      (:func:`mowflop.reference_front.own_archive_points` com ``config=None``);
    - todo ponto do wflopcec26 cuja run rodou aquele mesmo ``(vento, ângulo)``,
      inclusive as runs 11-20 sem contraparte nossa (:func:`cec_runs_of`).

    ``min``/``max`` de cada objetivo saem desse conjunto uma vez; a frente é o
    não dominado dele.  Unir runs de ventos diferentes é o que hoje produz uma
    frente inatingível por construção (ver
    ``reports/frente_referencia_vento.md``).

    Args:
        instance: nome da instância.
        external: se ``False``, ignora o wflopcec26 (mesmo sentido de
            ``MOWFLOP_EXTERNAL_FRONT`` em :mod:`mowflop.partition`).

    Returns:
        Mapa ``(vento, ângulo) -> ScenarioData``, um por cenário que a nossa
        campanha rodou.  Não mutar o resultado -- é memoizado.
    """
    ours = own_archive_points(instance, config=None)
    theirs = (
        external_points(instance)
        if external
        else pd.DataFrame(columns=["f_cost", "f_power", "run"])
    )
    our_scenario = scenarios(instance)

    out: dict[Scenario, ScenarioData] = {}
    for scenario in sorted(set(our_scenario.values())):
        our_runs = [run for run, s in our_scenario.items() if s == scenario]
        points = pd.concat(
            [
                ours[ours["run"].isin(our_runs)],
                theirs[theirs["run"].isin(cec_runs_of(instance, scenario))],
            ],
            ignore_index=True,
        )
        if points.empty:
            raise ValueError(f"no points for {instance} scenario {scenario}")
        out[scenario] = ScenarioData(
            scenario=scenario,
            front=pareto_front(points),
            lower_power=float(points["f_power"].min()),
            upper_power=float(points["f_power"].max()),
            lower_cost=float(points["f_cost"].min()),
            upper_cost=float(points["f_cost"].max()),
        )
    return out


def scenario_fronts(instance: str, external: bool = True) -> dict[int, ScenarioData]:
    """Régua e frente por cenário de vento, indexadas pela run da nossa campanha.

    Fina camada sobre :func:`_scenario_data`: cada run nossa aponta para a
    ``ScenarioData`` do seu cenário, então runs que compartilham
    ``(vento, ângulo)`` apontam para o *mesmo* objeto (mesma régua, mesma
    frente).

    Args:
        instance: nome da instância.
        external: se ``False``, usa só a nossa campanha (mesmo sentido de
            ``MOWFLOP_EXTERNAL_FRONT`` em :mod:`mowflop.partition`).

    Returns:
        Mapa ``run da nossa campanha -> ScenarioData``, uma entrada por run
        para a qual há cenário conhecido.
    """
    by_scenario = _scenario_data(instance, external)
    out: dict[int, ScenarioData] = {}
    for run, scenario in scenarios(instance).items():
        data = by_scenario.get(scenario)
        if data is None:
            raise ValueError(f"no wind scenario data for {instance} run {run}")
        out[run] = data
    return out
