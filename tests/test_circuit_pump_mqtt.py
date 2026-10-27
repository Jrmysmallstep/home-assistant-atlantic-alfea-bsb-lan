"""Regression checks for read-only direct MQTT pump feedback."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/atlantic_alfea_controller"


class PumpMqttTests(unittest.TestCase):
    def test_direct_status_topics_and_dispatcher(self):
        setup = (ROOT / "__init__.py").read_text(encoding="utf-8")
        ast.parse(setup)
        self.assertIn('((1, 9031), (2, 8760))', setup)
        self.assertIn('BSB-LAN/+/+/{parameter}/status', setup)
        self.assertIn('async_dispatcher_send', setup)
        self.assertIn('entry.async_on_unload(_clear_mqtt_subscriptions)', setup)
        self.assertNotIn('async_publish', setup)

    def test_both_entities_get_live_feedback(self):
        helpers = (ROOT / "helpers.py").read_text(encoding="utf-8")
        climate = (ROOT / "climate.py").read_text(encoding="utf-8")
        binary = (ROOT / "binary_sensor.py").read_text(encoding="utf-8")
        for code in (helpers, climate, binary):
            ast.parse(code)
        self.assertIn('def circuit_pump_is_on(', helpers)
        self.assertIn('circuit_pump_is_on(self.hass, self._entry, self._circuit)', climate)
        self.assertIn('circuit_pump_is_on(self.hass, self._entry, self._circuit)', binary)
        self.assertIn('async_dispatcher_connect', climate)
        self.assertIn('async_dispatcher_connect', binary)


if __name__ == "__main__":
    unittest.main()
