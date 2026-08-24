"""Testes do esquema de particionamento por grade de ocupação (`geometry.py`, `grid.py`).

Rode a partir de ``scripts/``::

    ../.venv/bin/python -m unittest mowflop.test.test_grid -v

Os testes puros (sem dependência de dados da campanha) cobrem: a fórmula da
área do polígono (shoelace) contra formas de área conhecida; a regra
adaptativa (eq. 6, incluindo o piso sigma); a atribuição de célula e a
assinatura de ocupação (Definição 1) com casos construídos à mão, onde é
possível confirmar a resposta certa sem rodar nada. Os testes de integração
(:class:`TestGridAgainstCampaign`) precisam dos dados reais de instância e da
campanha e são pulados se não estiverem presentes.
"""

from __future__ import annotations

import math
import unittest

from .. import geometry
from .. import grid as grid_mod
from .. import io_raw
from ..schemes import GridScheme, build_scheme


class TestPolygonArea(unittest.TestCase):
    def test_unit_square(self):
        square = [(0, 0), (1, 0), (1, 1), (0, 1)]
        self.assertAlmostEqual(geometry.polygon_area(square), 1.0)

    def test_right_triangle(self):
        triangle = [(0, 0), (4, 0), (0, 3)]
        self.assertAlmostEqual(geometry.polygon_area(triangle), 6.0)

    def test_area_independent_of_winding_direction(self):
        ccw = [(0, 0), (2, 0), (2, 2), (0, 2)]
        cw = list(reversed(ccw))
        self.assertAlmostEqual(geometry.polygon_area(ccw), geometry.polygon_area(cw))


class TestCellSide(unittest.TestCase):
    def _geometry(self, A, tau, sigma):
        return geometry.SiteGeometry(
            A=A, W=1000.0, H=1000.0, xmin=0.0, ymin=0.0,
            tau=tau, sigma=sigma, candidate_spacing=1.0,
        )

    def test_matches_eq6_formula(self):
        g = self._geometry(A=900.0, tau=9, sigma=1.0)
        # ell = kappa * sqrt(A/tau) = 2 * sqrt(100) = 20, well above sigma=1
        self.assertAlmostEqual(geometry.cell_side(2.0, g), 20.0)

    def test_floor_at_sigma(self):
        g = self._geometry(A=900.0, tau=9, sigma=50.0)
        # kappa*sqrt(A/tau) = 0.1*10 = 1, below sigma=50 -> floor binds
        self.assertAlmostEqual(geometry.cell_side(0.1, g), 50.0)

    def test_rejects_nonpositive_kappa(self):
        g = self._geometry(A=900.0, tau=9, sigma=1.0)
        with self.assertRaises(ValueError):
            geometry.cell_side(0.0, g)
        with self.assertRaises(ValueError):
            geometry.cell_side(-1.0, g)


class TestCellOf(unittest.TestCase):
    def _geometry(self):
        return geometry.SiteGeometry(
            A=1.0, W=100.0, H=100.0, xmin=0.0, ymin=0.0,
            tau=1, sigma=1.0, candidate_spacing=1.0,
        )

    def test_grid_indexing(self):
        g = self._geometry()
        # 10x10 grid of cells with ell=10; ncols=10
        self.assertEqual(grid_mod.cell_of(0.0, 0.0, g, ell=10.0, ncols=10), 0)
        self.assertEqual(grid_mod.cell_of(15.0, 0.0, g, ell=10.0, ncols=10), 1)
        self.assertEqual(grid_mod.cell_of(0.0, 15.0, g, ell=10.0, ncols=10), 10)
        self.assertEqual(grid_mod.cell_of(25.0, 35.0, g, ell=10.0, ncols=10), 32)

    def test_offset_origin(self):
        g = geometry.SiteGeometry(
            A=1.0, W=100.0, H=100.0, xmin=500.0, ymin=500.0,
            tau=1, sigma=1.0, candidate_spacing=1.0,
        )
        self.assertEqual(grid_mod.cell_of(500.0, 500.0, g, ell=10.0, ncols=10), 0)
        self.assertEqual(grid_mod.cell_of(510.0, 500.0, g, ell=10.0, ncols=10), 1)


class TestSignature(unittest.TestCase):
    def setUp(self):
        self.geometry = geometry.SiteGeometry(
            A=1.0, W=100.0, H=100.0, xmin=0.0, ymin=0.0,
            tau=3, sigma=1.0, candidate_spacing=1.0,
        )
        # 4 candidates: 0,1 share a cell (ell=10, both in cell (0,0)); 2 is in
        # a different cell; 3 is in yet another different cell.
        self.coords = {0: (1.0, 1.0), 1: (2.0, 2.0), 2: (15.0, 1.0), 3: (1.0, 25.0)}
        self.ell = 10.0
        self.ncols = 10

    def test_two_positions_same_cell_count_together(self):
        sig = grid_mod.signature({0, 1}, self.coords, self.geometry, self.ell, self.ncols)
        self.assertEqual(sig, frozenset({(0, 2)}))

    def test_positions_in_different_cells_stay_separate(self):
        sig = grid_mod.signature({0, 2, 3}, self.coords, self.geometry, self.ell, self.ncols)
        # cell 0: (1,1) row=0 col=0; cell 1: (15,1) row=0 col=1; cell 20: (1,25) row=2 col=0
        self.assertEqual(sig, frozenset({(0, 1), (1, 1), (20, 1)}))

    def test_same_signature_different_raw_solutions_share_location(self):
        # {0} and {1} are different raw solutions (different candidate index)
        # but land in the same cell -> same signature -> same location id.
        sig_a = grid_mod.signature({0}, self.coords, self.geometry, self.ell, self.ncols)
        sig_b = grid_mod.signature({1}, self.coords, self.geometry, self.ell, self.ncols)
        self.assertEqual(sig_a, sig_b)
        self.assertEqual(grid_mod.location_id(sig_a), grid_mod.location_id(sig_b))

    def test_different_signatures_get_different_ids(self):
        sig_a = grid_mod.signature({0, 2}, self.coords, self.geometry, self.ell, self.ncols)
        sig_b = grid_mod.signature({0, 3}, self.coords, self.geometry, self.ell, self.ncols)
        self.assertNotEqual(sig_a, sig_b)
        self.assertNotEqual(grid_mod.location_id(sig_a), grid_mod.location_id(sig_b))

    def test_location_id_has_expected_prefix(self):
        sig = grid_mod.signature({0}, self.coords, self.geometry, self.ell, self.ncols)
        loc_id = grid_mod.location_id(sig)
        self.assertTrue(loc_id.startswith(grid_mod.LOCATION_PREFIX))


class TestNCells(unittest.TestCase):
    """n_cells must follow the paper's eq. 7 (G ~= A/ell^2), not the bounding box."""

    def test_uses_true_area_not_bounding_box(self):
        # bounding box W*H = 10000, but true area A = 100 -- a sparse/irregular
        # site where the bounding box would badly overstate G if used.
        g = geometry.SiteGeometry(
            A=100.0, W=100.0, H=100.0, xmin=0.0, ymin=0.0,
            tau=1, sigma=1.0, candidate_spacing=1.0,
        )
        partition = grid_mod.GridPartition(
            instance="synthetic", geometry=g, kappa=1.0, ell=10.0,
            ncols=10, nrows=10, coords={},
        )
        # A/ell^2 = 100/100 = 1, NOT ncols*nrows = 100
        self.assertEqual(partition.n_cells, 1)

    def test_reduces_to_tau_over_kappa_squared_away_from_sigma_floor(self):
        g = geometry.SiteGeometry(
            A=900.0, W=1000.0, H=1000.0, xmin=0.0, ymin=0.0,
            tau=9, sigma=1.0, candidate_spacing=1.0,
        )
        kappa = 1.5
        ell = geometry.cell_side(kappa, g)  # not at the sigma floor
        partition = grid_mod.GridPartition(
            instance="synthetic", geometry=g, kappa=kappa, ell=ell,
            ncols=1, nrows=1, coords={},
        )
        expected = math.ceil(g.tau / kappa**2)
        self.assertEqual(partition.n_cells, expected)


def _instances_available() -> bool:
    try:
        geometry.instances_root()
    except FileNotFoundError:
        return False
    return True


def _campaign_available() -> bool:
    try:
        return io_raw.raw_root().is_dir()
    except FileNotFoundError:
        return False


@unittest.skipUnless(_instances_available() and _campaign_available(), "instance/campaign data not present")
class TestGridAgainstCampaign(unittest.TestCase):
    """Integration checks against real instance geometry and campaign data."""

    def test_ns48_is_the_smallest_tau_instance(self):
        # README's kappa justification depends on this; if it stops being true
        # the three regimes (0.5/1.0/2.0) need re-deriving against a new
        # binding instance.
        instances = ["ns48", "ns101", "ns178", "ns440"]
        taus = {inst: geometry.load_site_geometry(inst).tau for inst in instances}
        self.assertEqual(min(taus, key=taus.get), "ns48")

    def test_ell_matches_eq6_for_ns101(self):
        g = geometry.load_site_geometry("ns101")
        expected = max(1.0 * math.sqrt(g.A / g.tau), g.sigma)
        partition = grid_mod.build_partition("ns101", kappa=1.0)
        self.assertAlmostEqual(partition.ell, expected)

    def test_reduction_is_monotonic_in_kappa(self):
        """Higher kappa -> bigger cells -> at least as much aggregation."""
        df = io_raw.load_trajectories("ns101", "p10_i50")
        texts = df["occupied"].unique()[:500]
        from .. import entropy as entropy_mod
        solutions = [entropy_mod.from_index_list(t) for t in texts]

        counts = {}
        for kappa in [0.5, 1.0, 2.0]:
            scheme = GridScheme.build("ns101", kappa)
            counts[kappa] = len({scheme.assign(s) for s in solutions})

        self.assertGreaterEqual(counts[0.5], counts[1.0])
        self.assertGreaterEqual(counts[1.0], counts[2.0])

    def test_build_scheme_dispatches_to_grid(self):
        scheme = build_scheme("grid", [], 0, instance="ns101", kappa=1.0)
        self.assertIsInstance(scheme, GridScheme)

    def test_build_scheme_grid_requires_instance_and_kappa(self):
        with self.assertRaises(ValueError):
            build_scheme("grid", [], 0)

    def test_multi_zone_spacing_is_not_a_cross_zone_artifact(self):
        # ns203 has 2 zones; pooling coordinates across zones before measuring
        # nearest-neighbor distance used to give a spurious ~0.34m (two
        # candidates from *different* zones happening to nearly align on one
        # axis). Per-zone nearest-neighbor should land in the same ballpark
        # as every other instance's real candidate spacing (~150-160m).
        spacing = geometry.estimate_candidate_spacing("ns203")
        self.assertGreater(spacing, 100.0)


if __name__ == "__main__":
    unittest.main()
