"""Métricas de STN que só o lado Python calcula: ``step_len``, ``R(κ)`` e ``D(κ)``.

Definições (``o_g(v)`` = turbinas do nó ``v`` na célula ``g``, ``τ`` = nº de
turbinas)::

    step_len = (1/|E|) * sum_{(u,v) in E} sum_g |o_g(u) - o_g(v)| / (2τ)
    R(κ)     = 1 - |N_κ| / |N_0|
    D(κ)     = sum_L w_L d(L) / sum_L w_L,   d(L) = max_{u,v in S_L} ||f(u) - f(v)||_2

``D`` sai nas variantes normalizadas, por run e agregadas; no agregado ele
carrega também um piso de vento (ver :func:`dataset_metrics`).

Nenhuma das três sai do ``create .R``: ele só vê o id da localização e um
objetivo canônico por nó (:func:`mowflop.emit.canonical_objectives`), e a
assinatura ``o_g``, as soluções cruas de cada nó e os objetivos de cada uma
ficam para trás no ``emit``.  Este script refaz a partição em memória pelo
mesmo código do ``partition.py`` (:func:`mowflop.partition.scheme_for` e
:func:`mowflop.partition.datasets_to_emit`), sem escrever ``data/`` -- o que
também permite varrer κ para as curvas da RQ2 sem rodar o R.

Segue o contrato de variáveis de ambiente ``MOWFLOP_*`` do ``partition.py``
(esquema, κ, percent, variante), então a tag sai igual.  ``MOWFLOP_ALL``,
``MOWFLOP_INSTANCE`` e ``MOWFLOP_CONFIG`` são ignorados: sem ``--instance``
processa todo o inventário, com ele todas as configs da instância -- as linhas
vão todas para um CSV só, que uma chamada por config sobrescreveria::

    MOWFLOP_SCHEME=grid MOWFLOP_KAPPA=1.0 MOWFLOP_PER_RUN=1 MOWFLOP_NORMALIZE=1 \\
        ../.venv/bin/python -m mowflop.partition_metrics --instance ns178

Escreve ``metrics/mowflop_<tag>_partition_metrics.csv``, uma linha por
(instância, tag, algoritmo, p, run) -- a mesma chave de ``*_stn_metrics.csv``.
"""

from __future__ import annotations

import argparse
import math
import re
import sys

import numpy as np
import pandas as pd

from . import io_raw, partition
from .emit import assign_locations, config_tag, instance_label, output_name
from .io_raw import ALGO_LABELS

COLUMNS = [
    "instance",
    "tag",
    "algo",
    "p",
    "run",
    "tau",
    "n_positions",
    "density",
    "nodes_raw",
    "nodes",
    "edges",
    "R",
    "D",
    "step_len",
]


def location_signatures(scheme_name: str, projections: dict, ids: dict) -> dict[str, dict] | None:
    """Assinatura de ocupação ``{célula: turbinas}`` de cada localização.

    Args:
        scheme_name: ``"grid"``, ``"raw"`` ou ``"entropy"``.
        projections: projeção por texto bruto (ver :func:`mowflop.emit.assign_locations`).
        ids: id de localização por texto bruto.

    Returns:
        Dicionário id -> assinatura.  No ``raw`` cada posição ocupada é uma
        "célula" com uma turbina, e ``step_len`` vira Hamming/2τ.  ``None`` no
        ``entropy``: a projeção em ``z`` posições não tem τ turbinas, então
        ``o_g`` não se define.
    """
    if scheme_name == "grid":
        convert = dict
    elif scheme_name == "raw":
        convert = lambda solution: dict.fromkeys(solution, 1)  # noqa: E731
    else:
        return None
    signatures: dict[str, dict] = {}
    for text, location in ids.items():
        # todas as projeções de uma localização são iguais por construção
        if location not in signatures:
            signatures[location] = convert(projections[text])
    return signatures


def trajectory_edges(located: pd.DataFrame) -> pd.DataFrame:
    """O conjunto de arestas ``E`` da STN, como o ``create .R`` o monta.

    Mesma ordenação e mesmo self-loop final de :func:`mowflop.emit.build_table`;
    o ``create .R`` agrupa por ``(Solution1, Solution2)``, então ``E`` são os
    pares distintos, self-loops incluídos.

    Args:
        located: log de um algoritmo com ``Solution1`` atribuído.

    Returns:
        DataFrame com as colunas ``Solution1`` e ``Solution2``, uma linha por aresta.
    """
    ordered = located.sort_values(["run_id", "vector_id", "iteration"], ignore_index=True)
    nxt = ordered.groupby(["run_id", "vector_id"], sort=False)["Solution1"].shift(-1)
    return pd.DataFrame(
        {"Solution1": ordered["Solution1"], "Solution2": nxt.fillna(ordered["Solution1"])}
    ).drop_duplicates(ignore_index=True)


def edge_step(su: dict, sv: dict, tau: int) -> float:
    """Fração de turbinas que mudam de célula numa aresta: ``sum_g |o_g(u) - o_g(v)| / 2τ``.

    Args:
        su: assinatura de ``u``.
        sv: assinatura de ``v``.
        tau: nº de turbinas.

    Returns:
        Valor em ``[0, 1]``.
    """
    moved = sum(abs(su.get(cell, 0) - sv.get(cell, 0)) for cell in su.keys() | sv.keys())
    return moved / (2 * tau)


def step_len(edges: pd.DataFrame, signatures: dict[str, dict], tau: int) -> float:
    """Média simples de :func:`edge_step` sobre ``E`` (self-loops contam 0).

    Args:
        edges: arestas de :func:`trajectory_edges`.
        signatures: assinatura por localização.
        tau: nº de turbinas.

    Returns:
        ``step_len``, ou ``nan`` se não houver arestas.
    """
    if edges.empty:
        return math.nan
    total = 0.0
    for u, v in zip(edges["Solution1"], edges["Solution2"]):
        if u != v:
            total += edge_step(signatures[u], signatures[v], tau)
    return total / len(edges)


def diameter(points) -> float:
    """``d(L)``: maior distância euclidiana entre dois pontos do conjunto.

    Args:
        points: array ``(k, 2)`` de objetivos.

    Returns:
        O diâmetro; ``0`` com menos de dois pontos distintos.
    """
    pts = np.unique(np.asarray(points, dtype=float), axis=0)
    if len(pts) < 2:
        return 0.0
    # para cada ponto p: pts - p são os vetores de p até todos os pontos, e
    # norm(..., axis=1) o comprimento de cada um, ou seja, a distância de p a
    # cada ponto.  O .max() é o ponto mais longe de p, e o max externo o maior
    # desses valores entre todos os p: max_{u,v} ||f(u) - f(v)||
    return float(max(np.linalg.norm(pts - p, axis=1).max() for p in pts))


def distortion(located: pd.DataFrame) -> float:
    """``D``: diâmetro de cada localização no espaço objetivo, ponderado pelas visitas.

    Supõe que todo ponto de ``located`` está na mesma régua -- só assim o diâmetro
    mede partição.  Quem garante isso é :func:`dataset_metrics`, que só chama esta
    função nas variantes por run.

    Args:
        located: log de um algoritmo com ``Solution1``, ``f_cost`` e ``f_power``.

    Returns:
        ``D``, com ``w_L`` = nº de registros em ``L`` (o ``Count`` do nó no R).
    """
    weights = located.groupby("Solution1", sort=False).size()
    points = located[["Solution1", "f_cost", "f_power"]].drop_duplicates()
    distinct = points.groupby("Solution1", sort=False).size()
    # localização com um único ponto distinto tem diâmetro 0; só as outras são medidas
    multi = points[points["Solution1"].isin(distinct.index[distinct >= 2])]
    diameters = {
        location: diameter(group[["f_cost", "f_power"]].to_numpy())
        for location, group in multi.groupby("Solution1", sort=False)
    }
    d = weights.index.map(lambda location: diameters.get(location, 0.0)).to_numpy()
    return float((weights.to_numpy() * d).sum() / weights.sum())


def tau_of(located: pd.DataFrame) -> int:
    """Nº de turbinas por layout, conferindo que é constante.

    Args:
        located: log com a coluna ``occupied``.

    Returns:
        τ.

    Raises:
        ValueError: se os layouts tiverem números de turbinas diferentes.
    """
    lengths = located["occupied"].drop_duplicates().str.split().str.len().unique()
    if len(lengths) != 1:
        raise ValueError(f"layouts with different turbine counts: {sorted(lengths)}")
    return int(lengths[0])


def dataset_metrics(
    located: pd.DataFrame,
    signatures: dict[str, dict] | None,
    n_positions: int,
    normalize: bool,
) -> dict:
    """As métricas de uma STN (um algoritmo num dataset).

    ``D`` se calcula sempre que ``normalize``, por run ou agregado.  Numa run (um
    cenário de vento, uma régua só) o diâmetro no espaço objetivo mede apenas a
    fusão da partição.  No dataset agregado cada run entra normalizada pela régua
    do *seu* cenário (ver :mod:`mowflop.wind`), então a mesma solução aparece com
    objetivos diferentes conforme a run -- ``D`` carrega também um piso de vento
    que não vem da partição, e deve ser lido com isso em mente.  Medido em ns101/p10_i50:
    no esquema ``raw`` agregado, onde nada é fundido (``R = 0``), ``D`` ainda sai
    7.3e-4; no ``grid`` κ=1.0 vai de 0.0325 para 0.0099 descontando as
    localizações vistas por mais de uma run.  ``R`` e ``step_len`` não sofrem
    disso: saem da assinatura e do ``occupied``, não dos objetivos.

    Args:
        located: log do algoritmo com ``Solution1`` atribuído.
        signatures: assinatura por localização, ou ``None`` (``step_len`` sai ``nan``).
        n_positions: ``|P|``, nº de posições candidatas.
        normalize: se os objetivos estão na régua do cenário; senão ``D`` sai ``nan``.

    Returns:
        Dicionário com as colunas de :data:`COLUMNS` a partir de ``tau``.
    """
    tau = tau_of(located)
    nodes = located["Solution1"].nunique()
    # sem particionamento cada layout distinto é um nó, então |N_0| = nº de layouts distintos
    nodes_raw = located["occupied"].nunique()  # |N_0|: um nó por solução crua no create .R
    edges = trajectory_edges(located)
    return {
        "tau": tau,
        "n_positions": n_positions,
        "density": tau / n_positions,
        "nodes_raw": nodes_raw,
        "nodes": nodes,
        "edges": len(edges),
        "R": 1.0 - nodes / nodes_raw,
        "D": distortion(located) if normalize else math.nan,
        "step_len": step_len(edges, signatures, tau) if signatures is not None else math.nan,
    }


def check_emitted(located: pd.DataFrame, label: str, instance: str, config: str, tag: str, run_label: str) -> None:
    """Avisa no stderr se as localizações recalculadas diferem das emitidas em ``data/``.

    Não faz nada se o arquivo de trajetória ainda não foi emitido.

    Args:
        located: log do algoritmo com ``Solution1`` recalculado.
        label: rótulo do algoritmo (``MOEAD``/``NSGA2``).
        instance: nome da instância.
        config: config no formato ``p<P>_i<k>``.
        tag: tag desta execução.
        run_label: sétimo campo do nome de arquivo.
    """
    name = output_name(label, instance_label(instance), tag, config_tag(config), run_label)
    path = io_raw.out_root() / "data" / f"mowflop_{tag}" / label / name
    if not path.is_file():
        return
    emitted = pd.read_csv(path, sep=" ", usecols=["Solution1"], dtype={"Solution1": str})
    if set(emitted["Solution1"]) != set(located["Solution1"]):
        partition.warn(
            f"{name}: localizações recalculadas diferem das emitidas em data/ -- "
            "o partition.py rodou com outros parâmetros?"
        )


def p_of(config: str) -> int:
    """``p100_i50`` -> ``100``.

    Args:
        config: config no formato ``p<P>_i<k>``.

    Returns:
        O número de vetores observadores.
    """
    match = re.match(r"p(\d+)_", config)
    if match is None:
        raise ValueError(f"unexpected config: {config!r}")
    return int(match.group(1))


def run_one(instance: str, config: str, tag: str) -> list[dict]:
    """Métricas de toda STN de uma (instância, config), uma linha por (dataset, algoritmo).

    Args:
        instance: nome da instância.
        config: config no formato ``p<P>_i<k>``.
        tag: tag desta execução.

    Returns:
        Linhas com as colunas de :data:`COLUMNS`; vazia se o esquema não se aplica.
    """
    if not partition.scheme_available(instance, config):
        return []
    df = io_raw.load_trajectories(instance, config)
    scheme, _ = partition.scheme_for(instance, df)
    n_positions = io_raw.n_positions(instance)

    rows = []
    for run_label, trajectory, _front in partition.datasets_to_emit(df, instance, config):
        located, projections, ids = assign_locations(trajectory, scheme)
        signatures = location_signatures(scheme.name, projections, ids)
        for algorithm, group in located.groupby("algorithm", sort=True):
            label = ALGO_LABELS.get(str(algorithm), str(algorithm).upper())
            check_emitted(group, label, instance, config, tag, run_label)
            row = {
                "instance": instance_label(instance),
                "tag": tag,
                "algo": label,
                "p": p_of(config),
                "run": run_label,
            }
            row.update(
                dataset_metrics(
                    group, signatures, n_positions, partition.NORMALIZE
                )
            )
            rows.append(row)
    return rows


def targets(instance: str | None) -> list[tuple[str, str]]:
    """Pares (instância, config) a processar, com o mesmo filtro do ``partition.py``.

    Args:
        instance: se dado, só as configs com log dessa instância.

    Returns:
        Lista de ``(instância, config)`` (ver :func:`mowflop.partition.select_pairs`).
    """
    inv = io_raw.inventory()
    if instance is not None:
        inv = inv[inv["instance"] == instance]
    return partition.select_pairs(inv)


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando.

    Args:
        argv: argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns:
        Código de saída do processo.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instance", help="só esta instância (todas as configs com log)")
    args = parser.parse_args(argv)

    tag = partition.current_tag()
    pairs = targets(args.instance)
    if not pairs:
        print("nothing to do: no (instance, config) matched", file=sys.stderr)
        return 1
    if not partition.NORMALIZE:
        partition.warn(f"{tag}: objetivos na escala bruta; D sai NA (só se calcula nas variantes norm)")

    rows = []
    for instance, config in pairs:
        for row in run_one(instance, config, tag):
            print(
                f"{instance}/{config}/{row['run']} {row['algo']}: nodes={row['nodes']} "
                f"R={row['R']:.4f} D={row['D']:.4f} step_len={row['step_len']:.4f}"
            )
            rows.append(row)

    out = io_raw.out_root() / "metrics" / f"mowflop_{tag}_partition_metrics.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLUMNS).to_csv(out, index=False, float_format="%.6f", na_rep="NA")
    print(f"métricas -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
