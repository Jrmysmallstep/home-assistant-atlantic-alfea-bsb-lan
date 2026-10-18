"""Configuration numbers for Atlantic Alfea BSB-LAN."""

from __future__ import annotations

import asyncio

from homeassistant.components.number import NumberEntity, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .helpers import async_set_numeric_entity, source_entity, state_float, track_entities
from .polling import async_poll_parameters

_DURATION_PARAM = {1: ("override_duration_c1", 10990), 2: ("override_duration_c2", 10992)}
_DEFAULT_DURATION_HOURS = 2.0

_PROGRAMMED_SETPOINTS = (
    (1, "Chauffage", "Confort", "heat_setpoint_c1", 710),
    (1, "Chauffage", "Éco", "heat_reduced_setpoint_c1", 712),
    (1, "Rafraîchissement", "Confort", "cool_setpoint_c1", 902),
    (1, "Rafraîchissement", "Éco", "cool_reduced_setpoint_c1", 903),
    (2, "Chauffage", "Confort", "heat_setpoint_c2", 1010),
    (2, "Chauffage", "Éco", "heat_reduced_setpoint_c2", 1012),
    (2, "Rafraîchissement", "Confort", "cool_setpoint_c2", 1202),
    (2, "Rafraîchissement", "Éco", "cool_reduced_setpoint_c2", 1203),
)



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
            *(AlfeaProgrammedSetpointNumber(hass, entry, item) for item in _PROGRAMMED_SETPOINTS),
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


class AlfeaProgrammedSetpointNumber(NumberEntity):
    """Writable native Comfort/Reduced setpoint, separate from temporary overrides."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:thermometer-cog"
    _attr_native_min_value = 7.0
    _attr_native_max_value = 35.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, item: tuple) -> None:
        self.hass = hass
        self._entry = entry
        circuit, season, profile, key, parameter = item
        self._attr_native_min_value = 7.0
        self._attr_native_max_value = 35.0 if season == "Chauffage" else 30.0
        self._key = key
        self._parameter = parameter
        self._attr_unique_id = f"{entry.entry_id}_control_{key}"
        self._attr_name = f"Circuit {circuit} — {season} — Régler {profile}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _source(self) -> str | None:
        return source_entity(self.hass, self._entry, self._key, self._parameter)

    @property
    def native_value(self) -> float | None:
        return state_float(self.hass, self._source())

    @property
    def available(self) -> bool:
        source = self._source()
        return (
            source is not None
            and source.split(".", 1)[0] in ("number", "text")
            and self.native_value is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"parametre_bsb": self._parameter}

    async def async_set_native_value(self, value: float) -> None:
        source = self._source()
        if source is None or source.split(".", 1)[0] not in ("number", "text"):
            raise HomeAssistantError(
                f"Paramètre BSB {self._parameter} non disponible en écriture."
            )
        value = float(value)
        if (
            not self.native_min_value <= value <= self.native_max_value
            or abs(round(value * 2) - value * 2) > 1e-6
        ):
            raise HomeAssistantError(
                f"Consigne attendue de {self.native_min_value:g} à "
                f"{self.native_max_value:g} °C, par pas de 0,5 °C."
            )
        try:
            await async_set_numeric_entity(self.hass, source, value)
        except Exception as exc:
            raise HomeAssistantError(
                f"Écriture BSB {self._parameter} refusée : {exc}"
            ) from exc

        # The HA service call only confirms dispatch, not acceptance by the PAC.
        # Request a fresh BSB reading and check the actual returned value.
        await async_poll_parameters(self.hass, (self._parameter,))
        for _ in range(20):
            confirmed = state_float(self.hass, source)
            if confirmed is not None and abs(confirmed - value) < 0.01:
                self.async_write_ha_state()
                return
            await asyncio.sleep(0.5)
        raise HomeAssistantError(
            f"Consigne BSB {self._parameter} envoyée mais non confirmée "
            "après 10 secondes : vérifier le retour BSB-LAN."
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            track_entities(self.hass, [self._source()], self.async_write_ha_state)
        )
