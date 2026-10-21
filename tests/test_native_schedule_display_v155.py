"""V1.5.5: programme horaire lecture seule, commandes inchangées."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components" / "atlantic_alfea_controller" / "climate.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
KLASS = next(node for node in TREE.body if isinstance(node, ast.ClassDef) and node.name == "AlfeaCircuitClimate")
METHOD = next(node for node in KLASS.body if isinstance(node, ast.FunctionDef) and node.name == "_scheduled_profile")

class TestNativeScheduleDisplay(unittest.TestCase):
    def test_program_codes(self):
        # Run the actual schedule method, not a copied implementation.
        glob = {
            "_PROFILE_REDUCED": "reduced",
            "_PROFILE_COMFORT": "comfort",
            "state_value": lambda hass, source: hass["value"],
            "split_bsb_status": lambda value: ((int(value.split(" - ", 1)[0]), value.split(" - ", 1)[1]) if value and " - " in value and value.split(" - ", 1)[0].isdigit() else (None, value)),
            "status_uses_reduced_setpoint": lambda v: bool(v and ("réduit" in v.lower() or "reduit" in v.lower() or "eco" in v.lower())),
            "status_uses_comfort_setpoint": lambda v: bool(v and "confort" in v.lower()),
        }
        exec(compile(ast.Module(body=[METHOD], type_ignores=[]), str(SOURCE), "exec"), glob)
        fn = glob["_scheduled_profile"]
        class Fake:
            def __init__(self, circuit, value):
                self._circuit = circuit
                self.hass = {"value": value}
                self.sources = []
            def _source(self, key, parameter):
                self.sources.append((key, parameter))
                return "sensor.program"
        for circuit, raw, expected in (
            (1, "2 - Allure confort", "comfort"),
            (2, "1 - Allure Réduit", "reduced"),
            (2, "122 - Limitation de la température ambiante", None),
            (2, None, None),
        ):
            with self.subTest(circuit=circuit, value=raw):
                f = Fake(circuit, raw)
                self.assertEqual(fn(f), expected)
                param = 10112 if circuit == 1 else 10122
                self.assertEqual(f.sources, [(f"program_diagnostic_{param}", param)])

    def test_write_selection_not_replaced(self):
        climate = SOURCE.read_text(encoding="utf-8")
        self.assertIn("profile = self._active_profile(mode)", climate)
        self.assertIn("scheduled_profile = self._scheduled_profile()", climate)
        self.assertIn("display_profile = scheduled_profile or profile", climate)
        self.assertIn('"ecriture_consigne_autorisee": profile is not None', climate)

    def test_bundled_card_is_read_only(self):
        card = (ROOT / "custom_components" / "atlantic_alfea_controller" / "www" / "pac-synoptique-card.js").read_text(encoding="utf-8")
        self.assertIn("class PacSynoptiqueCard extends HTMLElement", card)
        self.assertNotIn("hass.callService(", card)
        self.assertNotIn("hass.services.", card)
        self.assertIn("programmedRegime(c.program)", card)

if __name__ == "__main__":
    unittest.main()
