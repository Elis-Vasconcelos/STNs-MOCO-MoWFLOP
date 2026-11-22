"""Inputs for the 2026-10-05 full STN campaign (runs inside the mowflop-stn container).

/repo = STNs-MOCO-MoWFLOP at d5b7af9d, /work = ~/stn_full_2026-10-05 (same on bambu1 and bambu3).

Builds, without touching the repo:
  /work/raw10_orig/, /work/raw10_sparse/
                                links to runs 0-9 of the 10 originals / 8 sparse (MOWFLOP_RAW);
                                originals run on bambu1, sparse on bambu3
  /work/wflopcec26_ext/         real wflopcec26 + sparse runs 10-29 laid out as CEC runs
                                (ext variant only, mounted over raw_results/wflopcec26).
                                A real CEC run is one MOEA/D + one NSGA-II execution, so each
                                fake run is the p10 execution of each algorithm only (p only
                                changes what the STN logger records, not the search).
and writes /work/prep_report.txt.
"""
import csv
import re
import shutil
from pathlib import Path

REPO = Path("/repo")
SRC = REPO / "raw_results" / "meta_heuristics_stn_windcorrected"
CEC = REPO / "raw_results" / "wflopcec26"
WIND = REPO / "raw_results" / "wind_corrected" / "sparse_wind_map_506-513_corrected.csv"
WORK = Path("/work")
ALGOS = ("moead", "nsga2")
CONFIGS = ("p10_i50", "p50_i50", "p100_i50")
SPARSE = [f"ns{n}" for n in range(506, 514)]
report = []


def final_checkpoint(run_dir: Path, algo: str) -> Path:
    pat = re.compile(rf"_{algo}_(\d+)\.txt$")
    hits = [(int(m.group(1)), f) for f in run_dir.iterdir() if (m := pat.search(f.name))]
    n, f = max(hits)
    assert n == 1000000, f"{run_dir}: last checkpoint {n}"
    return f


# 1. raw10_<family>: links (container paths) to runs 0-9
instances = sorted(p.name for p in (SRC / "moead").iterdir() if p.name.startswith("ns"))
assert len(instances) == 18, instances
families = {"orig": [i for i in instances if i not in SPARSE], "sparse": SPARSE}
assert len(families["orig"]) == 10
for fam, insts in families.items():
    raw10 = WORK / f"raw10_{fam}"
    shutil.rmtree(raw10, ignore_errors=True)
    for algo in ALGOS:
        for inst in insts:
            for cfg in CONFIGS:
                d = raw10 / algo / inst / cfg
                d.mkdir(parents=True)
                for r in range(10):
                    target = SRC / algo / inst / cfg / str(r)
                    assert (target / "infoRun.txt").is_file(), target
                    final_checkpoint(target, algo)
                    (d / str(r)).symlink_to(target)
    (raw10 / "candidates").symlink_to(SRC / "candidates")
    report.append(f"raw10_{fam}: {len(insts)} instances x 2 algos x 3 configs x runs 0-9 = {len(insts)*60} links: " + " ".join(insts))

# 2. wflopcec26_ext: real CEC + sparse runs 10-29 as CEC runs
ext = WORK / "wflopcec26_ext"
shutil.rmtree(ext, ignore_errors=True)
shutil.copytree(CEC, ext)
wind = {}
for row in csv.DictReader(WIND.open()):
    wind[(row["instance"], row["algo"], int(row["run_id"]))] = (float(row["wind"]), float(row["angle"]))
made = 0
for inst in SPARSE:
    for algo in ALGOS:
        for r in range(10, 30):
            d = ext / algo / inst / str(r)
            d.mkdir(parents=True)
            src = final_checkpoint(SRC / algo / inst / "p10_i50" / str(r), algo)
            shutil.copyfile(src, d / f"{inst[2:]}_{algo}_1000000.txt")
            w, a = wind[(inst, algo, r)]
            (d / "log.txt").write_text(
                f"Fake CEC log: sparse run {r}, final archive of the p10_i50 execution\n"
                f"Wind: {w:.12f}\nAngle: {a:.12f}\n")
            made += 1
report.append(f"wflopcec26_ext: real CEC copied + {made} sparse fake-CEC run folders (8 x 2 x runs 10-29, p10 execution each)")

# which fake runs share a scenario with runs 0-9 (only these can enter the front)
for inst in SPARSE:
    s09 = {wind[(inst, "moead", r)] for r in range(10)}
    match = [r for r in range(10, 30) if wind[(inst, "moead", r)] in s09]
    report.append(f"  {inst}: runs 10-29 matching a 0-9 scenario: {match}")

(WORK / "prep_report.txt").write_text("\n".join(report) + "\n")
print("\n".join(report))
