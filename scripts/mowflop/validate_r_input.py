"""Confere se um dataset emitido é o que ``create .R`` espera, antes de rodar o R.

O script R falha tarde e de forma obscura quando alguma suposição sua é
quebrada (uma frente de referência ausente para no ``read.table``; um endpoint
de aresta ausente em ``nodes`` para no ``graph_from_data_frame`` com "Some
vertex names in `d` are not listed in `vertices`").  Isso reproduz seus passos
críticos em pandas para que os problemas apareçam aqui em vez de lá:

* os nove nomes de coluna, na ordem, e nove campos em toda linha;
* ``nGen <- max(df$Gen) + 1`` / ``nRun <- max(df$Run)`` mantêm toda linha;
* ``group_by(f1, f2, Solution1, Vector)`` não parte uma localização em vários
  nós -- a armadilha que desfaria o particionamento silenciosamente;
* todo endpoint de aresta de ``filter(Gen < nGen)`` existe em ``nodes``;
* a frente de referência está exatamente no caminho que o script R calcula a
  partir do nome do arquivo, e seus valores batem com os objetivos dos nós
  como strings em ``dec = 6``;
* um par de pesos por vetor, para que a aritmética de colunas do script se
  sustente.

Uso::

    python -m mowflop.validate_r_input --data-dir ../data/mowflop_x60
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .emit import OUTPUT_COLUMNS
from .reference_front import DEC, FLOAT_FMT

FLOAT_COLUMNS = ("f1", "f2")


def front_path_as_r_computes(data_file: Path, pf_root: Path) -> Path:
    """Espelha o cálculo de caminho das linhas 59-63 de ``create .R``.

    Args:
        data_file: caminho do arquivo de trajetória (``*_post.txt``).
        pf_root: raiz onde as frentes de referência estão.

    Returns:
        Caminho da frente de referência que ``create .R`` procuraria.

    Raises:
        ValueError: se o nome do arquivo não tiver campos suficientes
            separados por ``_``.
    """
    fields = data_file.name.split("_")
    if len(fields) < 8:
        raise ValueError(f"file name has too few '_' fields for create .R: {data_file.name}")
    return pf_root / ("_".join(fields[1:7]) + "_ref.txt")


def check_file(data_file: Path, pf_root: Path) -> dict:
    """Roda todas as checagens de um arquivo de trajetória emitido.

    Args:
        data_file: caminho do arquivo de trajetória (``*_post.txt``).
        pf_root: raiz onde as frentes de referência estão.

    Returns:
        Dicionário com contagens (linhas, nós, arestas, vetores, runs...) e a
        lista de problemas encontrados (vazia se o arquivo estiver OK).
    """
    problems: list[str] = []

    with open(data_file, "r", encoding="utf-8") as handle:
        header = handle.readline().split()
    if header != OUTPUT_COLUMNS:
        problems.append(f"header is {header}, expected {OUTPUT_COLUMNS}")

    df = pd.read_csv(data_file, sep=" ")
    if df.isna().any().any():
        problems.append("file has missing values; read.table would misalign columns")

    # create .R: nGen <- max(df$Gen) + 1 ; nRun <- max(df$Run)
    n_gen, n_run = int(df["Gen"].max()) + 1, int(df["Run"].max())
    kept = df[(df["Gen"] <= n_gen) & (df["Run"] <= n_run)]
    if len(kept) != len(df):
        problems.append(f"{len(df) - len(kept)} rows dropped by the Gen/Run filter")
    if int(df["Run"].min()) < 1:
        problems.append("Run is not one-based; create .R would drop run 0")

    # a armadilha do group_by(f1, f2, Solution1, Vector)
    per_location = df.groupby("Solution1")[["f1", "f2"]].nunique()
    fragmented = int(((per_location > 1).any(axis=1)).sum())
    if fragmented:
        problems.append(
            f"{fragmented} locations carry more than one objective vector and "
            "would be split into several nodes by create .R"
        )

    # graph_from_data_frame(edges, vertices = nodes)
    nodes = set(df["Solution1"])
    edges = df[df["Gen"] < n_gen]
    dangling = (set(edges["Solution1"]) | set(edges["Solution2"])) - nodes
    if dangling:
        problems.append(f"{len(dangling)} edge endpoints are missing from nodes")

    # um par de pesos por vetor, senão a aritmética de colunas do vetor quebra
    triples = df[["Vector", "Weight1", "Weight2"]].drop_duplicates()
    n_vec = df["Vector"].nunique()
    if len(triples) != n_vec:
        problems.append("a Vector appears with more than one weight pair")

    # frente de referência, no caminho exato que create .R monta a partir do nome do arquivo
    front_file = front_path_as_r_computes(data_file, pf_root)
    pareto_nodes = -1
    if not front_file.is_file():
        problems.append(f"reference front not found where create .R looks: {front_file}")
    else:
        front = pd.read_csv(front_file, sep="\t", header=None, names=["f1", "f2"])
        keys = {
            f"{FLOAT_FMT % a}_{FLOAT_FMT % b}"
            for a, b in front.itertuples(index=False)
        }
        node_keys = (
            df.drop_duplicates("Solution1")
            .apply(lambda r: f"{FLOAT_FMT % r['f1']}_{FLOAT_FMT % r['f2']}", axis=1)
        )
        pareto_nodes = int(node_keys.isin(keys).sum())
        if pareto_nodes == 0:
            problems.append("no node matches the reference front; Position='Pareto' would be empty")
        if pareto_nodes == len(node_keys):
            problems.append("every node matches the reference front, which is the overflow bug's symptom")

    return {
        "file": data_file.name,
        "rows": len(df),
        "nodes": len(nodes),
        "edges": len(edges),
        "vectors": n_vec,
        "runs": int(df["Run"].nunique()),
        "nGen": n_gen,
        "pareto_nodes": pareto_nodes,
        "front": front_file.name,
        "decimals": DEC,
        "problems": problems,
    }


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada de linha de comando: valida todo arquivo de trajetória de um dataset.

    Args:
        argv: argumentos de linha de comando; ``None`` usa ``sys.argv``.

    Returns:
        ``0`` se todos os arquivos passarem, ``1`` se algum tiver problemas
        (ou se nenhum arquivo for encontrado).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", required=True, help="e.g. data/mowflop_x60")
    parser.add_argument("--pf-root", help="default: <repo>/pf/mowflop")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir).resolve()
    pf_root = Path(args.pf_root) if args.pf_root else data_dir.parents[1] / "pf" / "mowflop"

    files = sorted(data_dir.glob("*/*.txt"))
    if not files:
        print(f"no data files under {data_dir}")
        return 1

    failed = 0
    for data_file in files:
        result = check_file(data_file, pf_root)
        status = "OK  " if not result["problems"] else "FAIL"
        print(
            f"{status} {result['file']}: {result['rows']} rows, {result['nodes']} nodes, "
            f"{result['edges']} edges, {result['vectors']} vectors, {result['runs']} runs, "
            f"nGen={result['nGen']}, nós no front={result['pareto_nodes']}"
        )
        for problem in result["problems"]:
            print(f"       - {problem}")
        failed += bool(result["problems"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
