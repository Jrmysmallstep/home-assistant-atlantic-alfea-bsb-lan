"""Global PAC mode selector."""

from __future__ import annotations

import asyncio

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import BSB_PROTECTION, DOMAIN, MODE_COOL, MODE_HEAT, MODE_OFF, SELECT_OPTIONS
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
        self._selected_mode: str | None = None
        self._command_lock = asyncio.Lock()
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
        if mode in (MODE_HEAT, MODE_COOL):
            self._selected_mode = mode
        return _MODE_TO_OPTION[mode if mode != MODE_OFF else self._selected_mode or self._last_known_mode or MODE_OFF]

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        if self._observed_mode() != MODE_OFF:
            return {"source_saison": "BSB-LAN"}
        if self._selected_mode == MODE_OFF:
            return {"source_saison": "arrêt global demandé dans Home Assistant"}
        return {"source_saison": "choix HA / dernier mode connu (non confirmé)" if (self._selected_mode or self._last_known_mode) else "inconnu"}

    def _observed_mode(self) -> str:
        data = self._entry.data
        return derive_global_mode(
            state_value(self.hass, data["heat_mode_c1"]),
            state_value(self.hass, data["cool_mode_c1"]),
            state_value(self.hass, data["heat_mode_c2"]),
            state_value(self.hass, data["cool_mode_c2"]),
        )

    async def _write_verified(self, entity_id: str, option: str) -> None:
        """Write one mode and wait for source state feedback before continuing."""
        await async_select_option(self.hass, entity_id, option)
        expected_protection = option == BSB_PROTECTION
        for _ in range(20):
            value = state_value(self.hass, entity_id)
            if value is not None and is_protection(value) == expected_protection:
                return
            await asyncio.sleep(0.5)
        raise HomeAssistantError(
            f"BSB-LAN n'a pas confirmé {option} sur {entity_id} dans les 10 secondes. "
            "Commande interrompue, vérifier les états réels des circuits."
        )

    async def async_select_option(self, option: str) -> None:
        """Apply only verified changes; never enable the other season automatically.

        Changing season requires a controller-level interlock which has not yet
        been identified. Stopping active circuits is supported; enabling the
        opposite season in the same request is intentionally blocked.
        """
        if option not in _OPTION_TO_MODE:
            raise HomeAssistantError(f"Option de saison inconnue : {option}")
        if self._command_lock.locked():
            raise HomeAssistantError("Une commande de mode global est déjà en cours.")

        async with self._command_lock:
            data = self._entry.data
            keys = ("heat_mode_c1", "cool_mode_c1", "heat_mode_c2", "cool_mode_c2")
            readings = {key: state_value(self.hass, data[key]) for key in keys}
            if any(value is None for value in readings.values()):
                raise HomeAssistantError("État d'un circuit indisponible : aucune commande envoyée.")

            heat_active = {n for n in (1, 2) if is_enabled(readings[f"heat_mode_c{n}"])}
            cool_active = {n for n in (1, 2) if is_enabled(readings[f"cool_mode_c{n}"])}
            if heat_active and cool_active:
                raise HomeAssistantError(
                    "Chauffage et rafraîchissement simultanément actifs : commande bloquée."
                )

            target = _OPTION_TO_MODE[option]
            current = MODE_HEAT if heat_active else MODE_COOL if cool_active else MODE_OFF
            if target == current and target != MODE_OFF:
                self._selected_mode = target
                self.async_write_ha_state()
                return

            if target != MODE_OFF:
                if current == MODE_OFF and (
                    target == self._last_known_mode or target == getattr(self, "_selected_mode", None)
                ):
                    # Explicitly reselect the remembered season without starting
                    # either circuit. Each climate controls its own activation.
                    self._selected_mode = target
                    self.async_write_ha_state()
                    return
                raise HomeAssistantError(
                    "Changement de saison non confirmé : activation bloquée. "
                    "Aucun circuit activé."
                )

            # Off acts on circuit modes only. Season memory is retained.
            # Stop one circuit at a time and confirm actual source feedback.
            for n in (1, 2):
                for prefix in ("heat", "cool"):
                    key = f"{prefix}_mode_c{n}"
                    if not is_protection(readings[key]):
                        await self._write_verified(data[key], BSB_PROTECTION)
            self._selected_mode = MODE_OFF
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        previous = await self.async_get_last_state()
        if previous is not None:
            restored = _OPTION_TO_MODE.get(previous.state)
            if restored in (MODE_HEAT, MODE_COOL):
                self._last_known_mode = restored
            if restored in (MODE_HEAT, MODE_COOL, MODE_OFF):
                self._selected_mode = restored
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
