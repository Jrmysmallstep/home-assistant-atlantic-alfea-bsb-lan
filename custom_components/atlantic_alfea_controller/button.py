"""Control buttons for Atlantic Alfea BSB-LAN."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .clock import async_sync_pac_clock, clock_is_writable, clock_source_ids
from .const import DOMAIN
from .helpers import async_select_option, source_entity, track_entities
from .polling import async_poll_parameters


_OVERRIDE = {
    1: ("override_c1", 701, 8741),
    2: ("override_c2", 1001, 8771),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up clock and native-override control buttons."""
    entities: list[ButtonEntity] = []

    if all(clock_source_ids(hass, entry)):
        entities.append(AlfeaSyncClockButton(hass, entry))

    # Only expose a cancel button when BSB-LAN discovered the native override
    # parameter as a writable select entity. The validated bus command for
    # cancelling an override is value 1 on 701 (CC1) / 1001 (CC2).
    for circuit, (key, parameter, _effective_parameter) in _OVERRIDE.items():
        entity_id = source_entity(hass, entry, key, parameter)
        if entity_id and entity_id.startswith("select."):
            entities.append(AlfeaCancelOverrideButton(hass, entry, circuit))

    if entities:
        async_add_entities(entities)


class AlfeaSyncClockButton(ButtonEntity):
    """Synchronize the heat-pump clock with Home Assistant local time."""

    _attr_has_entity_name = True
    _attr_name = "Horloge PAC — Synchroniser"
    _attr_icon = "mdi:clock-sync-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._last_sync: datetime | None = None
        self._last_result: str | None = None
        self._attr_unique_id = f"{entry.entry_id}_sync_pac_clock"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def available(self) -> bool:
        """Return whether the clock parameter is writable."""
        return clock_is_writable(self.hass, self._entry)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Expose the last manual synchronization result."""
        attributes: dict[str, str] = {}
        if self._last_sync is not None:
            attributes["derniere_synchronisation"] = self._last_sync.isoformat()
        if self._last_result is not None:
            attributes["resultat"] = self._last_result
        return attributes or None

    async def async_press(self) -> None:
        """Write Home Assistant local date/time to BSB parameter 0."""
        try:
            self._last_sync = await async_sync_pac_clock(self.hass, self._entry)
        except HomeAssistantError:
            self._last_result = "échec"
            self.async_write_ha_state()
            raise
        except Exception as err:  # Defensive conversion to a user-visible HA error.
            self._last_result = "échec"
            self.async_write_ha_state()
            raise HomeAssistantError(
                f"La synchronisation de l’horloge PAC a échoué : {err}"
            ) from err

        self._last_result = "commande envoyée"
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Track source availability so the button state stays current."""
        self.async_on_remove(
            track_entities(
                self.hass,
                list(clock_source_ids(self.hass, self._entry)),
                self.async_write_ha_state,
            )
        )


class AlfeaCancelOverrideButton(ButtonEntity):
    """Cancel the native temporary override for one hydraulic circuit."""

    _attr_has_entity_name = True
    _attr_entity_category = None
    _attr_icon = "mdi:timer-remove-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, circuit: int) -> None:
        self.hass = hass
        self._entry = entry
        self._circuit = circuit
        self._attr_name = f"Circuit {circuit} — Annuler la dérogation"
        self._attr_unique_id = f"{entry.entry_id}_cancel_override_circuit_{circuit}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _source_id(self) -> str | None:
        key, parameter, _effective_parameter = _OVERRIDE[self._circuit]
        return source_entity(self.hass, self._entry, key, parameter)

    @property
    def available(self) -> bool:
        """Return whether the native override parameter is writable."""
        entity_id = self._source_id()
        if not entity_id or not entity_id.startswith("select."):
            return False
        state = self.hass.states.get(entity_id)
        return bool(
            state
            and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
        )

    def _normal_program_option(self) -> str:
        """Return the select option that corresponds to BSB value 1."""
        entity_id = self._source_id()
        if not entity_id:
            raise HomeAssistantError(
                f"Paramètre de dérogation du circuit {self._circuit} introuvable."
            )

        state = self.hass.states.get(entity_id)
        if state is None:
            raise HomeAssistantError(
                f"Entité BSB de dérogation du circuit {self._circuit} indisponible."
            )

        options = state.attributes.get("options") or []
        for option in options:
            text = str(option).strip()
            if text == "1" or text.startswith("1 -"):
                return str(option)

        raise HomeAssistantError(
            f"L’option BSB 1 permettant d’annuler la dérogation n’est pas "
            f"disponible sur {entity_id}. Options reçues : {options!r}."
        )

    async def async_press(self) -> None:
        """Return 701/1001 to value 1, restoring the PAC's normal program."""
        entity_id = self._source_id()
        if not entity_id or not entity_id.startswith("select."):
            raise HomeAssistantError(
                f"Le paramètre de dérogation du circuit {self._circuit} "
                "n’est pas disponible comme commande BSB-LAN modifiable."
            )

        option = self._normal_program_option()
        try:
            await async_select_option(self.hass, entity_id, option)
        except Exception as err:
            raise HomeAssistantError(
                f"Impossible d’annuler la dérogation du circuit {self._circuit} : {err}"
            ) from err

        # Ask BSB-LAN for an immediate confirmation of both the override state
        # and the resulting effective room setpoint.
        _key, parameter, effective_parameter = _OVERRIDE[self._circuit]
        await async_poll_parameters(self.hass, (parameter, effective_parameter))

    async def async_added_to_hass(self) -> None:
        """Track the BSB override source so availability stays current."""
        entity_id = self._source_id()
        if entity_id:
            self.async_on_remove(
                track_entities(self.hass, [entity_id], self.async_write_ha_state)
            )
