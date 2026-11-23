"""Compare STN metrics of a new campaign against a reference build.

usage: compare_metrics.py NEW_METRICS_DIR NEW_SUFFIX REF_METRICS_DIR REF_SUFFIX LEVEL...
  e.g. new/metrics noextnorm build_originals/metrics norm x60 g1.0
Graph columns (nodes, disc_rate, edge_ratio, shared_vec) must match exactly.
Front columns (pareto, par_strength, n_end, path_par, path_par_reach) are reported, not required to match.
"""
import csv
import sys
from pathlib import Path

GRAPH = ["nodes", "disc_rate", "edge_ratio", "shared_vec"]
FRONT = ["pareto", "par_strength", "n_end", "path_par", "path_par_reach"]
new_dir, new_suf, ref_dir, ref_suf, *levels = sys.argv[1:]
bad = 0
for lvl in levels:
    for algo in ("MOEAD", "NSGA2"):
        def load(d, suf):
            rows = csv.DictReader(open(Path(d) / f"mowflop_{lvl}{suf}_{algo}_stn_metrics.csv"))
            return {(r["instance"], r["p"], r["run"]): r for r in rows}
        new, ref = load(new_dir, new_suf), load(ref_dir, ref_suf)
        keys_ok = set(new) == set(ref)
        g_diff = [(k, c, ref[k][c], new[k][c]) for k in ref if k in new for c in GRAPH if ref[k][c] != new[k][c]]
        f_diff = sum(1 for k in ref if k in new for c in FRONT if ref[k][c] != new[k][c])
        bad += (not keys_ok) + len(g_diff)
        print(f"{lvl} {algo}: STNs new={len(new)} ref={len(ref)} same_keys={keys_ok} "
              f"graph_mismatches={len(g_diff)} front_cells_differing={f_diff}")
        for d in g_diff[:5]:
            print("   ", d)
print("RESULT:", "graph metrics identical" if bad == 0 else f"{bad} problems")
