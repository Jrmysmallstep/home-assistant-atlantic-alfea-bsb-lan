"""Regression checks for Home Assistant event-loop callback registration.

These tests parse the integration source without requiring Home Assistant to be
installed in the unit-test environment.
"""
from __future__ import annotations

import ast
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
    return any(isinstance(decorator, ast.Name) and decorator.id == "callback"
               for decorator in node.decorator_list)


def test_mqtt_feedback_dispatches_from_event_loop() -> None:
    tree = _source_tree("__init__.py")
    handlers = _named_functions(tree, "_notify_on_loop")
    assert len(handlers) == 2, "Expected pump and Q3 feedback handlers"
    assert all(_is_ha_callback(handler) for handler in handlers)


def test_mqtt_component_loaded_listener_runs_on_event_loop() -> None:
    tree = _source_tree("__init__.py")
    handlers = _named_functions(tree, "_mqtt_component_loaded")
    assert len(handlers) == 1
    assert _is_ha_callback(handlers[0])


def test_regime_interval_uses_decorated_callback() -> None:
    tree = _source_tree("climate.py")
    handlers = _named_functions(tree, "_schedule_regime_refresh")
    assert len(handlers) == 1
    assert _is_ha_callback(handlers[0])

    interval_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "async_track_time_interval"
    ]
    assert len(interval_calls) == 1
    callback_arg = interval_calls[0].args[1]
    assert isinstance(callback_arg, ast.Attribute)
    assert callback_arg.attr == "_schedule_regime_refresh"
