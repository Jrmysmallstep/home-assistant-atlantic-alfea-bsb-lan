"""Regression checks for explicit circulator display in the synoptique."""
from pathlib import Path
import unittest

CARD = (Path(__file__).resolve().parents[1] /
        "custom_components/atlantic_alfea_controller/www/pac-synoptique-card.js")


class CirculatorCardTests(unittest.TestCase):
    def test_pump_entities_discovered_and_shown(self):
        code = CARD.read_text(encoding="utf-8")
        self.assertIn("pump1:           ['binary_sensor','C1 - Circulateur']", code)
        self.assertIn("pump2:           ['binary_sensor','C2 - Circulateur']", code)
        self.assertIn("pump:this._b(", code)
        for value in ("Circulateur en marche", "Circulateur arrêté",
                      "Circulateur indisponible", "— Circulateur"):
            self.assertIn(value, code)

    def test_no_ambiguous_regime_badge(self):
        code = CARD.read_text(encoding="utf-8")
        self.assertNotIn("Régime : ${clean(c.regime", code)
        self.assertIn("'pump1','pump2'", code)


if __name__ == "__main__":
    unittest.main()
