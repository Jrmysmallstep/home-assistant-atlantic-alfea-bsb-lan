"""Global PAC mode selector."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, MODE_COOL, MODE_HEAT, MODE_OFF, SELECT_OPTIONS
from .helpers import derive_global_mode, state_value, track_entities

_OPTION_TO_MODE = {"Off": MODE_OFF, "Chauffage": MODE_HEAT, "Refroidissement": MODE_COOL}
_MODE_TO_OPTION = {value: key for key, value in _OPTION_TO_MODE.items()}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([AlfeaGlobalModeSelect(hass, entry)])


class AlfeaGlobalModeSelect(SelectEntity, RestoreEntity):
    """Select the mutually exclusive global PAC mode."""

    _attr_has_entity_name = True
    _attr_name = "Mode global"
    _attr_options = SELECT_OPTIONS
    _attr_icon = "mdi:heat-pump"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._last_known_mode: str | None = None
        self._attr_unique_id = f"{entry.entry_id}_global_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Atlantic Alfea BSB-LAN",
            manufacturer="Atlantic",
            model="Alfea via BSB-LAN",
        )

    @property
    def current_option(self) -> str:
        data = self._entry.data
        mode = derive_global_mode(
            state_value(self.hass, data["heat_mode_c1"]),
            state_value(self.hass, data["cool_mode_c1"]),
            state_value(self.hass, data["heat_mode_c2"]),
            state_value(self.hass, data["cool_mode_c2"]),
        )
        if mode in (MODE_HEAT, MODE_COOL):
            self._last_known_mode = mode
        return _MODE_TO_OPTION[mode if mode != MODE_OFF else self._last_known_mode or MODE_OFF]

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        if self._observed_mode() != MODE_OFF:
            return {"source_saison": "BSB-LAN"}
        return {"source_saison": "dernier mode connu (non confirmé)" if self._last_known_mode else "inconnu"}

    def _observed_mode(self) -> str:
        data = self._entry.data
        return derive_global_mode(
            state_value(self.hass, data["heat_mode_c1"]),
            state_value(self.hass, data["cool_mode_c1"]),
            state_value(self.hass, data["heat_mode_c2"]),
            state_value(self.hass, data["cool_mode_c2"]),
        )

    async def async_select_option(self, option: str) -> None:
        from homeassistant.exceptions import HomeAssistantError
        raise HomeAssistantError(
            "Commande saisonnière désactivée dans cette bêta : utiliser la régulation "
            "ou Cozytouch. Pour arrêter un circuit, choisir Protection individuellement."
        )

    async def async_added_to_hass(self) -> None:
        previous = await self.async_get_last_state()
        if previous is not None:
            restored = _OPTION_TO_MODE.get(previous.state)
            if restored in (MODE_HEAT, MODE_COOL):
                self._last_known_mode = restored
        self.async_on_remove(
            track_entities(
                self.hass,
                [
                    self._entry.data["heat_mode_c1"],
                    self._entry.data["cool_mode_c1"],
                    self._entry.data["heat_mode_c2"],
                    self._entry.data["cool_mode_c2"],
                ],
                self.async_write_ha_state,
            )
        )
