"""Configuration numbers for Atlantic Alfea BSB-LAN."""

from __future__ import annotations

from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .helpers import source_entity, state_float

_DURATION_PARAM = {1: ("override_duration_c1", 10990), 2: ("override_duration_c2", 10992)}
_DEFAULT_DURATION_HOURS = 2.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up local native-override duration selectors."""
    async_add_entities(
        [
            AlfeaOverrideDurationNumber(hass, entry, 1),
            AlfeaOverrideDurationNumber(hass, entry, 2),
        ]
    )


class AlfeaOverrideDurationNumber(RestoreNumber):
    """Preferred duration to write when a native PAC override is created.

    Changing this entity only changes the Home Assistant preference. The BSB
    duration parameter is written together with the offset immediately before
    the native override is activated from the Climate entity.
    """

    _attr_has_entity_name = True
    _attr_entity_category = None
    _attr_native_min_value = 1.0
    _attr_native_max_value = 24.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_should_poll = False
    _attr_icon = "mdi:timer-cog-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, circuit: int) -> None:
        self.hass = hass
        self._entry = entry
        self._circuit = circuit
        self._attr_name = f"Circuit {circuit} — Durée dérogation"
        self._attr_unique_id = f"{entry.entry_id}_override_duration_c{circuit}"
        self._attr_native_value = _DEFAULT_DURATION_HOURS
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Atlantic Alfea BSB-LAN",
            manufacturer="Atlantic",
            model="Alfea via BSB-LAN",
        )

    async def async_added_to_hass(self) -> None:
        """Restore the HA preference, otherwise initialize from the PAC."""
        await super().async_added_to_hass()

        last_data = await self.async_get_last_number_data()
        if last_data is not None and last_data.native_value is not None:
            self._attr_native_value = self._clamp(float(last_data.native_value))
            return

        key, parameter = _DURATION_PARAM[self._circuit]
        current = state_float(
            self.hass,
            source_entity(self.hass, self._entry, key, parameter),
        )
        if current is not None:
            self._attr_native_value = self._clamp(current)

    async def async_set_native_value(self, value: float) -> None:
        """Store the preferred duration locally until the next override."""
        self._attr_native_value = self._clamp(value)
        self.async_write_ha_state()

    def _clamp(self, value: float) -> float:
        return float(max(self.native_min_value, min(self.native_max_value, round(value))))
