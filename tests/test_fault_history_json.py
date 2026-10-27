"""Read-only fault history parser contract tests."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/fault_history_json.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
empty = next(n for n in TREE.body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=="_EMPTY" for t in n.targets))
parser = next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=="parse_fault_history")
scope={}
exec(compile(ast.Module(body=[empty,parser],type_ignores=[]),str(SOURCE),"exec"),scope)


class TestFaultHistory(unittest.TestCase):
    def test_empty_history(self):
        data={str(i):{"error":0,"value":"","desc":""} for i in range(6800,6820)}
        self.assertEqual(scope["parse_fault_history"](data),[])

    def test_raw_nonempty_record_preserved(self):
        data={str(i):{"error":0,"value":"","desc":""} for i in range(6800,6820)}
        data["6800"]["value"]="2026-10-27"
        data["6801"]["value"]="123"
        result=scope["parse_fault_history"](data)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["premier"],"2026-10-27")
        self.assertEqual(result[0]["second"],"123")

    def test_partial_failure_is_not_empty(self):
        data={str(i):{"error":0,"value":"","desc":""} for i in range(6800,6820)}
        data["6804"]["error"]=1
        with self.assertRaises(ValueError):
            scope["parse_fault_history"](data)

    def test_no_pac_write(self):
        source=SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("/JS",source)
        self.assertNotIn("session.post(",source)


if __name__=="__main__":
    unittest.main()
