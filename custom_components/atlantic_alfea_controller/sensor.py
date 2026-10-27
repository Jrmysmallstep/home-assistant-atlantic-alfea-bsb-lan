"""Diagnostic proxy and calculated sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .clock import clock_offset_seconds, clock_source_age_seconds, clock_source_ids, pac_clock_datetime
from .const import CONF_Q3_DIVERTER_CONFIRMED, DOMAIN, MODE_COOL, MODE_HEAT
from .helpers import clean_bsb_status, effective_season, is_protection, source_entity, split_bsb_status, state_float, state_is_on, state_value, track_entities
from .runtime import AlfeaRuntimeMonitor
from .regime_api import valid_base_url
from .weekly_programs import PROGRAMS


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
    enabled_default: bool = True


DESCRIPTIONS = (
    SensorDescription("pac_state", "PAC - État", "mdi:heat-pump", numeric=False, clean_bsb_code=True),
    SensorDescription("heat_state_c1", "C1 - Chauffage État", "mdi:radiator", numeric=False, clean_bsb_code=True, entity_category=EntityCategory.DIAGNOSTIC, enabled_default=False),
    SensorDescription("heat_state_c2", "C2 - Chauffage État", "mdi:radiator", numeric=False, clean_bsb_code=True, entity_category=EntityCategory.DIAGNOSTIC, enabled_default=False),
    SensorDescription("cool_state_c1", "C1 - Rafraîch. État", "mdi:snowflake", numeric=False, clean_bsb_code=True, entity_category=EntityCategory.DIAGNOSTIC, enabled_default=False),
    SensorDescription("cool_state_c2", "C2 - Rafraîch. État", "mdi:snowflake", numeric=False, clean_bsb_code=True, entity_category=EntityCategory.DIAGNOSTIC, enabled_default=False),
    SensorDescription("heat_flow_target_c1", "C1 - Chauffage T. départ cible", "mdi:thermometer-chevron-up", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C"),
    SensorDescription("heat_flow_target_c2", "C2 - Chauffage T. départ cible", "mdi:thermometer-chevron-up", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C"),
    SensorDescription("dhw_state", "ECS - État", "mdi:water-boiler", numeric=False, clean_bsb_code=True),
    SensorDescription(
        "dhw_nominal_setpoint",
        "ECS - T. Confort",
        "mdi:thermometer-water",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        "°C",
    ),
    SensorDescription(
        "dhw_reduced_setpoint",
        "ECS - T. Éco",
        "mdi:thermometer-low",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        "°C",
    ),
    SensorDescription(
        "dhw_temperature",
        "ECS - T. ballon",
        "mdi:water-thermometer",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        "°C",
    ),
    SensorDescription(
        "compressor_modulation",
        "COMP - Modulation",
        "mdi:gauge",
        unit="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorDescription(
        "energy_total",
        "PAC - Énergie totale",
        "mdi:lightning-bolt",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        "kWh",
    ),
    SensorDescription(
        "flow_temp",
        "PAC - T. départ",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit="°C",
    ),
    SensorDescription(
        "return_temp",
        "PAC - T. retour",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit="°C",
    ),
    SensorDescription(
        "target_flow_temp",
        "PAC - T. départ cible",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit="°C",
    ),
    SensorDescription(
        "outdoor_temp",
        "PAC - T. extérieure",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit="°C",
    ),
    SensorDescription(
        "compressor_hours",
        "COMP - Heures de fonctionnement",
        "mdi:timer",
        SensorDeviceClass.DURATION,
        SensorStateClass.TOTAL_INCREASING,
        "h",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_starts",
        "COMP - Nombre de démarrages",
        "mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit="démarrages",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_min_run",
        "COMP - Temps de marche minimum",
        "mdi:timer-play-outline",
        SensorDeviceClass.DURATION,
        SensorStateClass.MEASUREMENT,
        "min",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_min_off",
        "COMP - Temps d’arrêt minimum",
        "mdi:timer-pause-outline",
        SensorDeviceClass.DURATION,
        SensorStateClass.MEASUREMENT,
        "min",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_starts_max_rate",
        "COMP - Seuil de démarrages régulateur",
        "mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        unit="démarrages/h",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDescription(
        "compressor_starts_current_rate",
        "COMP - Démarrages régulateur",
        "mdi:speedometer-medium",
        state_class=SensorStateClass.MEASUREMENT,
        unit="démarrages/h",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


# The eight programmed setpoints are independent of the effective room target.
# BSB 8741/8771 may change with the program or native override, whereas these
# values remain the underlying Comfort/Reduced settings for each season.
_PROGRAMMED_SETPOINTS = (
    (1, "Chauffage", "Confort", "heat_setpoint_c1", 710),
    (1, "Chauffage", "Réduite (Éco)", "heat_reduced_setpoint_c1", 712),
    (1, "Rafraîchissement", "Confort", "cool_setpoint_c1", 902),
    (1, "Rafraîchissement", "Réduite (Éco)", "cool_reduced_setpoint_c1", 903),
    (2, "Chauffage", "Confort", "heat_setpoint_c2", 1010),
    (2, "Chauffage", "Réduite (Éco)", "heat_reduced_setpoint_c2", 1012),
    (2, "Rafraîchissement", "Confort", "cool_setpoint_c2", 1202),
    (2, "Rafraîchissement", "Réduite (Éco)", "cool_reduced_setpoint_c2", 1203),
)


# Custom BSB-LAN read-only parameters. These do not control the PAC or its
# native schedules. Keep absent/unknown parameter values as unavailable.
_CIRCUIT_PROGRAM_DIAGNOSTICS = (
    (1, "Régime temporaire", 10110),
    (2, "Régime temporaire", 10120),
    (1, "Programme actif", 10112),
    (2, "Programme actif", 10122),
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
        "ECS - Production",
        lambda monitor: monitor.dhw_production_state,
        "mdi:water-boiler-auto",
        state_class=None,
        entity_category=None,
    ),
    CalculatedSensorDescription(
        "average_cycle_duration",
        "COMP - Durée moyenne historique d’un cycle",
        lambda monitor: monitor.average_cycle_duration_minutes,
        "mdi:timer-sync-outline",
        "min",
        SensorDeviceClass.DURATION,
    ),
    CalculatedSensorDescription(
        "last_cycle_duration",
        "COMP - Durée du dernier cycle",
        lambda monitor: monitor.last_cycle_duration_minutes,
        "mdi:timer-outline",
        "min",
        SensorDeviceClass.DURATION,
    ),
    CalculatedSensorDescription(
        "last_off_duration",
        "COMP - Durée du dernier arrêt",
        lambda monitor: monitor.last_off_duration_minutes,
        "mdi:timer-pause",
        "min",
        SensorDeviceClass.DURATION,
    ),
    CalculatedSensorDescription(
        "starts_today",
        "COMP - Démarrages aujourd’hui",
        lambda monitor: monitor.starts_today,
        "mdi:counter",
        "démarrages",
    ),
    CalculatedSensorDescription(
        "starts_last_hour",
        "COMP - Démarrages sur la dernière heure",
        lambda monitor: monitor.starts_last_hour,
        "mdi:history",
        "démarrages",
    ),
    CalculatedSensorDescription(
        "short_cycles_last_six_hours",
        "COMP - Cycles courts sur 6 heures",
        lambda monitor: monitor.short_cycles_last_six_hours,
        "mdi:timer-alert-outline",
        "cycles",
    ),
    CalculatedSensorDescription(
        "flow_target_gap",
        "PAC - Écart départ / consigne",
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
    entities.extend(AlfeaCircuitSeasonStateSensor(hass, entry, circuit) for circuit in (1, 2))
    entities.append(AlfeaV3VCommandSensor(hass, entry))
    entities.extend(AlfeaWeeklyProgramSensor(hass, entry, key) for key in PROGRAMS)
    if valid_base_url(str(entry.options.get('bsb_base_url', '')).strip()):
        entities.append(AlfeaFaultHistorySensor(hass, entry))
    entities.extend(AlfeaCircuitProgramDiagnosticSensor(hass, entry, item) for item in _CIRCUIT_PROGRAM_DIAGNOSTICS)
    entities.extend(AlfeaProgrammedSetpointSensor(hass, entry, item) for item in _PROGRAMMED_SETPOINTS)
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
        self._attr_entity_registry_enabled_default = desc.enabled_default
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


class AlfeaWeeklyProgramSensor(SensorEntity):
    """Expose the PAC's native weekly program, imported only on demand."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, key: str) -> None:
        self.hass = hass
        self._entry = entry
        self._key = key
        name, icon, _base = PROGRAMS[key]
        self._attr_name = f"Programme natif - {name}"
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_weekly_program_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _importer(self):
        return self.hass.data.get(DOMAIN, {}).get("weekly_programs", {}).get(self._entry.entry_id)

    @property
    def native_value(self) -> str:
        importer = self._importer()
        if importer is None or not importer.configured:
            return "À configurer"
        return importer.snapshots[self._key].status

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        importer = self._importer()
        if importer is None:
            return {}
        snapshot = importer.snapshots[self._key]
        _name, _icon, base = PROGRAMS[self._key]
        return {
            "lecture_seule": True,
            "source": "BSB-LAN JSON /JQ",
            "parametre_lundi": base,
            "derniere_importation": snapshot.updated,
            "erreur_derniere_lecture": snapshot.error,
            "jours": snapshot.days or {},
        }

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(
            self.hass,
            f"{DOMAIN}_weekly_programs_{self._entry.entry_id}",
            self.async_write_ha_state,
        ))


class AlfeaV3VCommandSensor(SensorEntity):
    """Read-only Q3 command, validated on a diverter-equipped Alféa.

    8820 is the Q3 activation signal, not a physical valve-position feedback.
    Only expose A/B when BSB 5731 confirms Q3 as a diverter, or when
    the user explicitly confirms that fixed configuration in options.
    """

    _attr_has_entity_name = True
    _attr_name = "V3V - Commande"
    _attr_icon = "mdi:valve"
    _attr_state_class = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_v3v_command"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _configuration_source(self) -> str | None:
        return source_entity(self.hass, self._entry, "dhw_q3_type", 5731)

    def _command_source(self) -> str | None:
        return source_entity(self.hass, self._entry, "dhw_pump", 8820)

    def _is_diverter(self) -> bool:
        raw = state_value(self.hass, self._configuration_source())
        if raw is not None:
            # An actual 5731 reading always takes precedence over the manual
            # declaration, especially if the hardware configuration changes.
            code, label = split_bsb_status(raw)
            return code == 2 or raw.strip() == "2" or (
                label is not None and "vanne de dérivation" in label.casefold()
            )
        return self._entry.options.get(CONF_Q3_DIVERTER_CONFIRMED, False) is True

    def _command(self) -> bool | None:
        command = state_is_on(self.hass, self._command_source())
        if command is not None:
            return command
        # Fallback when BSB-LAN publishes 8820 but MQTT discovery has not
        # created an entity. None means no valid status message received yet.
        return self.hass.data.get(DOMAIN, {}).get("v3v_feedback", {}).get(self._entry.entry_id)

    @property
    def native_value(self) -> str | None:
        if not self._is_diverter():
            return None
        command = self._command()
        if command is None:
            return None
        return "ECS" if command else "Chauffage"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        state = self.native_value
        return {
            "position_commandee": "A" if state == "ECS" else "B" if state == "Chauffage" else None,
            "organe_q3": "Vanne de dérivation" if self._is_diverter() else "Non confirmé",
            "configuration_confirmee_manuellement": (
                state_value(self.hass, self._configuration_source()) is None
                and self._entry.options.get(CONF_Q3_DIVERTER_CONFIRMED, False) is True
            ),
            "parametre_configuration": 5731,
            "parametre_commande": 8820,
            "source_commande": (
                "entite_home_assistant" if state_is_on(self.hass, self._command_source()) is not None
                else "mqtt_direct" if self._command() is not None else "indisponible"
            ),
            "retour_position_mecanique": False,
        }

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(track_entities(
            self.hass,
            [self._configuration_source(), self._command_source()],
            self.async_write_ha_state,
        ))
        self.async_on_remove(async_dispatcher_connect(
            self.hass,
            f"{DOMAIN}_v3v_feedback_{self._entry.entry_id}",
            self.async_write_ha_state,
        ))


class AlfeaCircuitProgramDiagnosticSensor(SensorEntity):
    """Read-only native BSB regime and schedule diagnostics."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, item: tuple[int, str, int]) -> None:
        self.hass = hass
        self._entry = entry
        circuit, label, parameter = item
        self._parameter = parameter
        self._attr_name = f"C{circuit} - {label}"
        self._attr_unique_id = f"{entry.entry_id}_program_diagnostic_{parameter}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _source(self) -> str | None:
        return source_entity(self.hass, self._entry, f"program_diagnostic_{self._parameter}", self._parameter)

    @property
    def native_value(self) -> str | None:
        return clean_bsb_status(state_value(self.hass, self._source()))

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"parametre_bsb": self._parameter}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(track_entities(self.hass, [self._source()], self.async_write_ha_state))


class AlfeaProgrammedSetpointSensor(SensorEntity):
    """Read-only diagnostic for a native BSB programmed setpoint."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:thermometer-cog"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, item: tuple) -> None:
        self.hass = hass
        self._entry = entry
        circuit, season, profile, key, parameter = item
        self._key = key
        self._parameter = parameter
        self._attr_name = f"C{circuit} - {'Rafraîch.' if season == 'Rafraîchissement' else season} Cons. {'Conf' if profile == 'Confort' else 'Éco'}"
        self._attr_unique_id = f"{entry.entry_id}_programmed_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _source(self) -> str | None:
        return source_entity(self.hass, self._entry, self._key, self._parameter)

    @property
    def native_value(self) -> float | None:
        return state_float(self.hass, self._source())

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"parametre_bsb": self._parameter}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            track_entities(self.hass, [self._source()], self.async_write_ha_state)
        )


class AlfeaCircuitSeasonStateSensor(SensorEntity):
    """Season-appropriate native BSB-LAN circuit status.

    Retain existing entity identifiers and original controller wording.
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:home-thermometer"
    _attr_state_class = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, circuit: int) -> None:
        self.hass = hass
        self._entry = entry
        self._circuit = circuit
        self._attr_name = f"C{circuit} - État actuel"
        self._attr_unique_id = f"{entry.entry_id}_circuit_{circuit}_current_state"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _raw_status(self) -> tuple[int, str | None]:
        """BSB-LAN native status for the currently selected season; no inference."""
        season = effective_season(self.hass, self._entry)
        if season == MODE_HEAT:
            parameter = 8000 if self._circuit == 1 else 8001
            prefix = "heat"
        elif season == MODE_COOL:
            parameter = 8004 if self._circuit == 1 else 8025
            prefix = "cool"
        else:
            return 0, None
        return parameter, state_value(
            self.hass,
            source_entity(self.hass, self._entry, f"{prefix}_state_c{self._circuit}", parameter),
        )

    @property
    def native_value(self) -> str | None:
        _parameter, raw = self._raw_status()
        if _parameter == 0:
            return "Arrêt"
        return clean_bsb_status(raw)

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        parameter, raw = self._raw_status()
        return {
            "saison": effective_season(self.hass, self._entry),
            "parametre_etat_bsb": parameter,
            "regime_bsb": clean_bsb_status(raw),
            "etat_bsb_brut": raw,
        }

    async def async_added_to_hass(self) -> None:
        tracked = []
        for prefix, params in (("heat", (8000, 8001)), ("cool", (8004, 8025))):
            tracked.append(source_entity(
                self.hass, self._entry,
                f"{prefix}_state_c{self._circuit}", params[self._circuit - 1],
            ))
        self.async_on_remove(track_entities(self.hass, tracked, self.async_write_ha_state))


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

    _attr_name = "Horloge PAC - Date et heure"
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
    _attr_name = "Horloge PAC - Décalage"
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


class AlfeaFaultHistorySensor(SensorEntity):
    """Historical BSB faults, without treating old records as live alarms."""

    _attr_has_entity_name = True
    _attr_name = "PAC - Historique des défauts"
    _attr_icon = "mdi:history"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_fault_history"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _snapshot(self):
        return self.hass.data.get(DOMAIN, {}).get("fault_history", {}).get(
            self._entry.entry_id, {}
        )

    @property
    def native_value(self):
        snapshot = self._snapshot()
        if snapshot.get("status") != "Chargé":
            return "Indisponible"
        count = len(snapshot.get("entries", []))
        return "Aucun défaut enregistré" if count == 0 else f"{count} défaut(s) enregistré(s)"

    @property
    def extra_state_attributes(self):
        snapshot = self._snapshot()
        return {
            "statut_lecture": snapshot.get("status", "Indisponible"),
            "date_lecture": snapshot.get("updated"),
            "defauts": snapshot.get("entries", []),
            "lecture_seule": True,
        }

    async def async_added_to_hass(self):
        self.async_on_remove(async_dispatcher_connect(
            self.hass,
            f"{DOMAIN}_fault_history_{self._entry.entry_id}",
            self.async_write_ha_state,
        ))
