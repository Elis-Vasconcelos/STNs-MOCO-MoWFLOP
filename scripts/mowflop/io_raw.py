"""Leitura dos logs brutos da campanha.

A campanha vive em ``raw_results/meta_heuristics_stn_windcorrected`` dentro
deste repositório; ``$MOWFLOP_RAW`` sobrescreve isso.  Layout de diretórios
produzido pela campanha em C++::

    <raw_root>/<algoritmo>/<instância>/<config>/<run>/<instância>_<algoritmo>_stn.csv
    <raw_root>/candidates/<instância>_candidates.csv

``config`` é ``p<P>_i<k>``: P vetores observadores, um registro a cada k
gerações.  Cada ``*_stn.csv`` guarda uma única run e tem as colunas

    algorithm,instance,run_id,vector_id,generation,iteration,
    f_cost,f_power,weight1,weight2,occupied

``occupied`` é a lista, separada por espaço, dos índices globais de candidatos
que têm uma turbina -- uma entrada por turbina móvel, já ordenada.  O índice de
candidato é a ordem da linha em ``<instância>_candidates.csv``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

STN_COLUMNS = [
    "algorithm",
    "instance",
    "run_id",
    "vector_id",
    "generation",
    "iteration",
    "f_cost",
    "f_power",
    "weight1",
    "weight2",
    "occupied",
]

# o pipeline em R nomeia as pastas de algoritmo MOEAD/NSGA2; a campanha em C++
# escreve tudo em minúsculo
ALGO_LABELS = {"moead": "MOEAD", "nsga2": "NSGA2"}


def repo_root() -> Path:
    """Raiz do checkout do STNs-MOCO-MoWFLOP.

    Returns:
        Caminho absoluto da raiz do repositório.
    """
    return Path(__file__).resolve().parents[2]


def raw_root(root: str | os.PathLike | None = None) -> Path:
    """Localiza os logs da campanha: ``raw_results/meta_heuristics_stn_windcorrected`` no repo.

    Args:
        root: caminho explícito que sobrescreve o padrão; se ``None``, tenta
            ``$MOWFLOP_RAW`` e depois o caminho padrão dentro do repo.

    Returns:
        Caminho absoluto da raiz dos logs da campanha.

    Raises:
        FileNotFoundError: se nenhum caminho válido for encontrado.
    """
    if root is not None:
        return Path(root).resolve()
    env = os.environ.get("MOWFLOP_RAW")
    if env:
        return Path(env).resolve()
    path = repo_root() / "raw_results" / "meta_heuristics_stn_windcorrected"
    if not path.is_dir():
        raise FileNotFoundError(
            f"campaign logs not found at {path}; set MOWFLOP_RAW or pass root explicitly"
        )
    return path


def discover(root: str | os.PathLike | None = None) -> pd.DataFrame:
    """Inventário de todo ``*_stn.csv`` disponível, uma linha por run.

    Args:
        root: raiz da campanha; ver :func:`raw_root`.

    Returns:
        DataFrame com colunas ``algorithm``, ``instance``, ``config``, ``run``
        e ``path``.
    """
    base = raw_root(root)
    rows = []
    for path in sorted(base.glob("*/*/*/*/*_stn.csv")):
        # desempacota algoritmo/instância/config/run a partir do layout de pastas
        algorithm, instance, config, run = path.relative_to(base).parts[:4]
        rows.append(
            {
                "algorithm": algorithm,
                "instance": instance,
                "config": config,
                "run": run,
                "path": str(path),
            }
        )
    return pd.DataFrame(rows, columns=["algorithm", "instance", "config", "run", "path"])


def inventory(root: str | os.PathLike | None = None) -> pd.DataFrame:
    """Runs disponíveis por (instância, config, algoritmo), para relatórios de progresso.

    Args:
        root: raiz da campanha; ver :func:`raw_root`.

    Returns:
        DataFrame agregado com a contagem de runs distintas por combinação.
    """
    found = discover(root)
    if found.empty:
        return found
    return (
        found.groupby(["instance", "config", "algorithm"], as_index=False)
        .agg(runs=("run", "nunique"))
        .sort_values(["instance", "config", "algorithm"], ignore_index=True)
    )


def load_trajectories(
    instance: str,
    config: str,
    algorithms: list[str] | None = None,
    root: str | os.PathLike | None = None,
) -> pd.DataFrame:
    """Todos os registros de uma (instância, config), entre algoritmos e runs.

    Args:
        instance: nome da instância.
        config: config no formato ``p<P>_i<k>``.
        algorithms: se dado, mantém só esses algoritmos.
        root: raiz da campanha; ver :func:`raw_root`.

    Returns:
        DataFrame concatenado de todas as runs selecionadas, com as colunas
        de :data:`STN_COLUMNS`.

    Raises:
        FileNotFoundError: se não houver nenhum log para a campanha, ou para a
            combinação (instância, config) pedida.
        ValueError: se algum arquivo estiver com formato inesperado.
    """
    found = discover(root)
    if found.empty:
        raise FileNotFoundError("no *_stn.csv files under the campaign root")
    sel = found[(found["instance"] == instance) & (found["config"] == config)]
    if algorithms is not None:
        sel = sel[sel["algorithm"].isin(algorithms)]
    if sel.empty:
        raise FileNotFoundError(f"no logs for instance={instance} config={config}")

    # lê cada CSV de run com os tipos já fixados, para concatenar sem surpresas
    frames = [
        pd.read_csv(
            path,
            dtype={
                "algorithm": "string",
                "instance": "string",
                "run_id": "int32",
                "vector_id": "int32",
                "generation": "int64",
                "iteration": "int32",
                "f_cost": "float64",
                "f_power": "float64",
                "weight1": "float64",
                "weight2": "float64",
                "occupied": "string",
            },
        )
        for path in sel["path"]
    ]
    df = pd.concat(frames, ignore_index=True)
    missing = set(STN_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"unexpected log format, missing columns: {sorted(missing)}")
    return df[STN_COLUMNS]


def load_candidates(
    instance: str, root: str | os.PathLike | None = None
) -> pd.DataFrame:
    """Tabela de decodificação: índice global de candidato -> zona e coordenadas.

    Args:
        instance: nome da instância.
        root: raiz da campanha; ver :func:`raw_root`.

    Returns:
        DataFrame com as colunas ``global_index``, ``zone``, ``zone_index``,
        ``x`` e ``y``.

    Raises:
        ValueError: se o formato do arquivo de candidatos for inesperado, ou
            se ``global_index`` não for a ordem das linhas.
    """
    path = raw_root(root) / "candidates" / f"{instance}_candidates.csv"
    df = pd.read_csv(path)
    expected = ["global_index", "zone", "zone_index", "x", "y"]
    if list(df.columns) != expected:
        raise ValueError(f"unexpected candidate format in {path}: {list(df.columns)}")
    # occupied guarda o índice global; se ele não for a ordem da linha, a decodificação quebra
    if not (df["global_index"].to_numpy() == range(len(df))).all():
        raise ValueError(f"global_index is not row order in {path}")
    return df


def n_positions(instance: str, root: str | os.PathLike | None = None) -> int:
    """Número de posições candidatas, isto é, o tamanho da string binária.

    Args:
        instance: nome da instância.
        root: raiz da campanha; ver :func:`raw_root`.

    Returns:
        Número de candidatos (linhas do arquivo, menos o cabeçalho).
    """
    path = raw_root(root) / "candidates" / f"{instance}_candidates.csv"
    with open(path, "r", encoding="utf-8") as handle:
        return sum(1 for _ in handle) - 1
