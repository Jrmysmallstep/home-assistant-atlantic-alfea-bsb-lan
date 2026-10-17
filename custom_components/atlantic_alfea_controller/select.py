"""Global PAC mode selector."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import BSB_AUTO, BSB_PROTECTION, DOMAIN, MODE_COOL, MODE_HEAT, MODE_OFF, SELECT_OPTIONS
from .helpers import async_select_option, derive_global_mode, is_enabled, is_protection, state_value, track_entities

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
        """Switch season without enabling circuits that are already protected.

        The global selector is not an independent season switch on this RVS.
        Only a circuit already enabled in the previous season is transferred.
        """
        if option not in _OPTION_TO_MODE:
            raise HomeAssistantError(f"Option de saison inconnue : {option}")

        data = self._entry.data
        readings = {
            key: state_value(self.hass, data[key])
            for key in ("heat_mode_c1", "cool_mode_c1", "heat_mode_c2", "cool_mode_c2")
        }
        if any(value is None for value in readings.values()):
            raise HomeAssistantError(
                "États des quatre circuits indisponibles : aucune commande envoyée."
            )
        heat_active = {n for n in (1, 2) if is_enabled(readings[f"heat_mode_c{n}"])}
        cool_active = {n for n in (1, 2) if is_enabled(readings[f"cool_mode_c{n}"])}
        if heat_active and cool_active:
            raise HomeAssistantError(
                "Chauffage et rafraîchissement simultanément actifs : "
                "commande bloquée, vérifier les circuits BSB-LAN."
            )
        target = _OPTION_TO_MODE[option]
        if target == MODE_OFF:
            for n in (1, 2):
                for prefix in ("heat", "cool"):
                    key = f"{prefix}_mode_c{n}"
                    if not is_protection(readings[key]):
                        await async_select_option(self.hass, data[key], BSB_PROTECTION)
            self.async_write_ha_state()
            return

        old_mode = MODE_HEAT if heat_active else MODE_COOL if cool_active else MODE_OFF
        if old_mode == MODE_OFF:
            raise HomeAssistantError(
                "Les deux circuits sont en Protection. Aucun paramètre natif de "
                "saison indépendante n'est identifié : aucune commutation envoyée. "
                "Activer explicitement un circuit dans la saison souhaitée."
            )
        if old_mode == target:
            return

        active_circuits = heat_active if old_mode == MODE_HEAT else cool_active
        old_prefix = "heat" if old_mode == MODE_HEAT else "cool"
        new_prefix = "heat" if target == MODE_HEAT else "cool"
        # First stop all previously active circuits. The RVS remains responsible
        # for the physical heating/cooling changeover delay (BSB 913).
        for n in (1, 2):
            old_key = f"{old_prefix}_mode_c{n}"
            if n in active_circuits:
                await async_select_option(self.hass, data[old_key], BSB_PROTECTION)
        # Only explicitly active circuits transfer to the new season.
        for n in sorted(active_circuits):
            await async_select_option(self.hass, data[f"{new_prefix}_mode_c{n}"], BSB_AUTO)
        self._last_known_mode = target
        self.async_write_ha_state()

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
