"""Offline regression checks for pump-first heat/cool activity logic."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller"


class PumpClimateStateTests(unittest.TestCase):
    def test_missing_bsb_state_does_not_force_idle(self):
        climate = (ROOT / "climate.py").read_text(encoding="utf-8")
        ast.parse(climate)
        self.assertIn(
            "if circuit_state is not None and status_is_blocked_or_idle(circuit_state):",
            climate,
        )

    def test_pumps_are_separate_and_used_for_both_seasons(self):
        climate = (ROOT / "climate.py").read_text(encoding="utf-8")
        binary = (ROOT / "binary_sensor.py").read_text(encoding="utf-8")
        self.assertIn("9031 if self._circuit == 1 else 8760", climate)
        self.assertIn("return HVACAction.HEATING if mode == MODE_HEAT else HVACAction.COOLING", climate)
        self.assertIn("return HVACAction.IDLE", climate)
        self.assertIn("9031 if circuit == 1 else 8760", binary)

    def test_no_pac_write_added_to_pump_sensors(self):
        tree = ast.parse((ROOT / "binary_sensor.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == "AlfeaCircuitPumpBinarySensor")
        methods = {n.name for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertEqual(methods, {"__init__", "_source", "is_on", "extra_state_attributes", "async_added_to_hass"})


if __name__ == "__main__":
    unittest.main()
