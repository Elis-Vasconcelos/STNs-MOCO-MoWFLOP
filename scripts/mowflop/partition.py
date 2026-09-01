"""Script: transforma os logs brutos da campanha em entrada para o ``create .R``.

Não tem CLI: os parâmetros de execução ficam no bloco de constantes logo
abaixo dos imports.  Edite-as e rode::

    python -m mowflop.partition

Rode a partir de ``scripts/`` (ou com ``PYTHONPATH=scripts``) para que
``mowflop`` seja importável, usando o interpretador do virtualenv do repositório.
"""

from __future__ import annotations

import json
import os
import sys

import pandas as pd

from .schemes.shannon_entropy import entropy as entropy_mod
from . import io_raw
from .emit import emit
from .reference_front import external_points, own_archive_points, pareto_front
from .schemes.schemes import build_scheme

# ---------------------------------------------------------------------------
# Parâmetros de execução — edite antes de rodar o script, ou sobrescreva via
# variável de ambiente (mesmo padrão de $MOWFLOP_RAW em io_raw.py), útil para
# rodar vários valores num script não interativo sem editar o arquivo.
# ---------------------------------------------------------------------------

INSTANCE: str | None = os.environ.get("MOWFLOP_INSTANCE", "ns101")
CONFIG: str | None = os.environ.get("MOWFLOP_CONFIG", "p100_i50")
ALL = os.environ.get("MOWFLOP_ALL", "1") == "1"  # se True, processa toda (instância, config) que tenha log disponível
BOTH_ALGORITHMS = os.environ.get("MOWFLOP_BOTH_ALGORITHMS", "0") == "1"  # com ALL=True, mantém só os pares com MOEA/D e NSGA-II
SCHEME = os.environ.get("MOWFLOP_SCHEME", "entropy")
PERCENT = float(os.environ.get("MOWFLOP_PERCENT", "80.0"))  # critério de área em %, em [0, 100]; 0 significa não particionar (só "entropy")
KAPPA = float(os.environ.get("MOWFLOP_KAPPA", "2.0"))
TIE_BREAK = os.environ.get("MOWFLOP_TIE_BREAK", "random")  # "random" (o do artigo) ou "index" (determinístico, só para testes)
SEED = int(os.environ.get("MOWFLOP_SEED", "0"))  # semente do desempate aleatório
EXTERNAL_FRONT = os.environ.get("MOWFLOP_EXTERNAL_FRONT", "1") == "1"  # inclui o histórico do wflopcec26 na frente de referência


def default_tag(scheme: str, percent: float, kappa: float | None = None, external_front: bool = True) -> str:
    """Tag automática do particionamento, usada no nome dos arquivos de saída.

    Args:
        scheme: ``"entropy"``, ``"raw"`` ou ``"grid"``.
        percent: critério de área usado para obter ``z``; ignorado se
            ``scheme != "entropy"``.
        kappa: parâmetro do modelo de grade; obrigatório se ``scheme == "grid"``.
        external_front: se ``False``, sufixa ``noext`` -- roda numa tag
            separada, para não sobrescrever a saída com o histórico do
            wflopcec26 incluído.

    Returns:
        ``"raw"``, ``"x<percent>"`` ou ``"g<kappa>"``, com ``noext`` sufixado
        se ``external_front`` for ``False``.
    """
    if scheme == "raw":
        base = "raw"
    elif scheme == "grid":
        base = f"g{kappa}"
    else:
        base = f"x{int(percent)}"
    return base if external_front else f"{base}noext"


def unique_solutions(df) -> list[entropy_mod.Solution]:
    """``S(T)``: as soluções *únicas* de toda trajetória, como o artigo pede.

    Args:
        df: log bruto, com a coluna ``occupied``.

    Returns:
        Lista das soluções distintas logadas.
    """
    return [entropy_mod.from_index_list(text) for text in df["occupied"].unique()]


def run_one(instance: str, config: str) -> dict:
    """Particiona e emite os arquivos de uma (instância, config), usando as constantes do módulo.

    Args:
        instance: nome da instância.
        config: config no formato ``p<P>_i<k>``.

    Returns:
        Resumo da emissão (ver :func:`mowflop.emit.emit`), com os campos
        ``algorithms`` e ``unique_solutions`` adicionados.
    """
    df = io_raw.load_trajectories(instance, config)
    n = io_raw.n_positions(instance)
    solutions = unique_solutions(df)
    scheme = build_scheme(
        SCHEME,
        solutions,
        n,
        percent=None if SCHEME != "entropy" else PERCENT,
        tie_break=TIE_BREAK,
        seed=SEED,
        instance=instance,
        kappa=KAPPA,
    )
    tag = default_tag(SCHEME, PERCENT, KAPPA, EXTERNAL_FRONT)
    # frente de referência: o conjunto aproximativo da nossa própria campanha
    # (reference_front.own_archive_points -- o arquivo `pareto` acumulado
    # durante toda a busca, não a população amostrada em `df`/`_stn.csv`)
    # unido ao histórico do grupo (reference_front.external_points), não só
    # o que os nossos próprios MOEA/D e NSGA-II acharam -- a menos que
    # EXTERNAL_FRONT esteja desligado
    own = own_archive_points(instance, config)
    external = external_points(instance) if EXTERNAL_FRONT else pd.DataFrame(columns=["f_cost", "f_power"])
    combined = pd.concat([own, external], ignore_index=True)
    front = pareto_front(combined)
    summary = emit(
        df,
        scheme,
        instance=instance,
        config=config,
        tag=tag,
        out_root=io_raw.repo_root(),
        front=front,
    )
    summary["algorithms"] = sorted(df["algorithm"].unique().tolist())
    summary["unique_solutions"] = len(solutions)
    return summary


def main() -> int:
    """Ponto de entrada: processa um par (instância, config) ou todos, conforme as constantes.

    Returns:
        Código de saída do processo (``0`` em sucesso, ``1`` se nada casar
        com os parâmetros dados).
    """
    out_root = io_raw.repo_root()
    print(f"lendo logs de: {io_raw.raw_root()}")
    print(f"salvando em:   {out_root}")

    targets: list[tuple[str, str]]
    if ALL:
        # varre o inventário e monta a lista de (instância, config) a processar
        inv = io_raw.inventory()
        if BOTH_ALGORITHMS:
            counts = inv.groupby(["instance", "config"])["algorithm"].nunique()
            pairs = counts[counts >= 2].index
        else:
            pairs = inv.set_index(["instance", "config"]).index.unique()
        targets = [(str(i), str(c)) for i, c in pairs]
    else:
        if not INSTANCE or not CONFIG:
            print("give INSTANCE and CONFIG, or set ALL = True", file=sys.stderr)
            return 1
        targets = [(INSTANCE, CONFIG)]

    if not targets:
        print("nothing to do: no (instance, config) matched", file=sys.stderr)
        return 1

    summaries = []
    for instance, config in targets:
        summary = run_one(instance, config)
        summaries.append(summary)
        print(
            f"{instance}/{config} [{summary['scheme']}"
            + (f" z={summary['z']}" if "z" in summary else "")
            + f"] {summary['recordings']} recordings, "
            f"{summary['solutions']} solutions -> {summary['locations']} locations, "
            f"front={summary['front_size']}"
        )
        # onde cada arquivo desta (instância, config) foi escrito
        for written in summary["files"]:
            print(f"  -> {written['path']} ({written['rows']} linhas)")
        print(f"  -> {summary['front']} (frente de referência, {summary['front_size']} pontos)")
        print(f"  -> {summary['locations_table']} (tabela de localizações)")

    out = out_root / "reports" / "partition_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(f"resumo -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
