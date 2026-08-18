"""Escrita das trajetórias particionadas no formato que o ``create .R`` lê.

Formato alvo (``data/n16_m2/MOEAD/MOEAD_rmnk_-0.4_2_16_1_0_post.txt``)::

    f1 f2 Solution1 Solution2 Run Gen Vector Weight1 Weight2

A *ordem* das colunas importa: o script R faz um ``select(df, f1:Vector)``
posicional e fixa nove tipos de coluna em ``bdf_col_types``.  O *nome* do
arquivo importa também: ``create .R`` o separa por ``_`` e lê o número de
objetivos no quarto campo, depois monta o nome da frente de referência com os
campos 2 a 7 -- daí ``MOEAD_mowflop_ns101_2_x60_p100i50_0_post.txt`` e a
``pf/mowflop/mowflop_ns101_2_x60_p100i50_0_ref.txt`` correspondente.  Nenhum
campo pode conter underscore, por isso a tag de config é escrita ``p100i50``.

Duas coisas precisam de cuidado além do mapeamento de colunas:

*Objetivo canônico por localização.*  ``create .R`` agrupa nós por
``(f1, f2, Solution1, Vector)``.  Num espaço particionado uma localização
carrega muitos vetores objetivo, então esse agrupamento partiria silenciosamente
uma localização em vários nós e desfaria o particionamento.  Toda localização
recebe, portanto, um único objetivo representativo, escolhido entre as
soluções que de fato a visitaram -- a leitura multiobjetivo do
``f(s_z) := min{f(s')}`` do artigo: pertencer à frente de referência primeiro,
depois ordem lexicográfica ``(f_cost, -f_power)``.  Isso também faz a marcação
``Position="Pareto"`` do R coincidir com a métrica da S8.

*Self-loop no último registro.*  ``Solution2`` é a próxima localização da mesma
trajetória ``(Run, Vector)``; o último registro aponta para si mesmo.  Essa é a
convenção dos dados originais rho-mnk e mantém todo endpoint de aresta presente
em ``nodes`` (senão ``graph_from_data_frame`` falha com "Some vertex names in
`d` are not listed in `vertices`").
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import entropy as entropy_mod
from .io_raw import ALGO_LABELS
from .reference_front import DEC, FLOAT_FMT, front_keys, pareto_front, write_front

OUTPUT_COLUMNS = [
    "f1",
    "f2",
    "Solution1",
    "Solution2",
    "Run",
    "Gen",
    "Vector",
    "Weight1",
    "Weight2",
]


def config_tag(config: str) -> str:
    """``p100_i50`` -> ``p100i50``: campos do nome de arquivo não podem ter underscore.

    Args:
        config: config no formato ``p<P>_i<k>``.

    Returns:
        A mesma config, sem underscores.
    """
    return config.replace("_", "")


def output_name(algo_label: str, instance: str, tag: str, cfg_tag: str) -> str:
    """Nome do arquivo de trajetória de um algoritmo, no formato que ``create .R`` espera.

    Args:
        algo_label: rótulo do algoritmo (``MOEAD`` ou ``NSGA2``).
        instance: nome da instância.
        tag: tag do particionamento (``x60``, ``raw``...).
        cfg_tag: config sem underscore (ver :func:`config_tag`).

    Returns:
        Nome do arquivo ``*_post.txt``.

    Raises:
        ValueError: se algum campo contiver underscore.
    """
    for field in (algo_label, instance, tag, cfg_tag):
        if "_" in field:
            raise ValueError(f"file name field cannot contain '_': {field!r}")
    return f"{algo_label}_mowflop_{instance}_2_{tag}_{cfg_tag}_0_post.txt"


def front_name(instance: str, tag: str, cfg_tag: str) -> str:
    """Nome do arquivo da frente de referência, no formato que ``create .R`` espera.

    Args:
        instance: nome da instância.
        tag: tag do particionamento.
        cfg_tag: config sem underscore (ver :func:`config_tag`).

    Returns:
        Nome do arquivo ``*_ref.txt``.
    """
    return f"mowflop_{instance}_2_{tag}_{cfg_tag}_0_ref.txt"


def assign_locations(df: pd.DataFrame, scheme) -> tuple[pd.DataFrame, dict, dict]:
    """Adiciona ``Solution1`` (id da localização) e a projeção, memoizadas por layout bruto.

    Args:
        df: log bruto, com a coluna ``occupied``.
        scheme: esquema de particionamento (:mod:`mowflop.schemes`).

    Returns:
        Tupla ``(df com Solution1, projeções por texto bruto, ids por texto bruto)``.
    """
    distinct = df["occupied"].drop_duplicates()
    ids, projections = {}, {}
    for text in distinct:
        # memoiza por texto bruto -- o mesmo layout aparece em muitos registros
        solution = entropy_mod.from_index_list(text)
        projection = scheme.project(solution)
        ids[text] = scheme.assign(solution)
        projections[text] = projection
    out = df.copy()
    out["Solution1"] = out["occupied"].map(ids)
    return out, projections, ids


def canonical_objectives(df: pd.DataFrame, front: pd.DataFrame) -> pd.DataFrame:
    """Um vetor objetivo representativo por localização.

    Chave de ordenação: estar na frente de referência primeiro, depois
    ``f_cost`` crescente e ``f_power`` decrescente.  O representante é sempre
    uma solução que foi de fato visitada, nunca um ponto ideal sintético.

    Args:
        df: log com a coluna ``Solution1`` já atribuída (ver
            :func:`assign_locations`).
        front: frente de referência da instância.

    Returns:
        DataFrame com uma linha por localização: ``Solution1``, ``f1``, ``f2``
        e ``in_front``.
    """
    keys = front_keys(front)
    candidates = df[["Solution1", "f_cost", "f_power"]].drop_duplicates()
    # chave de string no mesmo formato de front_keys, pra comparar pertencimento à frente
    obj_key = (
        candidates["f_cost"].map(lambda v: FLOAT_FMT % v)
        + "_"
        + candidates["f_power"].map(lambda v: FLOAT_FMT % v)
    )
    candidates = candidates.assign(not_in_front=~obj_key.isin(keys).to_numpy())
    # ordena cada localização: na frente primeiro, depois lexicográfico (custo asc, poder desc)
    candidates = candidates.sort_values(
        ["Solution1", "not_in_front", "f_cost", "f_power"],
        ascending=[True, True, True, False],
        ignore_index=True,
    )
    # o primeiro de cada grupo, após a ordenação acima, é o representante escolhido
    best = candidates.drop_duplicates("Solution1", keep="first")
    best = best.assign(in_front=~best["not_in_front"].to_numpy())
    return best.rename(columns={"f_cost": "f1", "f_power": "f2"})[
        ["Solution1", "f1", "f2", "in_front"]
    ]


def build_table(df: pd.DataFrame, objectives: pd.DataFrame) -> pd.DataFrame:
    """Mapeia o log bruto para as nove colunas, adicionando o defasado ``Solution2``.

    Args:
        df: log com a coluna ``Solution1`` já atribuída.
        objectives: objetivo canônico por localização (ver
            :func:`canonical_objectives`).

    Returns:
        DataFrame com as colunas de :data:`OUTPUT_COLUMNS`, uma linha por registro.
    """
    out = df.merge(objectives, on="Solution1", how="left", validate="many_to_one")
    out["Run"] = out["run_id"].astype("int64") + 1
    out["Gen"] = out["iteration"].astype("int64")
    out["Vector"] = "V" + (out["vector_id"].astype("int64") + 1).astype(str)
    out["Weight1"] = out["weight1"].map(lambda v: FLOAT_FMT % v)
    out["Weight2"] = out["weight2"].map(lambda v: FLOAT_FMT % v)
    out = out.sort_values(["Run", "vector_id", "Gen"], ignore_index=True)
    # próxima localização da mesma trajetória (Run, vector_id), na ordem de Gen
    nxt = out.groupby(["Run", "vector_id"], sort=False)["Solution1"].shift(-1)
    out["Solution2"] = nxt.fillna(out["Solution1"])  # self-loop no último registro
    return out[OUTPUT_COLUMNS]


def check_vectors(table: pd.DataFrame) -> None:
    """``create .R`` deriva o número de vetores das (Vector, weights) distintas.

    Se um vetor mudasse de peso em algum momento essa contagem excederia o
    número de colunas de pivô e a aritmética de colunas do script
    (``i <- m + 2``) leria as colunas erradas silenciosamente.

    Args:
        table: tabela já no formato de saída, com as colunas ``Vector``,
            ``Weight1`` e ``Weight2``.

    Raises:
        ValueError: se algum ``Vector`` aparecer com mais de um par de pesos.
    """
    triples = table[["Vector", "Weight1", "Weight2"]].drop_duplicates()
    if len(triples) != table["Vector"].nunique():
        raise ValueError(
            "a Vector appears with more than one weight pair; "
            "create .R would miscount the vector columns"
        )


def write_table(path: str | Path, table: pd.DataFrame) -> Path:
    """Escreve a tabela de trajetória no formato de ``create .R`` (TSV com espaço, com cabeçalho).

    Args:
        path: caminho de saída.
        table: tabela já no formato de saída (ver :func:`build_table`).

    Returns:
        O caminho escrito, como :class:`Path`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, sep=" ", index=False, float_format=FLOAT_FMT)
    return path


def locations_table(
    df: pd.DataFrame,
    projections: dict[str, frozenset],
    ids: dict[str, str],
    objectives: pd.DataFrame,
) -> pd.DataFrame:
    """Tabela auxiliar: id da localização -> posições retidas, tamanho, representante.

    Args:
        df: log com a coluna ``Solution1`` já atribuída.
        projections: projeção por texto bruto (ver :func:`assign_locations`).
        ids: id de localização por texto bruto (ver :func:`assign_locations`).
        objectives: objetivo canônico por localização.

    Returns:
        DataFrame com uma linha por localização, ordenado por número de
        registros decrescente.
    """
    per_id: dict[str, frozenset] = {}
    for text, location in ids.items():
        # guarda só a primeira projeção vista para cada localização (todas são iguais por construção)
        per_id.setdefault(location, projections[text])
    counts = (
        df.groupby("Solution1")
        .agg(
            solutions=("occupied", "nunique"),
            recordings=("occupied", "size"),
            algorithms=("algorithm", lambda s: "|".join(sorted(set(s)))),
        )
        .reset_index()
    )
    counts["kept_positions"] = counts["Solution1"].map(lambda k: len(per_id[k]))
    counts["positions"] = counts["Solution1"].map(
        lambda k: " ".join(str(p) for p in sorted(per_id[k]))
    )
    return counts.merge(objectives, on="Solution1", how="left").sort_values(
        "recordings", ascending=False, ignore_index=True
    )


def emit(
    df: pd.DataFrame,
    scheme,
    instance: str,
    config: str,
    tag: str,
    out_root: str | Path,
    front: pd.DataFrame | None = None,
) -> dict:
    """Emissão completa de uma (instância, config): arquivos de dados, frente, tabela auxiliar.

    Args:
        df: log bruto da (instância, config).
        scheme: esquema de particionamento (:mod:`mowflop.schemes`).
        instance: nome da instância.
        config: config no formato ``p<P>_i<k>``.
        tag: tag do particionamento, usada nos nomes de arquivo.
        out_root: raiz onde ``data/``, ``pf/`` e ``locations/`` são escritos.
        front: frente de referência já calculada; se ``None``, é calculada
            aqui a partir de ``df``.

    Returns:
        Resumo da emissão: arquivos escritos, tamanho da frente, contagens de
        localizações/soluções/registros e a descrição do esquema.
    """
    out_root = Path(out_root)
    cfg = config_tag(config)
    if front is None:
        front = pareto_front(df)

    located, projections, ids = assign_locations(df, scheme)
    objectives = canonical_objectives(located, front)

    # um arquivo de trajetória por algoritmo, no formato e nome que create .R espera
    data_dir = out_root / "data" / f"mowflop_{tag}"
    written = []
    for algorithm, group in located.groupby("algorithm", sort=True):
        label = ALGO_LABELS.get(str(algorithm), str(algorithm).upper())
        table = build_table(group, objectives)
        check_vectors(table)
        path = write_table(
            data_dir / label / output_name(label, instance, tag, cfg), table
        )
        written.append({"algorithm": label, "path": str(path), "rows": len(table)})

    front_path = write_front(
        out_root / "pf" / "mowflop" / front_name(instance, tag, cfg), front
    )
    loc_path = out_root / "locations" / f"mowflop_{tag}" / f"{instance}_{cfg}_locations.csv"
    loc_path.parent.mkdir(parents=True, exist_ok=True)
    locations_table(located, projections, ids, objectives).to_csv(
        loc_path, index=False, float_format=FLOAT_FMT
    )

    return {
        "instance": instance,
        "config": config,
        "tag": tag,
        "files": written,
        "front": str(front_path),
        "front_size": len(front),
        "locations_table": str(loc_path),
        "locations": located["Solution1"].nunique(),
        "solutions": located["occupied"].nunique(),
        "recordings": len(located),
        "decimals": DEC,
        **scheme.describe(),
    }
