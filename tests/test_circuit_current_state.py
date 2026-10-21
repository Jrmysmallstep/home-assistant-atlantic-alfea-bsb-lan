"""Offline regression checks for readable circuit activity sensors."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller"


class CircuitCurrentStateTests(unittest.TestCase):
    def test_sensor_mirrors_climate_hvac_action(self):
        source = (ROOT / "sensor.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == "AlfeaCircuitSeasonStateSensor")
        code = ast.unparse(cls)
        self.assertIn("climate.attributes.get(", code)
        self.assertIn("hvac_action", code)
        for key, label in (("heating", "Chauffage"), ("cooling", "Refroidissement"),
                           ("idle", "En attente"), ("off", "Arrêt")):
            self.assertIn(key, code)
            self.assertIn(label, code)
        self.assertIn("current_state", code)

    def test_native_regime_is_diagnostic_only(self):
        source = (ROOT / "sensor.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == "AlfeaCircuitSeasonStateSensor")
        code = ast.unparse(cls)
        self.assertIn("regime_bsb", code)
        self.assertIn("etat_bsb_brut", code)
        self.assertIn("track_entities", code)
        self.assertNotIn("async_set_native_value", code)


if __name__ == "__main__":
    unittest.main()
