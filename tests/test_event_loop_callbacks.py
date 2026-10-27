"""Regression checks for Home Assistant event-loop callback registration.

Source-level tests run without Home Assistant installed.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "atlantic_alfea_controller"


def _source_tree(filename: str) -> ast.Module:
    return ast.parse((ROOT / filename).read_text(encoding="utf-8"))


def _named_functions(tree: ast.AST, name: str) -> list[ast.FunctionDef]:
    return [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]


def _is_ha_callback(node: ast.FunctionDef) -> bool:
    return any(
        isinstance(decorator, ast.Name) and decorator.id == "callback"
        for decorator in node.decorator_list
    )


class EventLoopCallbackTests(unittest.TestCase):
    def test_mqtt_feedback_dispatches_from_event_loop(self) -> None:
        handlers = _named_functions(_source_tree("__init__.py"), "_notify_on_loop")
        self.assertEqual(len(handlers), 2, "Expected pump and Q3 feedback handlers")
        self.assertTrue(all(_is_ha_callback(handler) for handler in handlers))

    def test_mqtt_component_loaded_listener_runs_on_event_loop(self) -> None:
        handlers = _named_functions(_source_tree("__init__.py"), "_mqtt_component_loaded")
        self.assertEqual(len(handlers), 1)
        self.assertTrue(_is_ha_callback(handlers[0]))

    def test_regime_interval_uses_decorated_callback(self) -> None:
        tree = _source_tree("climate.py")
        handlers = _named_functions(tree, "_schedule_regime_refresh")
        self.assertEqual(len(handlers), 1)
        self.assertTrue(_is_ha_callback(handlers[0]))

        interval_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "async_track_time_interval"
        ]
        self.assertEqual(len(interval_calls), 1)
        callback_arg = interval_calls[0].args[1]
        self.assertIsInstance(callback_arg, ast.Attribute)
        self.assertEqual(callback_arg.attr, "_schedule_regime_refresh")


if __name__ == "__main__":
    unittest.main()
