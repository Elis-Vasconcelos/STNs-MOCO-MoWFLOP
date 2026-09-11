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
from .wind import scenario_fronts

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
PER_RUN = os.environ.get("MOWFLOP_PER_RUN", "0") == "1"  # um dataset por run (por cenário de vento) em vez de um agregado
NORMALIZE = os.environ.get("MOWFLOP_NORMALIZE", "1") == "1"  # escala f_cost e f_power pela régua do cenário de cada run; ligado por padrão, porque sem isso a frente une ventos diferentes (ver mowflop/wind.py)


def default_tag(
    scheme: str,
    percent: float,
    kappa: float | None = None,
    external_front: bool = True,
    per_run: bool = False,
    normalize: bool = False,
) -> str:
    """Tag automática do particionamento, usada no nome dos arquivos de saída.

    A tag é o único eixo de variação que o lado R enxerga: ``data/mowflop_<tag>/``,
    ``stns/mowflop_<tag>/`` e ``plots/mowflop_<tag>/``.  Dando a cada variante a
    sua própria tag, ``run_create_r.py`` e ``run_plot_r.py`` rodam sem alteração.

    Args:
        scheme: ``"entropy"``, ``"raw"`` ou ``"grid"``.
        percent: critério de área usado para obter ``z``; ignorado se
            ``scheme != "entropy"``.
        kappa: parâmetro do modelo de grade; obrigatório se ``scheme == "grid"``.
        external_front: se ``False``, sufixa ``noext`` -- roda numa tag
            separada, para não sobrescrever a saída com o histórico do
            wflopcec26 incluído.
        per_run: se ``True``, sufixa ``run`` -- um dataset por cenário de vento.
        normalize: se ``True``, sufixa ``norm`` -- ``f_cost`` e ``f_power`` na régua do cenário.

    Returns:
        ``"raw"``, ``"x<percent>"`` ou ``"g<kappa>"``, com os sufixos
        ``noext``/``run``/``norm`` que se aplicarem, nessa ordem -- por exemplo
        ``x80norm`` (agregada, normalizada) ou ``x80runnorm`` (por cenário,
        normalizada).
    """
    if scheme == "raw":
        base = "raw"
    elif scheme == "grid":
        base = f"g{kappa}"
    else:
        base = f"x{int(percent)}"
    if not external_front:
        base = f"{base}noext"
    if per_run:
        base = f"{base}run"
    if normalize:
        base = f"{base}norm"
    return base


def current_tag() -> str:
    """A tag desta execução: :func:`default_tag` sobre as constantes do módulo.

    Fonte única da tag, também para os scripts de campanha, que precisam dela
    para dizer às etapas do R em que pasta olhar (``--tag``).

    Returns:
        A tag, já com todos os sufixos que as constantes do módulo pedirem.
    """
    return default_tag(SCHEME, PERCENT, KAPPA, EXTERNAL_FRONT, PER_RUN, NORMALIZE)


def unique_solutions(df) -> list[entropy_mod.Solution]:
    """``S(T)``: as soluções *únicas* de toda trajetória, como o artigo pede.

    Args:
        df: log bruto, com a coluna ``occupied``.

    Returns:
        Lista das soluções distintas logadas.
    """
    return [entropy_mod.from_index_list(text) for text in df["occupied"].unique()]


def datasets_to_emit(df, instance: str, config: str) -> list[tuple[str, "pd.DataFrame", "pd.DataFrame"]]:
    """Divide uma (instância, config) nos datasets a emitir, conforme ``PER_RUN``/``NORMALIZE``.

    Quatro combinações, uma tag cada:

    ===========  =========  ====================================================
    ``PER_RUN``  ``NORM``   dataset
    ===========  =========  ====================================================
    ``False``    ``False``  o agregado histórico: uma frente só, do não dominado
                            da união de *todas* as runs.  Une cenários de vento
                            diferentes.
    ``False``    ``True``   um dataset agregando as runs, com ``f_cost`` e
                            ``f_power`` na régua do cenário de cada uma: as
                            faixas horizontais colapsam umas sobre as outras.
    ``True``     ``False``  um dataset por cenário, na escala bruta.
    ``True``     ``True``   um dataset por cenário, normalizado -- o mesmo grafo
                            do caso anterior (a normalização é afim e crescente
                            dentro de uma run), só que todos no mesmo eixo
                            ``[1, 2]`` e portanto comparáveis entre si.
    ===========  =========  ====================================================

    Args:
        df: log bruto da (instância, config).
        instance: nome da instância.
        config: config no formato ``p<P>_i<k>``.

    Returns:
        Lista de ``(run_label, trajetória, frente)``, onde ``run_label`` é o
        sétimo campo do nome de arquivo (ver :func:`mowflop.emit.front_name`).
    """
    if not PER_RUN and not NORMALIZE:
        # frente de referência: o conjunto aproximativo da nossa própria campanha
        # (reference_front.own_archive_points -- o arquivo `pareto` acumulado
        # durante toda a busca, não a população amostrada em `df`/`_stn.csv`)
        # unido ao histórico do wflopcec26 (reference_front.external_points), não só
        # o que os nossos próprios MOEA/D e NSGA-II acharam -- a menos que
        # EXTERNAL_FRONT esteja desligado
        own = own_archive_points(instance, config)
        external = external_points(instance) if EXTERNAL_FRONT else pd.DataFrame(columns=["f_cost", "f_power"])
        return [("0", df, pareto_front(pd.concat([own, external], ignore_index=True)))]

    pieces = []
    for run, data in sorted(scenario_fronts(instance, EXTERNAL_FRONT).items()):
        traj = df[df["run_id"] == run]
        if traj.empty:  # a run tem arquivo `pareto` mas não foi logada nesta config
            continue
        front = data.front
        if NORMALIZE:
            traj = data.normalize_objectives(traj)
            front = data.normalize_objectives(front)
        pieces.append((run, traj, front))

    if PER_RUN:
        return [(f"r{run:02d}", traj, front) for run, traj, front in pieces]
    # agregado: as trajetórias já normalizadas voltam a um dataset só, e a frente
    # é o não dominado da união das frentes por cenário -- agora todas na mesma régua
    return [
        (
            "0", # 0 é o default quando a execução é agregada, não por run
            pd.concat([traj for _, traj, _ in pieces], ignore_index=True),
            pareto_front(pd.concat([front for _, _, front in pieces], ignore_index=True)),
        )
    ]


def run_one(instance: str, config: str) -> list[dict]:
    """Particiona e emite os arquivos de uma (instância, config), usando as constantes do módulo.

    Args:
        instance: nome da instância.
        config: config no formato ``p<P>_i<k>``.

    Returns:
        Um resumo de emissão (ver :func:`mowflop.emit.emit`) por dataset, com os
        campos ``algorithms`` e ``unique_solutions`` adicionados.  Uma lista de
        um elemento, exceto quando ``PER_RUN`` (aí, uma por cenário).
    """
    df = io_raw.load_trajectories(instance, config)
    n = io_raw.n_positions(instance)
    solutions = unique_solutions(df)
    # o particionamento sai de S(T) da (instância, config) INTEIRA em toda
    # variante, inclusive nas por run: é o que faz as tags falarem do mesmo
    # conjunto de localizações, isolando o efeito da normalização na comparação
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
    tag = current_tag()

    summaries = []
    for run_label, trajectory, front in datasets_to_emit(df, instance, config):
        summary = emit(
            trajectory,
            scheme,
            instance=instance,
            config=config,
            tag=tag,
            out_root=io_raw.repo_root(),
            front=front,
            run_label=run_label,
        )
        summary["algorithms"] = sorted(trajectory["algorithm"].unique().tolist())
        summary["unique_solutions"] = len(solutions)
        summaries.append(summary)
    return summaries


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
        for summary in run_one(instance, config):
            summaries.append(summary)
            print(
                f"{instance}/{config}/{summary['run_label']} [{summary['scheme']}"
                + (f" z={summary['z']}" if "z" in summary else "")
                + f"] {summary['recordings']} recordings, "
                f"{summary['solutions']} solutions -> {summary['locations']} locations, "
                f"front={summary['front_size']}"
            )
            # onde cada arquivo deste dataset foi escrito
            for written in summary["files"]:
                print(f"  -> {written['path']} ({written['rows']} linhas)")
            print(f"  -> {summary['front']} (frente de referência, {summary['front_size']} pontos)")
            print(f"  -> {summary['locations_table']} (tabela de localizações)")

    # um resumo por tag: as variantes rodam em paralelo no run_stn_variants.sh
    # e um nome fixo faria uma sobrescrever a outra
    tag = current_tag()
    out = out_root / "reports" / f"partition_summary_{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(f"resumo -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
