"""Compara nossos resultados (vento/angulo corrigidos p/ bater com o CEC) vs CEC.

Reproduz o estilo do gráfico que o Arthur mandou (mesmas cores/marcadores,
uma figura por instância), usando o run_id que teve angle/wind sorteado
igual ao que o CEC usou na run 1 de cada instância, em vez do
angle=30/wind=10 fixo original.

Lê direto das fontes canônicas (sem cópia local de dado):
- "Nosso": STN_MoWFLOP (repo irmão, assume layout padrão do workspace
  TCC/) em raw_results/meta_heuristics_stn_windcorrected/.
- "CEC": raw_results/wflopcec26_results/ deste próprio repo (vendorizado
  por completo, ver commit "Fronteira de refrência inclui resultados do
  wflopcec26").
"""
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOSSO_ROOT = REPO_ROOT.parent / "STN_MoWFLOP" / "raw_results" / "meta_heuristics_stn_windcorrected"
CEC_ROOT = REPO_ROOT / "raw_results" / "wflopcec26_results"
HERE = Path(__file__).parent

# run_id usado na prova original (angle/wind = run 1 do CEC); a campanha
# completa (run_id 0-9) cobre o mesmo cenário pra cada run, ver
# STN_MoWFLOP/tmp_demo/wind_corrected/cec_wind_map.csv
NOSSO_RUN_ID = 50
CEC_RUN = 1


def load(path):
    return pd.read_csv(path, sep=r"\s+", header=None, names=["cost", "power"])


def plot_instance(instance):
    nosso_moead = load(NOSSO_ROOT / "moead" / f"ns{instance}" / "p10_i50" / str(NOSSO_RUN_ID) / f"ns{instance}_moead_1000000.txt")
    nosso_nsga2 = load(NOSSO_ROOT / "nsga2" / f"ns{instance}" / "p10_i50" / str(NOSSO_RUN_ID) / f"ns{instance}_nsga2_1000000.txt")
    cec_moead = load(CEC_ROOT / "moead" / f"ns{instance}" / str(CEC_RUN) / f"{instance}_moead_1000000.txt")
    cec_nsga2 = load(CEC_ROOT / "nsga2" / f"ns{instance}" / str(CEC_RUN) / f"{instance}_nsga2_1000000.txt")

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(nosso_moead["cost"], nosso_moead["power"], c="#00008B", marker="o", s=18, label="Nosso MOEA/D", zorder=3)
    ax.scatter(cec_moead["cost"], cec_moead["power"], c="#87CEEB", marker="^", s=22, label="CEC MOEA/D", zorder=2)
    ax.scatter(nosso_nsga2["cost"], nosso_nsga2["power"], c="#8B0000", marker="o", s=18, label="Nosso NSGA-II", zorder=3)
    ax.scatter(cec_nsga2["cost"], cec_nsga2["power"], c="#FFA500", marker="^", s=22, label="CEC NSGA-II", zorder=2)

    ax.set_title(f"Instância ns{instance} (vento/angulo corrigido = mesmo do CEC)")
    ax.set_xlabel("Custo de construção")
    ax.set_ylabel("Potência")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out = HERE.parent.parent / "plots" / "mowflop_comparison_windfix" / f"corrected_{instance}.png"
    plt.savefig(out, dpi=150)
    print(f"saved {out}")


if __name__ == "__main__":
    plot_instance("101")
    plot_instance("178")
