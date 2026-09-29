"""Tests unitaires pour le lecteur de BASE_CONNAISSANCES_AGRICOLES."""

from __future__ import annotations

import unittest
from pathlib import Path

from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase


class TestCameroonKnowledgeBase(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1] / "BASE_CONNAISSANCES_AGRICOLES"
        self.kb = CameroonKnowledgeBase(root)

    def test_list_familles(self) -> None:
        familles = self.kb.list_familles()
        self.assertGreaterEqual(len(familles), 7)
        codes = {f["code"] for f in familles}
        self.assertIn("FAM_MARAICHAGE", codes)
        self.assertIn("FAM_TUBERCULES_RACINES", codes)
        self.assertIn("FAM_CEREALES", codes)

    def test_get_culture(self) -> None:
        tomate = self.kb.get_culture("CULT_TOMATE")
        self.assertIsNotNone(tomate)
        self.assertEqual(tomate["nom_scientifique"], "Solanum lycopersicum")
        self.assertEqual(tomate["famille_code"], "FAM_MARAICHAGE")

        pdt = self.kb.get_culture("pomme_de_terre")
        self.assertIsNotNone(pdt)
        self.assertEqual(pdt["code"], "CULT_POMME_DE_TERRE")

    def test_varietes(self) -> None:
        vars_tom = self.kb.get_varietes_culture("CULT_TOMATE")
        self.assertGreaterEqual(len(vars_tom), 3)
        var_codes = {v["code"] for v in vars_tom}
        self.assertIn("VAR_TOM_COBRA", var_codes)

        vars_pdt = self.kb.get_varietes_culture("CULT_POMME_DE_TERRE")
        self.assertGreaterEqual(len(vars_pdt), 3)
        pdt_codes = {v["code"] for v in vars_pdt}
        self.assertIn("VAR_PDT_CIPIRA", pdt_codes)

    def test_sols(self) -> None:
        sols = self.kb.list_sols()
        self.assertGreaterEqual(len(sols), 6)
        volc = self.kb.get_sol("SOL_VOLCANIQUE")
        self.assertIsNotNone(volc)
        self.assertIn("Andosols", volc["nom"])

        sols_fav = self.kb.get_sols_favorables("CULT_TOMATE")
        self.assertTrue(any(s["code"] == "SOL_VOLCANIQUE" for s in sols_fav))

    def test_10_regions(self) -> None:
        regions = self.kb.list_regions()
        self.assertEqual(len(regions), 10)
        codes = {r["code"] for r in regions}
        expected = {
            "REG_AD", "REG_CE", "REG_ES", "REG_EN", "REG_LT",
            "REG_NO", "REG_NW", "REG_OU", "REG_SU", "REG_SW"
        }
        self.assertEqual(codes, expected)

    def test_localites_ouest(self) -> None:
        locs = self.kb.list_localites("REG_OU")
        self.assertGreaterEqual(len(locs), 4)
        names = {loc["nom"] for loc in locs}
        self.assertIn("Bafoussam", names)
        self.assertIn("Dschang", names)
        self.assertIn("Foumban", names)
        self.assertIn("Mbouda", names)

    def test_resolve_culture_links(self) -> None:
        resolved = self.kb.resolve_culture_links("CULT_TOMATE")
        self.assertNotIn("error", resolved)
        self.assertGreater(len(resolved["sols_favorables"]), 0)
        self.assertGreater(len(resolved["regions_principales"]), 0)
        self.assertGreater(len(resolved["engrais_recommandes"]), 0)
        self.assertGreater(len(resolved["varietes"]), 0)
        self.assertGreater(len(resolved["photos"]), 0)


if __name__ == "__main__":
    unittest.main()
