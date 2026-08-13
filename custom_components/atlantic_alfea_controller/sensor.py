"""Diagnostic proxy and calculated sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .clock import clock_offset_seconds, clock_source_age_seconds, clock_source_ids, pac_clock_datetime
from .const import DOMAIN
from .helpers import clean_bsb_status, split_bsb_status, state_float, state_value, track_entities
from .runtime import AlfeaRuntimeMonitor


@dataclass(frozen=True)
class SensorDescription:
    key: str
    name: str
    icon: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    unit: str | None = None
    numeric: bool = True
    clean_bsb_code: bool = False
    entity_category: EntityCategory | None = None


DESCRIPTIONS = (
    SensorDescription("pac_state", "PAC — État général", "mdi:heat-pump", numeric=False, clean_bsb_code=True),
    SensorDescription("heat_state_c1", "Circuit 1 — Chauffage — État", "mdi:radiator", numeric=False, clean_bsb_code=True),
    SensorDescription("heat_state_c2", "Circuit 2 — Chauffage — État", "mdi:radiator", numeric=False, clean_bsb_code=True),
    SensorDescription("cool_state_c1", "Circuit 1 — Rafraîchissement — État", "mdi:snowflake", numeric=False, clean_bsb_code=True),
    SensorDescription("cool_state_c2", "Circuit 2 — Rafraîchissement — État", "mdi:snowflake", numeric=False, clean_bsb_code=True),
    SensorDescription("heat_flow_target_c1", "Circuit 1 — Chauffage — Consigne départ résultante", "mdi:thermometer-chevron-up", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C"),
    SensorDescription("heat_flow_target_c2", "Circuit 2 — Chauffage — Consigne départ résultante", "mdi:thermometer-chevron-up", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C"),
    SensorDescription("dhw_state", "ECS — État", "mdi:water-boiler", numeric=False, clean_bsb_code=True),
    SensorDescription(
        "dhw_nominal_setpoint",
        "ECS — Consigne nominale",
        "mdi:thermometer-water",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        "°C",
    ),
    SensorDescription(
        "dhw_reduced_setpoint",
        "ECS — Consigne réduite",
        "mdi:thermometer-low",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        "°C",
    ),
    SensorDescription(
        "dhw_temperature",
        "ECS — Température ballon",
        "mdi:water-thermometer",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        "°C",
    ),
    SensorDescription(
        "compressor_modulation",
        "Compresseur — Modulation",
        "mdi:gauge",
        unit="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorDescription(
        "energy_total",
        "PAC — Énergie utilisée (BSB)",
        "mdi:lightning-bolt",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "kWh",
    ),
    SensorDescription(
        "flow_temp",
        "PAC — Température départ",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit="°C",
    ),
    SensorDescription(
        "return_temp",
        "PAC — Température retour",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit="°C",
    ),
    SensorDescription(
        "target_flow_temp",
        "PAC — Consigne départ",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit="°C",
    ),
    SensorDescription(
        "outdoor_temp",
        "PAC — Température extérieure",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit="°C",
    ),
    SensorDescription(
        "compressor_hours",
        "Compresseur — Heures de fonctionnement",
        "mdi:timer",
        SensorDeviceClass.DURATION,
        SensorStateClass.TOTAL_INCREASING,
        "h",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_starts",
        "Compresseur — Nombre de démarrages",
        "mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit="démarrages",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_min_run",
        "Compresseur — Temps de marche minimum",
        "mdi:timer-play-outline",
        SensorDeviceClass.DURATION,
        SensorStateClass.MEASUREMENT,
        "min",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_min_off",
        "Compresseur — Temps d’arrêt minimum",
        "mdi:timer-pause-outline",
        SensorDeviceClass.DURATION,
        SensorStateClass.MEASUREMENT,
        "min",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_starts_max_rate",
        "Compresseur — Seuil de démarrages régulateur",
        "mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        unit="démarrages/h",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_starts_current_rate",
        "Compresseur — Démarrages régulateur",
        "mdi:speedometer-medium",
        state_class=SensorStateClass.MEASUREMENT,
        unit="démarrages/h",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


@dataclass(frozen=True)
class CalculatedSensorDescription:
    key: str
    name: str
    value_fn: Callable[[AlfeaRuntimeMonitor], float | int | str | None]
    icon: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT
    entity_category: EntityCategory | None = EntityCategory.DIAGNOSTIC


CALCULATED_DESCRIPTIONS = (
    CalculatedSensorDescription(
        "dhw_production",
        "ECS — Production",
        lambda monitor: monitor.dhw_production_state,
        "mdi:water-boiler-auto",
        state_class=None,
        entity_category=None,
    ),
    CalculatedSensorDescription(
        "average_cycle_duration",
        "Compresseur — Durée moyenne historique d’un cycle",
        lambda monitor: monitor.average_cycle_duration_minutes,
        "mdi:timer-sync-outline",
        "min",
        SensorDeviceClass.DURATION,
    ),
    CalculatedSensorDescription(
        "last_cycle_duration",
        "Compresseur — Durée du dernier cycle",
        lambda monitor: monitor.last_cycle_duration_minutes,
        "mdi:timer-outline",
        "min",
        SensorDeviceClass.DURATION,
    ),
    CalculatedSensorDescription(
        "last_off_duration",
        "Compresseur — Durée du dernier arrêt",
        lambda monitor: monitor.last_off_duration_minutes,
        "mdi:timer-pause",
        "min",
        SensorDeviceClass.DURATION,
    ),
    CalculatedSensorDescription(
        "starts_today",
        "Compresseur — Démarrages aujourd’hui",
        lambda monitor: monitor.starts_today,
        "mdi:counter",
        "démarrages",
    ),
    CalculatedSensorDescription(
        "starts_last_hour",
        "Compresseur — Démarrages sur la dernière heure",
        lambda monitor: monitor.starts_last_hour,
        "mdi:history",
        "démarrages",
    ),
    CalculatedSensorDescription(
        "short_cycles_last_six_hours",
        "Compresseur — Cycles courts sur 6 heures",
        lambda monitor: monitor.short_cycles_last_six_hours,
        "mdi:timer-alert-outline",
        "cycles",
    ),
    CalculatedSensorDescription(
        "flow_target_gap",
        "PAC — Écart départ / consigne",
        lambda monitor: monitor.flow_gap,
        "mdi:thermometer-alert",
        "°C",
        SensorDeviceClass.TEMPERATURE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[SensorEntity] = [
        AlfeaProxySensor(hass, entry, desc)
        for desc in DESCRIPTIONS
        if entry.data.get(desc.key)
    ]
    if isinstance(entry.runtime_data, AlfeaRuntimeMonitor):
        entities.extend(
            AlfeaCalculatedSensor(entry, entry.runtime_data, desc)
            for desc in CALCULATED_DESCRIPTIONS
        )
    if all(clock_source_ids(hass, entry)):
        entities.extend(
            [
                AlfeaClockDateTimeSensor(hass, entry),
                AlfeaClockOffsetSensor(hass, entry),
            ]
        )
    async_add_entities(entities)


class AlfeaProxySensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, desc: SensorDescription) -> None:
        self.hass = hass
        self._entry = entry
        self._desc = desc
        self._source = entry.data[desc.key]
        self._attr_name = desc.name
        self._attr_unique_id = f"{entry.entry_id}_{desc.key}"
        self._attr_icon = desc.icon
        self._attr_device_class = desc.device_class
        self._attr_state_class = desc.state_class
        self._attr_native_unit_of_measurement = desc.unit
        self._attr_entity_category = desc.entity_category
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def native_value(self):
        if self._desc.numeric:
            return state_float(self.hass, self._source)
        raw = state_value(self.hass, self._source)
        return clean_bsb_status(raw) if self._desc.clean_bsb_code else raw

    @property
    def extra_state_attributes(self) -> dict[str, str | int] | None:
        if not self._desc.clean_bsb_code:
            return None
        raw = state_value(self.hass, self._source)
        code, _text = split_bsb_status(raw)
        attributes: dict[str, str | int] = {}
        if code is not None:
            attributes["code_bsb"] = code
        if raw is not None:
            attributes["etat_bsb_brut"] = raw
        return attributes or None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(track_entities(self.hass, [self._source], self.async_write_ha_state))


class AlfeaCalculatedSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        monitor: AlfeaRuntimeMonitor,
        desc: CalculatedSensorDescription,
    ) -> None:
        self._monitor = monitor
        self._desc = desc
        self._attr_name = desc.name
        self._attr_unique_id = f"{entry.entry_id}_{desc.key}"
        self._attr_icon = desc.icon
        self._attr_device_class = desc.device_class
        self._attr_state_class = desc.state_class
        self._attr_native_unit_of_measurement = desc.unit
        self._attr_entity_category = desc.entity_category
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def native_value(self) -> float | int | str | None:
        return self._desc.value_fn(self._monitor)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._monitor.async_add_listener(self.async_write_ha_state))



class _AlfeaClockSensorBase(SensorEntity):
    """Base class for clock diagnostic sensors."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    async def async_added_to_hass(self) -> None:
        # Update only when BSB parameter 0 is actually republished. The hourly
        # poll is the source of truth; no synthetic local ticking is generated.
        self.async_on_remove(
            track_entities(
                self.hass,
                list(clock_source_ids(self.hass, self._entry)),
                self.async_write_ha_state,
            )
        )


class AlfeaClockDateTimeSensor(_AlfeaClockSensorBase):
    """PAC date and time read from BSB parameter 0."""

    _attr_name = "Horloge PAC — Date et heure"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_pac_clock_datetime"

    @property
    def native_value(self) -> str | None:
        value = pac_clock_datetime(self.hass, self._entry)
        if value is None:
            return None
        return value.strftime("%d/%m/%Y à %H:%M:%S")


class AlfeaClockOffsetSensor(_AlfeaClockSensorBase):
    """Signed difference between the PAC clock and Home Assistant."""

    _attr_entity_registry_enabled_default = False
    _attr_name = "Horloge PAC — Décalage"
    _attr_icon = "mdi:clock-alert-outline"
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_pac_clock_offset"

    @property
    def native_value(self) -> int | None:
        return clock_offset_seconds(self.hass, self._entry)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        value = self.native_value
        if value is None:
            return None
        age = clock_source_age_seconds(self.hass, self._entry)
        return {
            "sens": "PAC en avance" if value > 0 else "PAC en retard" if value < 0 else "synchronisée",
            "age_derniere_lecture_bsb_s": age,
        }
