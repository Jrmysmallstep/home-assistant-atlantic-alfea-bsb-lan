"""Read-only native cooling weekly schedule mapping tests (no HA runtime needed)."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import unittest

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "atlantic_alfea_controller"
    / "weekly_programs.py"
)
TEXT = SOURCE.read_text(encoding="utf-8")
TREE = ast.parse(TEXT)


def load_literal(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} absent")


def load_function(name, extra=None):
    node = next(
        n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == name
    )
    scope = dict(extra or {})
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), scope)
    return scope[name]


PROGRAMS = load_literal("PROGRAMS")
WEEKDAYS = load_literal("WEEKDAYS")
parameter_for_day = load_function("parameter_for_day", {"WEEKDAYS": WEEKDAYS})
parse_timeprog = load_function(
    "parse_timeprog",
    {"_SLOT_RE": re.compile(r"(\d{2}:\d{2}|##:##)-(\d{2}:\d{2}|##:##)")},
)


class TestCoolingWeeklyPrograms(unittest.TestCase):
    def test_cooling_has_fourteen_consecutive_parameters(self):
        for key, first in (
            ("rafraichissement_c1", 11000),
            ("rafraichissement_c2", 11010),
        ):
            self.assertEqual(PROGRAMS[key][2], str(first))
            self.assertEqual(
                [parameter_for_day(key, str(first), day) for day in range(7)],
                [str(first + day) for day in range(7)],
            )

    def test_heating_and_dhw_keep_dotted_parameters(self):
        for key, first in (
            ("chauffage_c1", "501"),
            ("chauffage_c2", "521"),
            ("ecs", "561"),
        ):
            self.assertEqual(
                [parameter_for_day(key, first, day) for day in range(7)],
                [first] + [f"{first}.{day}" for day in range(1, 7)],
            )

    def test_reject_invalid_day(self):
        for day in (-1, 7):
            with self.assertRaises(ValueError):
                parameter_for_day("rafraichissement_c1", "11000", day)

    def test_real_cooling_values_and_inactive_slots(self):
        self.assertEqual(
            parse_timeprog("10:30-20:30 ##:##-##:## ##:##-##:##"),
            [{"debut": "10:30", "fin": "20:30"}],
        )
        self.assertEqual(
            parse_timeprog("11:30-21:30 ##:##-##:## ##:##-##:##"),
            [{"debut": "11:30", "fin": "21:30"}],
        )

    def test_no_write_calls_in_importer(self):
        self.assertIn("/JQ=", TEXT)
        self.assertNotIn("/JS=", TEXT)
        self.assertNotIn("session.post(", TEXT)


if __name__ == "__main__":
    unittest.main()
