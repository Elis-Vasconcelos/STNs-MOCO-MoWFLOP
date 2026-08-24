"""Testes do estágio de particionamento do MoWFLOP.

Rode a partir de ``scripts/``::

    ../.venv/bin/python -m unittest mowflop.test.test_partition -v

O teste principal é :class:`TestPmed7Regression`: a implementação é conferida
contra três números publicados pelos autores do esquema (Ochoa, Malan & Blum
2021) para os dados ``pmed7`` deles próprios -- ``|S(T)| = 423`` e
``n_total = 423`` sem particionar (Tabela 8), ``z = 19`` para um particionamento
de 60% (S6.2), e ``n_total = 312`` particionado (Tabela 8).  Se esses três
baterem, o que implementamos é o esquema deles, e não uma reinterpretação.

Estes testes usam ``tie_break="index"`` explicitamente onde o resultado
precisa ser determinístico (regressão contra os números do artigo); em todo o
resto do pacote o default de ``tie_break`` é ``"random"``.
"""

from __future__ import annotations

import glob
import math
import unittest
from pathlib import Path

import pandas as pd

from .. import entropy as entropy_mod
from .. import io_raw
from ..diagnose_entropy import load_pmed7
from ..emit import (
    build_table,
    canonical_objectives,
    check_vectors,
    config_tag,
    output_name,
    front_name,
    assign_locations,
)
from ..reference_front import front_keys, pareto_front
from ..schemes import RawScheme, build_scheme

PMED7 = io_raw.repo_root().parent / "STNs" / "pmed7"


class TestEntropy(unittest.TestCase):
    def test_known_values(self):
        # four solutions; position 0 in two of them -> p = 1/2 -> H = 1 bit
        solutions = [frozenset({0}), frozenset({0}), frozenset({1}), frozenset({2})]
        entropy = entropy_mod.position_entropy(solutions, 4)
        self.assertAlmostEqual(entropy[0], 1.0)
        self.assertAlmostEqual(entropy[1], 0.8112781244591328)  # p = 1/4
        self.assertAlmostEqual(entropy[3], 0.0)  # never used

    def test_entropy_is_bounded_by_one_bit(self):
        solutions = [frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2})]
        for value in entropy_mod.position_entropy(solutions, 3):
            self.assertLessEqual(value, 1.0 + 1e-12)

    def test_zero_percent_means_no_partitioning(self):
        # the paper: "a 0% search space partitioning corresponds to not applying
        # any search space partitioning"
        entropy = [1.0, 0.5, 0.25, 0.0]
        self.assertEqual(entropy_mod.area_partition_z(entropy, 0), 4)

    def test_area_criterion_is_monotone_in_x(self):
        entropy = sorted([1.0, 0.9, 0.5, 0.4, 0.2, 0.1, 0.0], reverse=True)
        zs = [entropy_mod.area_partition_z(entropy, x) for x in (0, 30, 60, 90)]
        self.assertEqual(zs, sorted(zs, reverse=True))

    def test_flat_curve_returns_full_space(self):
        self.assertEqual(entropy_mod.area_partition_z([0.0, 0.0, 0.0], 60), 3)

    def test_projection_defines_the_location(self):
        partition = entropy_mod.Partition(
            n=5, entropy=[1.0, 0.9, 0.1, 0.0, 0.0], order=[0, 1, 2, 3, 4], z=2
        )
        a = frozenset({0, 2})
        b = frozenset({0, 3})  # differs only outside the retained positions
        c = frozenset({1, 2})
        self.assertEqual(partition.assign(a), partition.assign(b))
        self.assertNotEqual(partition.assign(a), partition.assign(c))

    def test_z_equal_n_is_the_identity(self):
        solutions = [frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2})]
        partition = entropy_mod.build_partition(solutions, 3, z=3)
        self.assertEqual(len(partition.locations(solutions)), len(set(solutions)))

    def test_z_zero_collapses_everything(self):
        solutions = [frozenset({0, 1}), frozenset({1, 2})]
        partition = entropy_mod.build_partition(solutions, 3, z=0)
        self.assertEqual(len(partition.locations(solutions)), 1)

    def test_binary_string_and_index_list_agree(self):
        self.assertEqual(
            entropy_mod.from_binary_string("010110"), entropy_mod.from_index_list("1 3 4")
        )

    def test_tie_break_random_is_seeded(self):
        entropy = [0.5] * 6
        first = entropy_mod.rank_positions(entropy, tie_break="random", seed=7)
        second = entropy_mod.rank_positions(entropy, tie_break="random", seed=7)
        third = entropy_mod.rank_positions(entropy, tie_break="index")
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)


@unittest.skipUnless(PMED7.is_dir(), f"p-median control data not found at {PMED7}")
class TestPmed7Regression(unittest.TestCase):
    """The three numbers published by the authors for their own data."""

    @classmethod
    def setUpClass(cls):
        cls.solutions, cls.n = load_pmed7(PMED7)

    def test_unique_solution_count(self):
        # Table 8, column n_total for the full (unpartitioned) search space
        self.assertEqual(len(self.solutions), 423)
        self.assertEqual(self.n, 200)

    def test_z_for_60_percent_partitioning(self):
        # tie_break="index" para reproduzir o número publicado de forma determinística
        partition = entropy_mod.build_partition(
            self.solutions, self.n, percent=60, tie_break="index"
        )
        self.assertEqual(partition.z, 19)  # Section 6.2 of the paper

    def test_partitioned_location_count(self):
        partition = entropy_mod.build_partition(
            self.solutions, self.n, percent=60, tie_break="index"
        )
        # Table 8, column n_total for the partitioned search space
        self.assertEqual(len(partition.locations(self.solutions)), 312)

    def test_zero_percent_reproduces_the_unpartitioned_space(self):
        partition = entropy_mod.build_partition(
            self.solutions, self.n, percent=0, tie_break="index"
        )
        self.assertEqual(len(partition.locations(self.solutions)), 423)


class TestReferenceFront(unittest.TestCase):
    def test_mixed_directions(self):
        # f_cost minimised, f_power maximised
        df = pd.DataFrame(
            {
                "f_cost": [10.0, 20.0, 15.0, 15.0, 30.0],
                "f_power": [100.0, 300.0, 150.0, 200.0, 250.0],
            }
        )
        front = pareto_front(df)
        got = set(map(tuple, front.to_numpy()))
        self.assertEqual(got, {(10.0, 100.0), (15.0, 200.0), (20.0, 300.0)})

    def test_front_keys_match_r_formatting(self):
        front = pd.DataFrame({"f_cost": [1.5], "f_power": [2.25]})
        self.assertEqual(front_keys(front), {"1.500000_2.250000"})


class TestNaming(unittest.TestCase):
    def test_fields_survive_the_r_split(self):
        name = output_name("MOEAD", "ns101", "x60", config_tag("p100_i50"))
        fields = name.split("_")
        self.assertEqual(fields[3], "2")  # create .R reads m from aux[4]
        self.assertEqual(
            "_".join(fields[1:7]) + "_ref.txt", front_name("ns101", "x60", "p100i50")
        )

    def test_underscore_in_a_field_is_rejected(self):
        with self.assertRaises(ValueError):
            output_name("MOEAD", "ns101", "x_60", "p100i50")


def _fake_log() -> pd.DataFrame:
    """Two runs x two vectors x three recordings of a tiny instance."""
    rows = []
    layouts = ["0 1", "0 2", "1 2", "0 3"]
    for run in (0, 1):
        for vector in (0, 1):
            for iteration in range(3):
                layout = layouts[(run + vector + iteration) % len(layouts)]
                rows.append(
                    {
                        "algorithm": "moead",
                        "instance": "fake",
                        "run_id": run,
                        "vector_id": vector,
                        "generation": iteration * 50,
                        "iteration": iteration,
                        "f_cost": 100.0 + iteration + run,
                        "f_power": 10.0 + vector,
                        "weight1": float(vector),
                        "weight2": 1.0 - vector,
                        "occupied": layout,
                    }
                )
    return pd.DataFrame(rows)


class TestEmit(unittest.TestCase):
    def setUp(self):
        self.df = _fake_log()
        self.front = pareto_front(self.df)
        scheme = RawScheme()
        self.located, self.projections, self.ids = assign_locations(self.df, scheme)
        self.objectives = canonical_objectives(self.located, self.front)
        self.table = build_table(self.located, self.objectives)

    def test_column_order_is_what_create_r_expects(self):
        self.assertEqual(
            list(self.table.columns),
            ["f1", "f2", "Solution1", "Solution2", "Run", "Gen", "Vector",
             "Weight1", "Weight2"],
        )

    def test_no_recording_is_lost(self):
        self.assertEqual(len(self.table), len(self.df))

    def test_run_is_one_based_and_gen_is_the_recording_index(self):
        # create .R filters Run <= nRun with nRun = max(Run): a zero-based Run
        # would silently drop run 0
        self.assertEqual(sorted(self.table["Run"].unique()), [1, 2])
        self.assertEqual(sorted(self.table["Gen"].unique()), [0, 1, 2])

    def test_last_recording_is_a_self_loop(self):
        last = self.table.sort_values("Gen").groupby(["Run", "Vector"]).tail(1)
        self.assertTrue((last["Solution1"] == last["Solution2"]).all())

    def test_trajectories_are_continuous(self):
        ordered = self.table.sort_values(["Run", "Vector", "Gen"])
        for _, group in ordered.groupby(["Run", "Vector"]):
            targets = group["Solution2"].tolist()[:-1]
            sources = group["Solution1"].tolist()[1:]
            self.assertEqual(targets, sources)

    def test_one_objective_vector_per_location(self):
        # otherwise create .R's group_by(f1, f2, Solution1, Vector) would split
        # a single location into several nodes
        counts = self.table.groupby("Solution1")[["f1", "f2"]].nunique()
        self.assertTrue((counts == 1).all().all())

    def test_representative_is_a_visited_solution(self):
        visited = set(map(tuple, self.df[["f_cost", "f_power"]].to_numpy()))
        for _, row in self.objectives.iterrows():
            self.assertIn((row["f1"], row["f2"]), visited)

    def test_front_membership_wins_over_lexicographic_order(self):
        keys = front_keys(self.front)
        for solution, group in self.located.groupby("Solution1"):
            pairs = group[["f_cost", "f_power"]].drop_duplicates()
            has_front = any(
                f"{c:.6f}_{p:.6f}" in keys for c, p in pairs.itertuples(index=False)
            )
            chosen = self.objectives.loc[
                self.objectives["Solution1"] == solution
            ].iloc[0]
            if has_front:
                self.assertTrue(chosen["in_front"])

    def test_vector_weight_consistency_is_checked(self):
        check_vectors(self.table)
        broken = self.table.copy()
        broken.loc[0, "Weight1"] = "9.000000"
        with self.assertRaises(ValueError):
            check_vectors(broken)


class TestSchemes(unittest.TestCase):
    def test_raw_is_one_location_per_solution(self):
        solutions = [frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 1})]
        scheme = build_scheme("raw", solutions, 3)
        self.assertEqual(len({scheme.assign(s) for s in solutions}), 2)

    def test_entropy_scheme_matches_partition(self):
        solutions = [frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2})]
        scheme = build_scheme("entropy", solutions, 3, percent=60)
        ids = {scheme.assign(s) for s in solutions}
        self.assertEqual(len(ids), len(scheme.partition.locations(solutions)))

    def test_unknown_scheme(self):
        with self.assertRaises(ValueError):
            build_scheme("hamming", [], 1)


def _campaign_available() -> bool:
    try:
        return io_raw.raw_root().is_dir()
    except FileNotFoundError:
        return False


@unittest.skipUnless(_campaign_available(), "campaign logs not present")
class TestCampaignInvariants(unittest.TestCase):
    def test_occupied_has_one_entry_per_turbine(self):
        inv = io_raw.inventory()
        instance, config = inv.iloc[0]["instance"], inv.iloc[0]["config"]
        df = io_raw.load_trajectories(instance, config).head(2000)
        sizes = df["occupied"].map(lambda s: len(s.split())).unique()
        self.assertEqual(len(sizes), 1)

    def test_indices_are_within_the_candidate_table(self):
        inv = io_raw.inventory()
        instance, config = inv.iloc[0]["instance"], inv.iloc[0]["config"]
        n = io_raw.n_positions(instance)
        df = io_raw.load_trajectories(instance, config).head(500)
        for text in df["occupied"].head(50):
            positions = entropy_mod.from_index_list(text)
            self.assertLess(max(positions), n)
            self.assertGreaterEqual(min(positions), 0)

    def test_decoded_layout_matches_the_layout_file(self):
        """Cross-check of the index -> (x, y) map against the C++ output."""
        inv = io_raw.inventory()
        instance, config = inv.iloc[0]["instance"], inv.iloc[0]["config"]
        run_dir = None
        for path in io_raw.discover()["path"]:
            path = Path(path)
            if f"/{instance}/{config}/" in str(path):
                run_dir = path.parent
                break
        layouts = sorted(glob.glob(str(run_dir / "*_layout.txt")))
        if not layouts:
            self.skipTest("no layout file next to the logs")
        candidates = io_raw.load_candidates(instance)
        coordinates = set(
            zip(candidates["x"].round(3), candidates["y"].round(3), strict=True)
        )
        found = 0
        with open(layouts[0], "r", encoding="utf-8") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) < 2:
                    continue
                try:
                    x, y = float(parts[0]), float(parts[1])
                except ValueError:
                    continue
                if (round(x, 3), round(y, 3)) in coordinates:
                    found += 1
                if found >= 5:
                    break
        self.assertGreaterEqual(found, 5, "layout coordinates not found among candidates")


if __name__ == "__main__":
    unittest.main()
