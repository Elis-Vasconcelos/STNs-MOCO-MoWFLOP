from mowflop import wind
for inst in ["ns48", "ns178"]:
    for ext in (False, True):
        d = wind._scenario_data(inst, external=ext)
        print(inst, "external" if ext else "noext   ", "front points per scenario:", [len(v.front) for v in d.values()])
