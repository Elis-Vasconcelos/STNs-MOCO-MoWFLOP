"""Testes da fonte de vento (``raw_results/wind_corrected``) e do rótulo de instância.

Rode a partir de ``scripts/``::

    ../.venv/bin/python -m unittest mowflop.test.test_wind -v
"""

from __future__ import annotations

import unittest

from ..emit import config_tag, front_name, instance_label, output_name
from ..wind import cec_scenarios, scenarios, wind_map, wind_mismatches


class TestInstanceLabel(unittest.TestCase):
    def test_sparse_name_loses_underscore(self):
        self.assertEqual(instance_label("506_e-02"), "506e-02")

    def test_ns_name_is_unchanged(self):
        self.assertEqual(instance_label("ns101"), "ns101")

    def test_sparse_fields_survive_the_r_split(self):
        inst = instance_label("506_e-02")
        name = output_name("MOEAD", inst, "x60", config_tag("p100_i50"), "r06")
        fields = name.split("_")
        self.assertEqual(fields[2], "506e-02")  # plot.R/metrics leem a instância no campo 3
        self.assertEqual(fields[3], "2")  # create .R lê m em aux[4]
        self.assertEqual(
            "_".join(fields[1:7]) + "_ref.txt", front_name(inst, "x60", "p100i50", "r06")
        )


class TestWindMap(unittest.TestCase):
    def test_cec_map_matches_the_cec_logs(self):
        # a convenção antiga (nossa run r <-> run r+1 do cec) é o que o mapa registra
        ns = [inst for inst in wind_map() if inst.startswith("ns")]
        self.assertEqual(len(ns), 10)
        for inst in ns:
            cec = {run: (wind, angle) for run, wind, angle in cec_scenarios(inst)}
            for (algo, run), scenario in scenarios(inst).items():
                self.assertEqual(scenario, cec[run + 1], f"{inst} {algo} run {run}")

    def test_scenario_identity_is_wind_and_angle(self):
        ns41 = scenarios("ns41")
        self.assertEqual(ns41[("moead", 3)], (7.0, 150.0))
        self.assertEqual(ns41[("moead", 3)], ns41[("moead", 5)])

    def test_cec_instances_have_no_mismatch(self):
        for inst in (i for i in wind_map() if i.startswith("ns")):
            self.assertEqual(wind_mismatches(inst), [], inst)

    def test_sparse_algorithms_drew_winds_independently(self):
        mismatched = wind_mismatches("507_e-03")
        self.assertEqual(len(mismatched), 28)
        self.assertNotIn(6, mismatched)
        self.assertNotIn(25, mismatched)


if __name__ == "__main__":
    unittest.main()
