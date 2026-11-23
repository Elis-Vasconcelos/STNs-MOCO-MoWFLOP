import os
from mowflop import wind
for inst in os.environ["INSTS"].split():
    ours = wind.scenarios(inst)
    sc = sorted({s for s in ours.values()})
    cec = [r for s in sc for r in wind.cec_runs_of(inst, s)]
    print(inst, "| our runs:", sorted({r for _, r in ours}), "| scenarios:", len(sc), "| external runs entering:", cec or "none")
