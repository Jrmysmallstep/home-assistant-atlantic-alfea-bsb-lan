"""Offline tests for circuit modes extracted from the actual climate implementation."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/climate.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AlfeaCircuitClimate")
methods = [n for n in klass.body if isinstance(n, ast.AsyncFunctionDef) and n.name in ("async_set_hvac_mode", "_write_circuit_mode_verified")]

class HAError(Exception):
    pass

class HVAC:
    OFF, HEAT, COOL = "off", "heat", "cool"

def protected(value):
    return value.startswith("0 -")

def derive(heat1, cool1, heat2, cool2):
    heat = any(not protected(x) for x in (heat1, heat2))
    cool = any(not protected(x) for x in (cool1, cool2))
    return "heat" if heat and not cool else "cool" if cool and not heat else "off"

class Circuit:
    def __init__(self, active=False, season="heat", global_mode="Chauffage"):
        self._circuit = 1
        self.season = season
        self.global_mode = global_mode
        self._entry = SimpleNamespace(entry_id="test", data={
            "heat_mode_c1": "h1", "heat_mode_c2": "h2",
            "cool_mode_c1": "c1", "cool_mode_c2": "c2",
        })
        self.hass = self
        self.values = {"h1": "1 - Automatique" if active else "0 - Mode protection",
                       "h2":"0 - Mode protection","c1":"0 - Mode protection",
                       "c2":"0 - Mode protection", "select.global":"Chauffage" if global_mode == "Chauffage" else global_mode}
        self.writes = []
    def _mode(self): return self.season
    def async_write_ha_state(self): pass

async def write(hass, eid, option):
    hass.writes.append((eid, option))
    hass.values[eid] = option

namespace = {
    "HVACMode": HVAC, "HomeAssistantError": HAError,
    "MODE_HEAT": "heat", "MODE_COOL":"cool", "MODE_OFF":"off",
    "BSB_AUTO":"1 - Automatique", "BSB_PROTECTION":"0 - Mode protection",
    "DOMAIN":"atlantic_alfea_controller",
    "state_value":lambda hass,eid:hass.values.get(eid),
    "is_protection":protected, "derive_global_mode":derive,
    "async_select_option":write,
    "er":SimpleNamespace(async_get=lambda hass:SimpleNamespace(
        async_get_entity_id=lambda *args:"select.global")),
}
exec(compile(ast.Module(body=methods, type_ignores=[]), str(SOURCE), "exec"), namespace)
Circuit.async_set_hvac_mode = namespace["async_set_hvac_mode"]
Circuit._write_circuit_mode_verified = namespace["_write_circuit_mode_verified"]
namespace["asyncio"] = asyncio

class Tests(unittest.TestCase):
    def test_reenable_when_both_protected_and_ha_heating(self):
        circuit=Circuit()
        asyncio.run(circuit.async_set_hvac_mode(HVAC.HEAT))
        self.assertEqual(circuit.writes, [("h1","1 - Automatique")])
    def test_block_cooling_in_heating(self):
        circuit=Circuit()
        with self.assertRaises(HAError):
            asyncio.run(circuit.async_set_hvac_mode(HVAC.COOL))
        self.assertEqual(circuit.writes, [])
    def test_block_if_global_missing(self):
        circuit=Circuit()
        circuit.values["select.global"]="Off"
        with self.assertRaises(HAError):
            asyncio.run(circuit.async_set_hvac_mode(HVAC.HEAT))
        self.assertEqual(circuit.writes, [])
    def test_off_only_this_circuit(self):
        circuit=Circuit(active=True)
        asyncio.run(circuit.async_set_hvac_mode(HVAC.OFF))
        self.assertEqual(circuit.writes,[("h1","0 - Mode protection")])
    def test_reenable_stage_when_rdc_active(self):
        circuit=Circuit(active=True)
        circuit._circuit=2
        asyncio.run(circuit.async_set_hvac_mode(HVAC.HEAT))
        self.assertEqual(circuit.writes,[("h2","1 - Automatique")])

if __name__ == "__main__":
    unittest.main()
