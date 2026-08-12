"""Diagnostic and alert binary sensors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .clock import clock_offset_seconds, clock_source_ids, clock_source_is_fresh
from .const import CLOCK_DESYNC_THRESHOLD_SECONDS, DOMAIN
from .helpers import split_bsb_status, state_is_on, state_value, track_entities
from .runtime import AlfeaRuntimeMonitor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[BinarySensorEntity] = []
    if entry.data.get("override_c1"):
        entities.append(AlfeaOverrideBinarySensor(hass, entry, 1, "override_c1"))
    if entry.data.get("override_c2"):
        entities.append(AlfeaOverrideBinarySensor(hass, entry, 2, "override_c2"))
    if entry.data.get("compressor_state"):
        entities.append(
            AlfeaBinaryProxy(
                hass,
                entry,
                "compressor_state",
                "Compresseur — État",
                "mdi:engine",
                BinarySensorDeviceClass.RUNNING,
            )
        )
    if entry.data.get("defrost"):
        entities.append(
            AlfeaBinaryProxy(
                hass,
                entry,
                "defrost",
                "PAC — Entrée dégivrage DI6",
                "mdi:snowflake-alert",
                BinarySensorDeviceClass.RUNNING,
                EntityCategory.DIAGNOSTIC,
            )
        )
    if entry.data.get("dhw_electric_heater"):
        entities.append(
            AlfeaBinaryProxy(
                hass,
                entry,
                "dhw_electric_heater",
                "ECS — Appoint électrique",
                "mdi:water-boiler",
                BinarySensorDeviceClass.RUNNING,
                EntityCategory.DIAGNOSTIC,
            )
        )
    if entry.data.get("dhw_pump"):
        entities.append(
            AlfeaBinaryProxy(
                hass,
                entry,
                "dhw_pump",
                "ECS — Pompe",
                "mdi:pump",
                BinarySensorDeviceClass.RUNNING,
                EntityCategory.DIAGNOSTIC,
            )
        )
    if isinstance(entry.runtime_data, AlfeaRuntimeMonitor):
        entities.extend(
            AlfeaAlertBinarySensor(entry, entry.runtime_data, description)
            for description in ALERT_DESCRIPTIONS
        )
    if all(clock_source_ids(hass, entry)):
        entities.append(AlfeaClockDesyncBinarySensor(hass, entry))
    async_add_entities(entities)


class AlfeaOverrideBinarySensor(BinarySensorEntity):
    """Report the native room-setpoint override/deviation state.

    Tests on this Alfea controller established code 1 as the neutral state.
    A temporary native override changed the value away from 1 and returned to
    1 when cancelled. This entity is deliberately read-only: the integration
    does not invent the write protocol for starting an override.
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:thermometer-chevron-up"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, circuit: int, key: str) -> None:
        self.hass = hass
        self._source = entry.data[key]
        self._circuit = circuit
        self._attr_name = f"Circuit {circuit} — Dérogation native"
        self._attr_unique_id = f"{entry.entry_id}_{key}_active"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def is_on(self) -> bool | None:
        raw = state_value(self.hass, self._source)
        code, _text = split_bsb_status(raw)
        if code is None:
            return None
        return code != 1

    @property
    def extra_state_attributes(self) -> dict[str, object | None]:
        raw = state_value(self.hass, self._source)
        code, text = split_bsb_status(raw)
        return {
            "code_bsb": code,
            "etat_bsb": text,
            "etat_neutre_valide": 1,
            "parametre_bsb": 701 if self._circuit == 1 else 1001,
        }

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(track_entities(self.hass, [self._source], self.async_write_ha_state))


class AlfeaBinaryProxy(BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
        device_class: BinarySensorDeviceClass | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        self.hass = hass
        self._source = entry.data[key]
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_entity_category = entity_category
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def is_on(self) -> bool | None:
        return state_is_on(self.hass, self._source)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(track_entities(self.hass, [self._source], self.async_write_ha_state))


@dataclass(frozen=True)
class AlertDescription:
    key: str
    name: str
    icon: str
    value_fn: Callable[[AlfeaRuntimeMonitor], bool | None]
    attributes_fn: Callable[[AlfeaRuntimeMonitor], dict[str, Any]]
    entity_category: EntityCategory | None = EntityCategory.DIAGNOSTIC


ALERT_DESCRIPTIONS = (
    AlertDescription(
        "short_cycle_problem",
        "Alarme — Compresseur — Cycles courts répétés",
        "mdi:timer-alert-outline",
        lambda monitor: monitor.short_cycle_problem,
        lambda monitor: {
            "seuil_cycle_minutes": monitor.short_cycle_threshold,
            "source_seuil": monitor.short_cycle_threshold_source,
            "dernier_cycle_minutes": monitor.last_cycle_duration_minutes,
            "dernier_cycle_court": monitor.last_cycle_was_short,
            "cycles_courts_derniere_heure": monitor.short_cycles_last_hour,
            "cycles_courts_6_heures": monitor.short_cycles_last_six_hours,
            "regle_alerte": "2 en 1 h ou 3 en 6 h",
            "phase_apprentissage": not monitor.cycle_learning_complete,
        },
    ),
    AlertDescription(
        "restart_too_soon_problem",
        "Alarme — Compresseur — Redémarrages trop rapprochés",
        "mdi:timer-refresh-outline",
        lambda monitor: monitor.restart_too_soon_problem,
        lambda monitor: {
            "temps_arret_minimum_minutes": monitor.configured_min_off_minutes,
            "dernier_arret_minutes": monitor.last_off_duration_minutes,
            "dernier_redemarrage_trop_rapproche": monitor.last_restart_was_too_soon,
            "redemarrages_rapproches_derniere_heure": monitor.early_restarts_last_hour,
            "redemarrages_rapproches_6_heures": monitor.early_restarts_last_six_hours,
            "regle_alerte": "2 en 1 h ou 3 en 6 h",
            "phase_apprentissage": monitor.last_off_duration_minutes is None,
        },
    ),
    AlertDescription(
        "frequent_starts_problem",
        "Alarme — Compresseur — Démarrages fréquents",
        "mdi:restart-alert",
        lambda monitor: monitor.frequent_starts_problem,
        lambda monitor: {
            "seuil_par_heure": monitor.frequent_starts_threshold,
            "demarrages_derniere_heure": monitor.starts_last_hour,
            "fenetre_complete": monitor.starts_window_complete,
            "phase_apprentissage": not monitor.starts_window_complete,
        },
    ),
    AlertDescription(
        "flow_gap_problem",
        "Alarme — PAC — Écart de température anormal",
        "mdi:thermometer-alert",
        lambda monitor: monitor.flow_gap_problem,
        lambda monitor: {
            "seuil_ecart_degC": monitor.flow_gap_threshold,
            "temporisation_minutes": monitor.flow_gap_duration,
            "ecart_actuel_degC": monitor.flow_gap,
            "ecs_en_charge": monitor.dhw_charging,
            "surveillance_suspendue_ecs": monitor.dhw_charging is True,
        },
    ),
    AlertDescription(
        "compressor_alert",
        "Alarme — Compresseur — Synthèse",
        "mdi:engine-off-outline",
        lambda monitor: monitor.compressor_alert,
        lambda monitor: {
            "cycles_courts_repetes": monitor.short_cycle_problem,
            "redemarrage_trop_rapproche": monitor.restart_too_soon_problem,
            "demarrages_frequents": monitor.frequent_starts_problem,
            "ecart_temperature": monitor.flow_gap_problem is True,
            "supervision_complete": monitor.supervision_complete,
            "phase_apprentissage": not monitor.supervision_complete,
        },
        EntityCategory.DIAGNOSTIC,
    ),
)


class AlfeaAlertBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        entry: ConfigEntry,
        monitor: AlfeaRuntimeMonitor,
        description: AlertDescription,
    ) -> None:
        self._monitor = monitor
        self._description = description
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def is_on(self) -> bool:
        # Learning or unavailable source data must never be shown as a fault.
        return self._description.value_fn(self._monitor) is True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._description.attributes_fn(self._monitor)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._monitor.async_add_listener(self.async_write_ha_state))



class AlfeaClockDesyncBinarySensor(BinarySensorEntity):
    """Report a significant difference between PAC and Home Assistant clocks."""

    _attr_has_entity_name = True
    _attr_name = "Alarme — Horloge PAC désynchronisée"
    _attr_icon = "mdi:clock-alert-outline"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_pac_clock_desynchronized"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def is_on(self) -> bool | None:
        # A stale BSB sample cannot prove that the PAC clock is wrong. Keep the
        # diagnostic unknown rather than raising a false alarm.
        if not clock_source_is_fresh(self.hass, self._entry):
            return None
        offset = clock_offset_seconds(self.hass, self._entry)
        if offset is None:
            return None
        return abs(offset) > CLOCK_DESYNC_THRESHOLD_SECONDS

    @property
    def extra_state_attributes(self) -> dict[str, int | bool] | None:
        offset = clock_offset_seconds(self.hass, self._entry)
        if offset is None:
            return None
        return {
            "decalage_secondes": offset,
            "seuil_secondes": CLOCK_DESYNC_THRESHOLD_SECONDS,
            "lecture_bsb_recente": clock_source_is_fresh(self.hass, self._entry),
        }

    @callback
    def _handle_clock_interval(self, _now) -> None:
        """Refresh the clock diagnostic from the Home Assistant event loop."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            track_entities(
                self.hass,
                list(clock_source_ids(self.hass, self._entry)),
                self.async_write_ha_state,
            )
        )
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._handle_clock_interval,
                timedelta(minutes=5),
            )
        )
