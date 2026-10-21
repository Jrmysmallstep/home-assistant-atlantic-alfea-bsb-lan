"""Offline structural regression checks for hydraulic circuit activity."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller"
CLIMATE = ast.parse((ROOT / "climate.py").read_text(encoding="utf-8"))
BINARY = ast.parse((ROOT / "binary_sensor.py").read_text(encoding="utf-8"))


class Tests(unittest.TestCase):
    def test_each_circuit_has_its_pump_parameter(self):
        pump = next(node for node in BINARY.body if isinstance(node, ast.ClassDef)
                    and node.name == "AlfeaCircuitPumpBinarySensor")
        constructor = next(node for node in pump.body if isinstance(node, ast.FunctionDef)
                           and node.name == "__init__")
        code = ast.unparse(constructor)
        self.assertIn("9031 if circuit == 1 else 8760", code)
        self.assertIn("circuit_pump_c", code)
        self.assertNotIn("async_set", ast.unparse(pump))

    def test_climate_checks_pump_before_compressor(self):
        climate = next(node for node in CLIMATE.body if isinstance(node, ast.ClassDef)
                       and node.name == "AlfeaCircuitClimate")
        action = next(node for node in climate.body if isinstance(node, ast.FunctionDef)
                      and node.name == "hvac_action")
        code = ast.unparse(action)
        self.assertIn("pump_on is True", code)
        self.assertIn("pump_on is False", code)
        self.assertIn("dhw_pump is True", code)
        self.assertNotIn("compressor_on", code)
        self.assertNotIn("current_temperature", code)
        tracked = next(node for node in climate.body if isinstance(node, ast.AsyncFunctionDef)
                       and node.name == "async_added_to_hass")
        self.assertIn("circuit_pump_c", ast.unparse(tracked))

if __name__ == "__main__":
    unittest.main()
