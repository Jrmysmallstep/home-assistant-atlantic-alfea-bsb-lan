"""Offline tests of actual native programmed setpoint write method."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/number.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AlfeaProgrammedSetpointNumber")
method = next(n for n in klass.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_set_native_value")

class HAError(Exception):
    pass

class Fake:
    def __init__(self, season, initial=20.0, confirm=True):
        self.hass = self
        self._parameter = 710 if season == "Chauffage" else 902
        self.native_min_value = 7.0
        self.native_max_value = 35.0 if season == "Chauffage" else 30.0
        self.current = initial
        self.confirm = confirm
        self.calls = []
    def _source(self): return "number.bsb"
    def async_write_ha_state(self): self.calls.append(("state",))

async def write(hass, source, value):
    hass.calls.append(("write", value))
    if hass.confirm: hass.current = value

async def poll(hass, parameters):
    hass.calls.append(("poll", parameters))

async def no_wait(value):
    pass

namespace = {
    "HomeAssistantError": HAError,
    "async_set_numeric_entity": write,
    "async_poll_parameters": poll,
    "state_float":lambda hass, source: hass.current,
    "asyncio":SimpleNamespace(sleep=no_wait),
}
exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), "exec"), namespace)
Fake.async_set_native_value = namespace["async_set_native_value"]

class TestSetpoints(unittest.TestCase):
    def test_heat_bounds(self):
        for value in (7.0, 35.0):
            f=Fake("Chauffage")
            asyncio.run(f.async_set_native_value(value))
            self.assertIn(("poll",(710,)),f.calls)
            self.assertIn(("write",value),f.calls)
    def test_cooling_bounds(self):
        f=Fake("Rafraîchissement")
        asyncio.run(f.async_set_native_value(30.0))
        self.assertIn(("write",30.0),f.calls)
    def test_reject_out_of_range_and_step(self):
        for season,value in (("Chauffage",6.5),("Chauffage",35.5),("Rafraîchissement",30.5),("Rafraîchissement",21.3)):
            f=Fake(season)
            with self.assertRaises(HAError):
                asyncio.run(f.async_set_native_value(value))
            self.assertEqual(f.calls,[])
    def test_unconfirmed_write_reports_error(self):
        f=Fake("Chauffage",initial=20.0,confirm=False)
        with self.assertRaisesRegex(HAError,"non confirmée"):
            asyncio.run(f.async_set_native_value(21.0))
        self.assertIn(("poll",(710,)),f.calls)
        self.assertNotIn(("state",),f.calls)

if __name__ == "__main__":
    unittest.main()
