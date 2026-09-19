"""Testes de ``partition_metrics.py`` (``step_len``, ``R(κ)``, ``D(κ)``).

Rode a partir de ``scripts/``::

    ../.venv/bin/python -m unittest mowflop.test.test_partition_metrics -v

Os testes puros usam casos construídos à mão -- ``step_len`` no exemplo de
assinatura abaixo, o conjunto de arestas contra :func:`mowflop.emit.build_table`
(que é o que o ``create .R`` lê) e o diâmetro contra casos à mão e força
bruta.  :class:`TestAgainstCampaign` precisa dos logs da campanha e é pulado se
eles não estiverem presentes.
"""

from __future__ import annotations

import itertools
import math
import random
import unittest

import numpy as np
import pandas as pd

from .. import io_raw
from .. import partition_metrics as pm
from ..emit import assign_locations, build_table
from ..schemes.schemes import RawScheme

# Exemplo de assinatura: grade 2x2 (células g1..g4), τ = 3. A e B ocupam as
# mesmas células (mesma localização) e C desloca uma turbina de g1 para g2
SIG_A = {1: 2, 4: 1}  # o(A) = (2, 0, 0, 1)
SIG_B = {1: 2, 4: 1}  # o(B) = (2, 0, 0, 1)
SIG_C = {1: 1, 2: 1, 4: 1}  # o(C) = (1, 1, 0, 1)
SIGNATURES = {"A": SIG_A, "B": SIG_B, "C": SIG_C}


def _log(steps: list[tuple[int, int, int, str]]) -> pd.DataFrame:
    """Log mínimo a partir de ``(run_id, vector_id, iteration, Solution1)``."""
    return pd.DataFrame(steps, columns=["run_id", "vector_id", "iteration", "Solution1"])


class TestStepLen(unittest.TestCase):
    def test_signature_example(self):
        self.assertAlmostEqual(pm.edge_step(SIG_A, SIG_C, 3), 1 / 3)
        self.assertEqual(pm.edge_step(SIG_A, SIG_B, 3), 0.0)

    def test_mean_over_distinct_edges(self):
        # A->C duas vezes e o self-loop final C->C: E = {A->C, C->A, C->C}
        edges = pm.trajectory_edges(_log([(0, 0, 0, "A"), (0, 0, 1, "C"), (0, 0, 2, "A"), (0, 0, 3, "C")]))
        self.assertEqual(len(edges), 3)
        self.assertAlmostEqual(pm.step_len(edges, SIGNATURES, 3), (1 / 3 + 1 / 3 + 0) / 3)

    def test_repeated_edges_count_once(self):
        edges = pm.trajectory_edges(_log([(0, 0, 0, "A"), (0, 0, 1, "C"), (1, 0, 0, "A"), (1, 0, 1, "C")]))
        # {A->C, C->C}: a aresta A->C aparece em duas runs e conta uma vez
        self.assertEqual(len(edges), 2)
        self.assertAlmostEqual(pm.step_len(edges, SIGNATURES, 3), (1 / 3 + 0) / 2)

    def test_raw_signature_is_hamming(self):
        signatures = pm.location_signatures(
            "raw", {"x": frozenset({1, 2, 3}), "y": frozenset({1, 2, 9})}, {"x": "X", "y": "Y"}
        )
        # uma turbina muda de posição: Hamming 2, 2/(2*3)
        self.assertAlmostEqual(pm.edge_step(signatures["X"], signatures["Y"], 3), 1 / 3)

    def test_entropy_has_no_signature(self):
        self.assertIsNone(pm.location_signatures("entropy", {}, {}))


class TestEdgesMatchCreateR(unittest.TestCase):
    def test_same_pairs_as_build_table(self):
        rng = random.Random(0)
        rows = []
        for run, vector in itertools.product(range(2), range(3)):
            iterations = list(range(6))
            rng.shuffle(iterations)  # a ordem no log não pode importar
            for it in iterations:
                rows.append({
                    "run_id": run, "vector_id": vector, "iteration": it,
                    "Solution1": rng.choice("ABCD"), "weight1": vector / 2, "weight2": 1 - vector / 2,
                })
        log = pd.DataFrame(rows)
        objectives = pd.DataFrame({"Solution1": list("ABCD"), "f1": 1.0, "f2": 1.0})
        expected = set(map(tuple, build_table(log, objectives)[["Solution1", "Solution2"]].to_numpy()))
        got = set(map(tuple, pm.trajectory_edges(log).to_numpy()))
        self.assertEqual(got, expected)


class TestDiameter(unittest.TestCase):
    @staticmethod
    def brute(points) -> float:
        pts = np.asarray(points, dtype=float)
        if len(pts) < 2:
            return 0.0
        return float(max(np.linalg.norm(p - q) for p, q in itertools.combinations(pts, 2)))

    def test_small_sets(self):
        self.assertEqual(pm.diameter([[1.0, 1.0]]), 0.0)
        self.assertEqual(pm.diameter([[1.0, 1.0], [1.0, 1.0]]), 0.0)
        self.assertAlmostEqual(pm.diameter([[0.0, 0.0], [3.0, 4.0]]), 5.0)

    def test_collinear(self):
        points = [[t, 2 * t] for t in (0.0, 0.3, 0.1, 1.0, 0.7)]
        self.assertAlmostEqual(pm.diameter(points), self.brute(points))

    def test_random_against_brute_force(self):
        rng = np.random.default_rng(0)
        for size in (3, 4, 10, 200):
            points = rng.uniform(1.0, 2.0, size=(size, 2))
            self.assertAlmostEqual(pm.diameter(points), self.brute(points))

    def test_distortion_weights_by_visits(self):
        located = pd.DataFrame({
            "Solution1": ["L1", "L1", "L1", "L2"],
            "f_cost": [0.0, 0.0, 3.0, 7.0],
            "f_power": [0.0, 0.0, 4.0, 7.0],
        })
        # d(L1) = 5 com w = 3, d(L2) = 0 com w = 1
        self.assertAlmostEqual(pm.distortion(located), 15 / 4)


def _campaign_available() -> bool:
    try:
        return io_raw.raw_root().is_dir()
    except FileNotFoundError:
        return False


@unittest.skipUnless(_campaign_available(), "campaign logs not present")
class TestAgainstCampaign(unittest.TestCase):
    def test_raw_single_scenario_does_not_merge_or_distort(self):
        df = io_raw.load_trajectories("ns101", "p10_i50", algorithms=["moead"])
        run = df[df["run_id"] == df["run_id"].min()]
        located, projections, ids = assign_locations(run, RawScheme())
        signatures = pm.location_signatures("raw", projections, ids)
        metrics = pm.dataset_metrics(
            located, signatures, io_raw.n_positions("ns101"), normalize=True
        )
        self.assertEqual(metrics["R"], 0.0)
        # um cenário: cada layout tem um único objetivo, a menos do ruído de
        # reavaliação (f_cost ~1e8 difere em ~1e-6, 1e-14 relativo, em ns101 r0)
        scale = run[["f_cost", "f_power"]].abs().to_numpy().max()
        self.assertLess(metrics["D"], 1e-12 * scale)
        self.assertTrue(0.0 <= metrics["step_len"] <= 1.0)
        self.assertFalse(math.isnan(metrics["step_len"]))

    def test_aggregated_dataset_reports_wind_floor_distortion(self):
        """No agregado ``D`` também sai, mas carrega um piso de vento.

        As runs vêm em réguas de vento diferentes, então o ``raw`` agregado --
        onde nada é fundido, ``R = 0`` -- ainda reporta ``D`` > 0.
        """
        df = io_raw.load_trajectories("ns101", "p10_i50", algorithms=["moead"])
        self.assertGreater(df["run_id"].nunique(), 1)  # é mesmo um agregado
        located, projections, ids = assign_locations(df, RawScheme())
        signatures = pm.location_signatures("raw", projections, ids)
        metrics = pm.dataset_metrics(
            located, signatures, io_raw.n_positions("ns101"), normalize=True
        )
        self.assertFalse(math.isnan(metrics["D"]))
        self.assertGreater(metrics["D"], 0.0)  # o piso de vento
        # R e step_len não dependem do vento e continuam válidos no agregado
        self.assertEqual(metrics["R"], 0.0)
        self.assertFalse(math.isnan(metrics["step_len"]))


if __name__ == "__main__":
    unittest.main()
