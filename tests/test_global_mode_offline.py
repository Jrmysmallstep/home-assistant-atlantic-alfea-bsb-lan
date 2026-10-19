"""Offline tests of actual select.py methods; no Home Assistant connection needed.

Run from repository root: python -m unittest discover -s tests -v
"""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/select.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
SELECTOR = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "AlfeaGlobalModeSelect")
METHODS = [n for n in SELECTOR.body if isinstance(n, ast.AsyncFunctionDef) and n.name in ("_write_verified", "async_select_option")]
CODE = compile(ast.Module(body=METHODS, type_ignores=[]), str(SOURCE), "exec")

class HomeAssistantError(Exception):
    pass

MODE_OFF, MODE_HEAT, MODE_COOL = "off", "heat", "cool"
BSB_PROTECTION = "0 - Mode protection"
OPTIONS = {"Off": MODE_OFF, "Chauffage": MODE_HEAT, "Refroidissement": MODE_COOL}

def is_protection(value):
    return value is not None and (value.startswith("0 -") or "protection" in value.lower())

def is_enabled(value):
    return value is not None and not is_protection(value)

async def fast_sleep(_seconds):
    return None

class Fake:
    def __init__(self, states, fail_at=None, confirm=True):
        self.values = states.copy()
        self.hass = self
        self._entry = SimpleNamespace(data={k:k for k in states})
        self._command_lock = asyncio.Lock()
        self._last_known_mode = MODE_HEAT
        self.writes = []
        self.fail_at = fail_at
        self.confirm = confirm
    def async_write_ha_state(self):
        pass

def states(h1=False, h2=False, c1=False, c2=False):
    return {f"{p}_mode_c{n}": "1 - Automatique" if enabled else BSB_PROTECTION
            for p, n, enabled in (("heat",1,h1),("heat",2,h2),("cool",1,c1),("cool",2,c2))}

class Tests(unittest.TestCase):
    def setUp(self):
        async def write(hass, key, option):
            if hass.fail_at == len(hass.writes):
                raise HomeAssistantError("Write failed")
            hass.writes.append((key, option))
            if hass.confirm:
                hass.values[key] = option

        namespace = {
            "asyncio": SimpleNamespace(Lock=asyncio.Lock, sleep=fast_sleep),
            "HomeAssistantError": HomeAssistantError,
            "_OPTION_TO_MODE": OPTIONS,
            "MODE_OFF": MODE_OFF, "MODE_HEAT": MODE_HEAT, "MODE_COOL": MODE_COOL,
            "BSB_PROTECTION": BSB_PROTECTION,
            "BSB_AUTO": "1 - Automatique",
            "is_protection": is_protection, "is_enabled": is_enabled,
            "state_value": lambda hass, key: hass.values.get(key),
            "async_select_option": write,
        }
        exec(CODE, namespace)
        Fake._write_verified = namespace["_write_verified"]
        Fake.async_select_option = namespace["async_select_option"]
        namespace["async_select_option"] = write  # Keep the service mock separate from the entity method

    def execute(self, initial, option, expected, fails=False, **kwargs):
        inst = Fake(initial, **kwargs)
        if fails:
            with self.assertRaises(HomeAssistantError):
                asyncio.run(inst.async_select_option(option))
        else:
            asyncio.run(inst.async_select_option(option))
        self.assertEqual(inst.writes, expected)
        return inst

    def test_off_stops_only_active_circuit(self):
        self.execute(states(h1=True), "Off", [("heat_mode_c1", BSB_PROTECTION)])

    def test_off_stops_both(self):
        self.execute(states(h1=True,h2=True), "Off", [
            ("heat_mode_c1", BSB_PROTECTION), ("heat_mode_c2", BSB_PROTECTION)])

    def test_same_season_noop(self):
        self.execute(states(h1=True), "Chauffage", [("heat_mode_c2", "1 - Automatique")])

    def test_both_protected_no_activation(self):
        self.execute(states(), "Refroidissement", [("cool_mode_c1", "1 - Automatique"), ("cool_mode_c2", "1 - Automatique")])

    def test_opposite_season_blocked_before_writes(self):
        self.execute(states(h1=True), "Refroidissement", [("heat_mode_c1", BSB_PROTECTION), ("cool_mode_c1", "1 - Automatique"), ("cool_mode_c2", "1 - Automatique")])
        self.execute(states(c1=True), "Chauffage", [("cool_mode_c1", BSB_PROTECTION), ("heat_mode_c1", "1 - Automatique"), ("heat_mode_c2", "1 - Automatique")])

    def test_conflict_blocked(self):
        self.execute(states(h1=True,c2=True), "Off", [], fails=True)

    def test_unavailable_blocked(self):
        values = states(h1=True)
        values["cool_mode_c2"] = None
        self.execute(values, "Off", [], fails=True)

    def test_first_write_fails(self):
        self.execute(states(h1=True), "Off", [], fails=True, fail_at=0)

    def test_second_write_fails_and_stops(self):
        self.execute(states(h1=True,h2=True), "Off",
                     [("heat_mode_c1", BSB_PROTECTION)], fails=True, fail_at=1)

    def test_unconfirmed_write_timeout_stops(self):
        self.execute(states(h1=True,h2=True), "Off",
                     [("heat_mode_c1", BSB_PROTECTION)], fails=True, confirm=False)

if __name__ == "__main__":
    unittest.main()
