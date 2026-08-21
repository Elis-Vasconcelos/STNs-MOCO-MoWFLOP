"""Teste de :func:`mowflop.run_compare_r.discover_tags`.

Regressão para um bug real: ``any(d.glob(...) for algo in ...)`` é sempre
``True`` (a expressão geradora produz objetos ``glob``, não seus resultados),
então toda tag aparecia como "tem dados" para toda instância -- inclusive
``x60`` para ``ns178``, que não existe. Isso teria feito
``run_compare_r --instance ns178`` (sem ``--tags``) tentar ler arquivos
inexistentes em vez de simplesmente não incluir ``x60`` no máximo global de
Count.

Rode a partir de ``scripts/``::

    ../.venv/bin/python -m unittest mowflop.test_run_compare_r -v
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from .run_compare_r import discover_tags


class TestDiscoverTags(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _touch(self, tag: str, algo: str, instance: str) -> None:
        d = self.repo / "stns" / f"mowflop_{tag}" / algo
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{algo}_mowflop_{instance}_2_{tag}_p10i50_0_post.RData").touch()

    def test_only_tags_with_real_files_are_found(self):
        self._touch("x60", "MOEAD", "ns101")
        self._touch("x60", "NSGA2", "ns101")
        self._touch("g1.0", "MOEAD", "ns101")
        self._touch("g1.0", "MOEAD", "ns178")

        self.assertEqual(discover_tags(self.repo, "ns101"), ["g1.0", "x60"])
        self.assertEqual(discover_tags(self.repo, "ns178"), ["g1.0"])
        self.assertEqual(discover_tags(self.repo, "ns999"), [])

    def test_empty_algo_dirs_do_not_count(self):
        (self.repo / "stns" / "mowflop_x60" / "MOEAD").mkdir(parents=True)
        (self.repo / "stns" / "mowflop_x60" / "NSGA2").mkdir(parents=True)
        self.assertEqual(discover_tags(self.repo, "ns101"), [])


if __name__ == "__main__":
    unittest.main()
