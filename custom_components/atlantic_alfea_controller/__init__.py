"""Atlantic Alfea BSB-LAN integration."""

from __future__ import annotations

from pathlib import Path
import asyncio
import logging

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.mqtt import async_subscribe
from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .ecs_heater_json import async_start_heater_polling
from .fault_history_json import async_start_fault_history
from .clock import async_start_clock_polling
from .const import DOMAIN, PLATFORMS
from .discovery import discover_mapping
from .runtime import AlfeaRuntimeMonitor
from .polling import async_start_data_polling
from .weekly_programs import WeeklyProgramImporter

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Expose the bundled read-only Lovelace card through Home Assistant HTTP.

    The integration ships its static asset in HACS.  This registers only a
    GET endpoint; it never modifies dashboards, resources, or PAC commands.
    """
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                "/alfea-synoptique/pac-synoptique-card.js",
                str(Path(__file__).resolve().parent / "www" / "pac-synoptique-card.js"),
                False,
            ),
            StaticPathConfig(
                "/alfea-synoptique/pac-programmes-card.js",
                str(Path(__file__).resolve().parent / "www" / "pac-programmes-card.js"),
                False,
            ),
        ]
    )
    return True


def _remove_obsolete_energy_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove annual/history snapshots that were previously exposed as live energy."""
    registry = er.async_get(hass)
    for key in ("energy_heating", "energy_dhw", "energy_cooling"):
        unique_id = f"{entry.entry_id}_{key}"
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id is not None:
            registry.async_remove(entity_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate earlier entries and enrich them through automatic discovery."""
    data = dict(entry.data)
    # V1.2 now uses the single full date/time parameter 0.
    for legacy_key in ("clock_time", "clock_day_month", "clock_year", "compressor_min_run_enforcement", "compressor_power", "energy_heating", "energy_dhw", "energy_cooling"):
        data.pop(legacy_key, None)
    discovered = discover_mapping(hass, data)
    data.update(discovered.mapping)

    _remove_obsolete_energy_entities(hass, entry)
    if entry.version < 14 or data != dict(entry.data) or entry.title != "Atlantic Alfea BSB-LAN":
        hass.config_entries.async_update_entry(
            entry,
            title="Atlantic Alfea BSB-LAN",
            data=data,
            version=14,
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Atlantic Alfea BSB-LAN from a config entry."""
    data = dict(entry.data)
    for legacy_key in ("clock_time", "clock_day_month", "clock_year", "compressor_min_run_enforcement", "compressor_power", "energy_heating", "energy_dhw", "energy_cooling"):
        data.pop(legacy_key, None)
    discovered = discover_mapping(hass, data)
    data.update(discovered.mapping)
    _remove_obsolete_energy_entities(hass, entry)
    if data != dict(entry.data) or entry.title != "Atlantic Alfea BSB-LAN":
        hass.config_entries.async_update_entry(
            entry,
            title="Atlantic Alfea BSB-LAN",
            data=data,
        )

    # Listen to BSB-LAN's read-only MQTT pump status messages, even if no HA
    # MQTT-discovery sensor exists for these newly logged parameters.
    feedback = hass.data.setdefault(DOMAIN, {}).setdefault("pump_feedback", {})
    feedback[entry.entry_id] = {}
    def _clear_pump_feedback() -> None:
        feedback.pop(entry.entry_id, None)

    entry.async_on_unload(_clear_pump_feedback)

    pump_handlers = []
    for circuit, parameter in ((1, 9031), (2, 8760)):
        def _handle_pump(message, *, _circuit=circuit):
            payload = message.payload
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8", errors="replace")
            payload = str(payload).strip().lower()
            if payload in ("1", "on", "true", "activé") or payload.startswith("1 -"):
                on = True
            elif payload in ("0", "off", "false", "désactivé") or payload.startswith("0 -"):
                on = False
            else:
                return
            # MQTT callbacks can run off the HA event-loop thread. Schedule
            # both the cache update and dispatcher signal onto the HA loop.
            @callback
            def _notify_on_loop() -> None:
                current = feedback.get(entry.entry_id)
                if current is None:
                    return  # Integration unloaded between callback and dispatch.
                current[_circuit] = on
                async_dispatcher_send(hass, f"{DOMAIN}_pump_feedback_{entry.entry_id}")

            hass.add_job(_notify_on_loop)

        pump_handlers.append((f"BSB-LAN/+/+/{parameter}/status", _handle_pump))

    # Q3 command (8820): like pump feedback, this can be published on MQTT
    # without creating a Home Assistant entity via MQTT discovery.
    v3v_feedback = hass.data.setdefault(DOMAIN, {}).setdefault("v3v_feedback", {})
    v3v_feedback[entry.entry_id] = None
    entry.async_on_unload(lambda: v3v_feedback.pop(entry.entry_id, None))

    def _handle_v3v(message) -> None:
        payload = message.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8", errors="replace")
        value = str(payload).strip().lower()
        if value in ("1", "on", "true", "activé") or value.startswith("1 -"):
            commanded_ecs = True
        elif value in ("0", "off", "false", "désactivé") or value.startswith("0 -"):
            commanded_ecs = False
        else:
            return

        @callback
        def _notify_on_loop() -> None:
            if entry.entry_id not in v3v_feedback:
                return
            v3v_feedback[entry.entry_id] = commanded_ecs
            async_dispatcher_send(hass, f"{DOMAIN}_v3v_feedback_{entry.entry_id}")

        hass.add_job(_notify_on_loop)

    # MQTT peut ne pas être prêt lors du démarrage de HA. L'abonnement
    # n'est pas une condition pour charger l'intégration ni les programmes.
    # Réessayer quand le composant MQTT termine son initialisation.
    mqtt_topics = [
        *pump_handlers,
        ("BSB-LAN/+/+/8820/status", _handle_v3v),
    ]
    mqtt_lock = asyncio.Lock()
    mqtt_subscribed = False
    mqtt_unsubscribers = []

    async def _subscribe_feedback() -> None:
        nonlocal mqtt_subscribed
        async with mqtt_lock:
            if mqtt_subscribed or "mqtt" not in hass.data:
                return
            subscriptions = []
            try:
                for topic, handler in mqtt_topics:
                    subscriptions.append(
                        await async_subscribe(hass, topic, handler, qos=0)
                    )
            except HomeAssistantError as err:
                for unsubscribe in subscriptions:
                    unsubscribe()
                _LOGGER.warning(
                    "Abonnements MQTT BSB-LAN reportés : %s", err
                )
                return
            mqtt_unsubscribers.extend(subscriptions)
            mqtt_subscribed = True

    def _mqtt_component_loaded(event) -> None:
        if event.data.get("component") == "mqtt":
            hass.async_create_task(_subscribe_feedback())

    unsubscribe_event = hass.bus.async_listen(
        EVENT_COMPONENT_LOADED, _mqtt_component_loaded
    )
    entry.async_on_unload(unsubscribe_event)

    def _clear_mqtt_subscriptions() -> None:
        for unsubscribe in mqtt_unsubscribers:
            unsubscribe()
        mqtt_unsubscribers.clear()

    entry.async_on_unload(_clear_mqtt_subscriptions)
    await _subscribe_feedback()

    # Import des programmes à la demande, indépendant des 40 publications MQTT.
    # Aucun appel HTTP au démarrage : seul le bouton explicite déclenche /JQ.
    programs = hass.data.setdefault(DOMAIN, {}).setdefault("weekly_programs", {})
    programs[entry.entry_id] = WeeklyProgramImporter(
        hass, entry.entry_id, entry.options.get("bsb_base_url", "")
    )
    entry.async_on_unload(lambda: programs.pop(entry.entry_id, None))

    monitor = AlfeaRuntimeMonitor(hass, entry)
    entry.runtime_data = monitor
    await monitor.async_start()
    entry.async_on_unload(async_start_clock_polling(hass))
    entry.async_on_unload(async_start_data_polling(hass))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(await async_start_heater_polling(hass, entry))
    entry.async_on_unload(await async_start_fault_history(hass, entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and isinstance(entry.runtime_data, AlfeaRuntimeMonitor):
        await entry.runtime_data.async_stop()
    return unloaded
