"""Testes do ``rank_stab``.

Rode a partir de ``scripts/``::

    ../.venv/bin/python -m unittest mowflop.test.test_rank_stability -v
"""

from __future__ import annotations

import unittest

import pandas as pd

from ..schemes.shannon_entropy import rank_stability as rs


def frame(rows: list[tuple[int, str]]) -> pd.DataFrame:
    """DataFrame mínimo com as colunas que o ``rank_stab`` lê."""
    return pd.DataFrame(rows, columns=["run_id", "occupied"])


class TestRankStab(unittest.TestCase):
    def test_identical_halves_are_perfectly_stable(self):
        # runs 0-1 e 2-3 visitam as mesmas soluções
        solutions = ["0 1", "1 2", "0 3", "2 4"]
        df = frame([(run, s) for run in range(4) for s in solutions])
        self.assertAlmostEqual(rs.rank_stab(df, 6)["rank_stab"], 1.0)

    def test_half_entropy_only_sees_its_runs(self):
        # a posição 5 só aparece na run 3
        df = frame([(0, "0 1"), (1, "1 2"), (2, "0 1"), (3, "4 5")])
        h = rs.half_entropy(df, [0, 1], 6)
        self.assertEqual(h[5], 0.0)
        self.assertGreater(h[0], 0.0)

    def test_positions_active_counts_either_half(self):
        # metade 1 usa as posições 0-2, metade 2 usa 3-5, cada uma em 2 de 3
        # soluções (p = 1 também dá H = 0); as posições 6-9 nunca aparecem
        df = frame([(0, "0 1"), (0, "1 2"), (1, "0 2"),
                    (2, "3 4"), (2, "4 5"), (3, "3 5")])
        self.assertEqual(rs.rank_stab(df, 10)["positions_active"], 6)


if __name__ == "__main__":
    unittest.main()
