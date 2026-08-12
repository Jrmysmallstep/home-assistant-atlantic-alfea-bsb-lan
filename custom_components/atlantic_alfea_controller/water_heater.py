"""Domestic hot water entity for Atlantic Alfea BSB-LAN."""

from __future__ import annotations

from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DHW_ECO,
    DHW_OFF,
    DHW_ON,
    DHW_OPERATIONS,
    DOMAIN,
    TEMPERATURE_STEP,
)
from .helpers import (
    async_select_option,
    source_entity,
    state_float,
    state_is_on,
    state_value,
    track_entities,
)

_MODE_OPTIONS = {
    DHW_OFF: "0 - Arrêt",
    DHW_ON: "1 - Marche",
    DHW_ECO: "2 - Eco",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    # The Alfea controller can expose the ECS controls without publishing the
    # tank temperature parameter. Keep the water-heater entity available in
    # that case; current_temperature will simply remain unknown.
    required = [
        source_entity(hass, entry, "dhw_mode", 1600),
        source_entity(hass, entry, "dhw_nominal_setpoint", 1610),
        source_entity(hass, entry, "dhw_reduced_setpoint", 1612),
    ]
    if all(required):
        async_add_entities([AlfeaWaterHeater(hass, entry)])


class AlfeaWaterHeater(WaterHeaterEntity):
    """Represent the Alfea domestic hot water tank."""

    _attr_has_entity_name = True
    _attr_name = "Eau chaude sanitaire"
    _attr_temperature_unit = "°C"
    _attr_min_temp = 30.0
    _attr_max_temp = 65.0
    _attr_target_temperature_step = TEMPERATURE_STEP
    _attr_operation_list = DHW_OPERATIONS
    # The ECS setpoint is intentionally read-only in Home Assistant.
    # The PAC schedule/regulator remains the source of truth for temperature.
    _attr_supported_features = WaterHeaterEntityFeature.OPERATION_MODE

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_dhw"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})
        self._monitor = entry.runtime_data

    def _source(self, key: str, parameter: int) -> str | None:
        return source_entity(self.hass, self._entry, key, parameter)

    @property
    def current_temperature(self) -> float | None:
        return state_float(self.hass, self._source("dhw_temperature", 8830))

    @property
    def current_operation(self) -> str | None:
        raw = state_value(self.hass, self._source("dhw_mode", 1600))
        if not raw:
            return None
        if raw.startswith("0 -") or "arrêt" in raw.lower():
            return DHW_OFF
        if raw.startswith("2 -") or "eco" in raw.lower():
            return DHW_ECO
        if raw.startswith("1 -") or "marche" in raw.lower():
            return DHW_ON
        return None

    def _active_setpoint(self) -> tuple[str, int] | None:
        """Return the setpoint explicitly reported by ECS state 8003.

        BSB mode 1600 = Eco does not mean that the reduced 1612 setpoint is
        necessarily active. On the tested controller, 8003 can report a nominal
        charge while 1600 remains Eco.
        """
        state = state_value(self.hass, self._source("dhw_state", 8003))
        normalized = state.lower() if state else ""
        if any(marker in normalized for marker in ("réduit", "reduit", "reduced")):
            return "dhw_reduced_setpoint", 1612
        if any(marker in normalized for marker in ("nominal", "nominale")):
            return "dhw_nominal_setpoint", 1610
        if self.current_operation == DHW_ON:
            return "dhw_nominal_setpoint", 1610
        return None

    @property
    def target_temperature(self) -> float | None:
        active = self._active_setpoint()
        if active is None:
            # Keep a useful read-only target when the exact active regime is not
            # reported, without pretending that Eco always means 1612.
            active = ("dhw_nominal_setpoint", 1610)
        key, parameter = active
        return state_float(self.hass, self._source(key, parameter))

    @property
    def production_state(self) -> str | None:
        """Return the instantaneous ECS production state calculated by runtime."""
        production = getattr(self._monitor, "dhw_production_state", None)
        return production if isinstance(production, str) else None

    @property
    def icon(self) -> str:
        """Adapt the icon to the instantaneous ECS production state."""
        production = self.production_state
        if production == "Chauffe par PAC":
            return "mdi:heat-pump"
        if production == "Appoint électrique":
            return "mdi:lightning-bolt"
        if production == "PAC + appoint électrique":
            return "mdi:water-boiler-alert"
        if production == "Demande / attente":
            return "mdi:water-boiler-auto"
        return "mdi:water-boiler-off"

    @property
    def extra_state_attributes(self) -> dict[str, str | float | bool | None]:
        production = self.production_state
        compressor = state_is_on(self.hass, self._source("compressor_state", 8400))
        modulation = state_float(self.hass, self._source("compressor_modulation", 8413))
        return {
            "production": production,
            "demande_ecs": getattr(self._monitor, "dhw_charging", None),
            "etat_ecs_bsb": state_value(self.hass, self._source("dhw_state", 8003)),
            "etat_generateur_bsb": state_value(self.hass, self._source("pac_state", 8006)),
            "consigne_nominale": state_float(self.hass, self._source("dhw_nominal_setpoint", 1610)),
            "consigne_reduite": state_float(self.hass, self._source("dhw_reduced_setpoint", 1612)),
            "regime_consigne_actif": (
                "réduit" if self._active_setpoint() == ("dhw_reduced_setpoint", 1612)
                else "nominal" if self._active_setpoint() == ("dhw_nominal_setpoint", 1610)
                else "indéterminé"
            ),
            "compresseur_actif": compressor,
            "modulation_compresseur": modulation,
            "pompe_ecs": state_is_on(self.hass, self._source("dhw_pump", 8820)),
            "appoint_electrique": state_is_on(self.hass, self._source("dhw_electric_heater", 8821)),
        }

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        if operation_mode not in _MODE_OPTIONS:
            raise HomeAssistantError(f"Mode ECS non pris en charge : {operation_mode}")
        source = self._source("dhw_mode", 1600)
        if source is None:
            raise HomeAssistantError("Entité BSB-LAN 1600 introuvable.")
        await async_select_option(self.hass, source, _MODE_OPTIONS[operation_mode])

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            track_entities(
                self.hass,
                [
                    self._source("dhw_mode", 1600),
                    self._source("dhw_nominal_setpoint", 1610),
                    self._source("dhw_reduced_setpoint", 1612),
                    self._source("dhw_state", 8003),
                    self._source("pac_state", 8006),
                    self._source("dhw_temperature", 8830),
                    self._source("dhw_pump", 8820),
                    self._source("dhw_electric_heater", 8821),
                    self._source("compressor_state", 8400),
                    self._source("compressor_modulation", 8413),
                ],
                self.async_write_ha_state,
            )
        )
