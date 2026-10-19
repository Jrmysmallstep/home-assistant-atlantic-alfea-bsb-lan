"""Test the actual V1.3.3-derived BSB native override send path in both seasons."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller/climate.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AlfeaCircuitClimate")
method = next(n for n in klass.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "_async_apply_pending_override")

class HAError(Exception):
    pass

class FakeLogger:
    def warning(self,*args): pass
    def error(self,*args): pass
    def exception(self,*args): raise AssertionError(args)

class Fake:
    def __init__(self, season, target, base=21.0, circuit=1):
        self.hass = self
        self._circuit = circuit
        self.season = season
        self._pending_target_temperature = target
        self._pending_base_temperature = base
        self._pending_override_task = None
        self.calls = []
    def _override_state(self): return (False,1,"...")
    def _mode(self): return self.season
    def _circuit_in_protection(self, mode): return False
    def _source(self,key,param): return "number.bsb."+str(param)
    def _preferred_override_duration(self): return 3.0
    def _override_option(self,code): return ("select.bsb.override",str(code)+" - "+("Plus chaud" if code==2 else "Plus froid"))
    def async_write_ha_state(self): pass

async def write_number(hass,source,value):
    hass.calls.append(("numeric",int(source.split(".")[-1]),value))
async def write_select(hass,source,option):
    hass.calls.append(("option",option[0]))
async def poll(hass,params):
    hass.calls.append(("poll",tuple(params)))
async def sleep(_): pass

PARAM={
    1: {"override_offset":("override_offset_c1",10991),"override_duration":("override_duration_c1",10990),
        "override":("override_c1",701),"effective_setpoint":8741},
    2: {"override_offset":("override_offset_c2",10993),"override_duration":("override_duration_c2",10992),
        "override":("override_c2",1001),"effective_setpoint":8771}
}
namespace=dict(
    asyncio=SimpleNamespace(sleep=sleep,CancelledError=asyncio.CancelledError),
    _OVERRIDE_DEBOUNCE_SECONDS=2,
    MODE_HEAT="heat",MODE_COOL="cool",
    _LOGGER=FakeLogger(),_PARAM=PARAM,
    async_set_numeric_entity=write_number,
    async_select_option=write_select,
    async_poll_parameters=poll
)
exec(compile(ast.Module(body=[method],type_ignores=[]),str(SOURCE),"exec"),namespace)
Fake._async_apply_pending_override=namespace["_async_apply_pending_override"]

class NativeOverrideTests(unittest.TestCase):
    def test_heating_warmer_circuit_1(self):
        f=Fake("heat",23.0)
        asyncio.run(f._async_apply_pending_override())
        self.assertIn(("numeric",10991,2.0),f.calls)
        self.assertIn(("option","2"),f.calls)
        self.assertIn(("numeric",10990,3.0),f.calls)
        self.assertIn(("poll",(10991,10990,701,8741)),f.calls)
    def test_heating_colder_circuit_2(self):
        f=Fake("heat",19.5,21.0,circuit=2)
        asyncio.run(f._async_apply_pending_override())
        self.assertIn(("numeric",10993,1.5),f.calls)
        self.assertIn(("option","0"),f.calls)
        self.assertIn(("poll",(10993,10992,1001,8771)),f.calls)
    def test_cooling_colder_unchanged(self):
        f=Fake("cool",19.0)
        asyncio.run(f._async_apply_pending_override())
        self.assertIn(("numeric",10991,2.0),f.calls)
        self.assertIn(("option","0"),f.calls)
    def test_out_of_range_never_writes(self):
        f=Fake("heat",28.0)
        asyncio.run(f._async_apply_pending_override())
        self.assertFalse(any(x[0] in ("numeric","option") for x in f.calls))

if __name__=="__main__": unittest.main()
