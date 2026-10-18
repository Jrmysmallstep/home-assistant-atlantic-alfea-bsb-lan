"""Exercise actual select.py global-mode methods without Home Assistant runtime."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/select.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AlfeaGlobalModeSelect")
methods = [node for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in
           ("current_option", "_observed_mode", "_write_verified", "async_select_option")]
class HAError(Exception): pass
def is_protection(x): return x is not None and x.startswith("0")
def is_enabled(x): return x is not None and not is_protection(x)
def derive(h1,c1,h2,c2):
    if is_enabled(h1) or is_enabled(h2): return "heat"
    if is_enabled(c1) or is_enabled(c2): return "cool"
    return "off"
async def write(hass,entity_id,option):
    hass.writes.append((entity_id,option))
    hass.values[entity_id]=option
namespace = dict(
    HomeAssistantError=HAError, MODE_HEAT="heat", MODE_COOL="cool", MODE_OFF="off",
    BSB_PROTECTION="0 - Mode protection",
    _OPTION_TO_MODE={"Off":"off","Chauffage":"heat","Refroidissement":"cool"},
    _MODE_TO_OPTION={"off":"Off","heat":"Chauffage","cool":"Refroidissement"},
    is_protection=is_protection,is_enabled=is_enabled,derive_global_mode=derive,
    state_value=lambda hass,eid:hass.values[eid],
    async_select_option=write,asyncio=asyncio
)
exec(compile(ast.Module(body=methods,type_ignores=[]),str(SOURCE),"exec"),namespace)
class Fake:
    current_option=property(namespace["current_option"].fget if isinstance(namespace["current_option"],property) else namespace["current_option"])
    _observed_mode=namespace["_observed_mode"]
    _write_verified=namespace["_write_verified"]
    async_select_option=namespace["async_select_option"]
    def __init__(self,active=False):
        self.values=dict(h1="1 - Automatique" if active else "0 - Mode protection",
                         h2="0 - Mode protection", c1="0 - Mode protection",c2="0 - Mode protection")
        self.hass=self
        self._entry=SimpleNamespace(data=dict(heat_mode_c1="h1",heat_mode_c2="h2",cool_mode_c1="c1",cool_mode_c2="c2"))
        self._last_known_mode="heat"
        self._selected_mode="heat"
        self._command_lock=asyncio.Lock()
        self.writes=[]
    def async_write_ha_state(self):pass

class Tests(unittest.TestCase):
    def test_both_off_keeps_heating(self):
        f=Fake()
        self.assertEqual(f.current_option,"Chauffage")
    def test_explicit_global_off_stays_off(self):
        f=Fake(active=True)
        asyncio.run(f.async_select_option("Off"))
        self.assertEqual(f.current_option,"Off")
    def test_reselect_same_season_without_writes(self):
        f=Fake()
        f._selected_mode="off"
        asyncio.run(f.async_select_option("Chauffage"))
        self.assertEqual(f.current_option,"Chauffage")
        self.assertEqual(f.writes,[])
    def test_refuse_unconfirmed_switch(self):
        f=Fake()
        with self.assertRaises(HAError):
            asyncio.run(f.async_select_option("Refroidissement"))
        self.assertEqual(f.writes,[])

if __name__=="__main__":unittest.main()
