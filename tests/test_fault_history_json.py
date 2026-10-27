"""Read-only BSB fault history decoding tests."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/fault_history_json.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
parser = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "parse_fault_history")
scope = {}
exec(compile(ast.Module(body=[parser], type_ignores=[]), str(SOURCE), "exec"), scope)
parse = scope["parse_fault_history"]


def empty_history():
    data = {}
    for i in range(10):
        data[str(6800 + 2*i)] = {"error": 0, "dataType_name": "DATETIME", "value": "---", "desc": ""}
        data[str(6801 + 2*i)] = {"error": 0, "dataType_name": "ENUM", "value": "65535", "desc": "---"}
    return data


class TestFaultHistory(unittest.TestCase):
    def test_empty_real_pac_values(self):
        self.assertEqual(parse(empty_history()), [])

    def test_date_code_pair(self):
        data = empty_history()
        data["6800"]["value"] = "27.10.2026 19:00"
        data["6801"].update(value="123", desc="Défaut exemple")
        result = parse(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "27.10.2026 19:00")
        self.assertEqual(result[0]["code"], "123")

    def test_partial_failure_not_empty(self):
        data = empty_history()
        data["6803"]["error"] = 1
        with self.assertRaises(ValueError):
            parse(data)

    def test_inconsistent_slot_not_empty(self):
        data = empty_history()
        data["6800"]["value"] = "27.10.2026 19:00"
        with self.assertRaises(ValueError):
            parse(data)

    def test_no_pac_write(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("/JS", source)
        self.assertNotIn("session.post(", source)


if __name__ == "__main__":
    unittest.main()
