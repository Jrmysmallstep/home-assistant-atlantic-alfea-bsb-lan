"""Guard against missing production constants hidden by offline mocks."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/select.py"

class GlobalImportsTest(unittest.TestCase):
    def test_bsb_auto_imported_from_const(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        imports = {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "const" and node.level == 1
            for alias in node.names
        }
        self.assertIn("BSB_AUTO", imports)

if __name__ == "__main__":
    unittest.main()
