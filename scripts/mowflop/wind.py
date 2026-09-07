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

    ``lower``/``upper`` são os extremos de ``f_power`` no *conjunto todo* do
    cenário, não só na frente -- é o que o ``bound.exe`` do professor calcula
    e grava no ``boundddd.out``, e o que o ``normalize.cc`` consome.  Como a
    trajetória logada na STN é uma amostra da população (e não do arquivo
    ``pareto``), ela pode conter pontos piores que qualquer um do arquivo:
    esses caem *abaixo* de 1,0 depois de normalizados.  Isso é esperado e
    inofensivo -- a transformação é afim, então nada muda de ordem.
    """

    scenario: Scenario
    front: pd.DataFrame
    lower: float
    upper: float

    def normalize(self, values: pd.Series) -> pd.Series:
        """Aplica a régua deste cenário, a mesma fórmula do ``normalize.cc:308``.

        Args:
            values: coluna de ``f_power`` na escala bruta.

        Returns:
            ``1 + (v − lower) / (upper − lower)``, ou 1,0 em toda a coluna se o
            cenário for degenerado (potência constante).
        """
        if self.upper == self.lower:
            return pd.Series(1.0, index=values.index)
        return 1.0 + (values - self.lower) / (self.upper - self.lower)

    def normalize_f_power(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Cópia de ``frame`` com ``f_power`` na régua deste cenário.

        Vale tanto para a frente do cenário quanto para a trajetória de uma run
        dele: a régua é a mesma, e aplicá-la aos dois é o que os põe no mesmo
        eixo.

        Args:
            frame: tabela com uma coluna ``f_power`` na escala bruta.

        Returns:
            Cópia de ``frame`` com ``f_power`` normalizada.
        """
        return frame.assign(f_power=self.normalize(frame["f_power"]))


def scenario_fronts(
    instance: str, config: str, external: bool = True
) -> dict[int, ScenarioData]:
    """Frente de referência e régua de cada run nossa, por cenário de vento.

    Para cada run nossa, une o arquivo ``pareto`` dela ao de *toda* run do
    cec que rodou o mesmo ``(vento, ângulo)`` -- inclusive as runs 11-20, que
    não têm contraparte nossa -- e tira o não dominado.  A frente continua
    sendo "a melhor conhecida", mas agora do mesmo problema: unir runs de
    ventos diferentes é o que hoje produz uma frente inatingível por
    construção (ver ``reports/frente_referencia_vento.md``).

    Args:
        instance: nome da instância.
        config: config no formato ``p<P>_i<k>``.
        external: se ``False``, usa só a nossa campanha (mesmo sentido de
            ``MOWFLOP_EXTERNAL_FRONT`` em :mod:`mowflop.partition`).

    Returns:
        Mapa ``run da nossa campanha -> ScenarioData``, só com as runs que a
        nossa campanha de fato rodou nessa config.
    """
    ours = own_archive_points(instance, config)
    theirs = (
        external_points(instance)
        if external
        else pd.DataFrame(columns=["f_cost", "f_power", "run"])
    )
    by_scenario = scenarios(instance)

    out: dict[int, ScenarioData] = {}
    for run, group in ours.groupby("run", sort=True):
        scenario = by_scenario.get(int(run))
        if scenario is None:
            raise ValueError(f"no wind scenario known for {instance} run {run}")
        matching = theirs[theirs["run"].isin(cec_runs_of(instance, scenario))]
        points = pd.concat([group, matching], ignore_index=True)
        out[int(run)] = ScenarioData(
            scenario=scenario,
            front=pareto_front(points),
            lower=float(points["f_power"].min()),
            upper=float(points["f_power"].max()),
        )
    return out
