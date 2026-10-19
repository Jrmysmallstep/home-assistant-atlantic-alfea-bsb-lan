"""Offline checks for four read-only native BSB circuit-program diagnostics."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/sensor.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
ITEMS = next(node for node in TREE.body if isinstance(node, ast.Assign)
             if any(isinstance(t, ast.Name) and t.id == "_CIRCUIT_PROGRAM_DIAGNOSTICS" for t in node.targets))
CLASS = next(node for node in TREE.body if isinstance(node, ast.ClassDef)
             and node.name == "AlfeaCircuitProgramDiagnosticSensor")

class Tests(unittest.TestCase):
    def test_exact_parameters_and_labels(self):
        self.assertEqual(ast.literal_eval(ITEMS.value), (
            (1, "Régime temporaire", 10110),
            (2, "Régime temporaire", 10120),
            (1, "Programme actif", 10112),
            (2, "Programme actif", 10122),
        ))

    def test_entity_is_read_only(self):
        method_names = {n.name for n in CLASS.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertIn("native_value", method_names)
        self.assertIn("async_added_to_hass", method_names)
        self.assertFalse(any(n.startswith("async_set") or n.startswith("async_press") for n in method_names))

    def test_setup_adds_four_diagnostics(self):
        setup = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_setup_entry")
        self.assertIn("AlfeaCircuitProgramDiagnosticSensor", ast.unparse(setup))

if __name__ == "__main__":
    unittest.main()
