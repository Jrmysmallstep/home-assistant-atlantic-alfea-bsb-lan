"""Atlantic Alfea BSB-LAN integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.mqtt import async_subscribe
from homeassistant.helpers.dispatcher import async_dispatcher_send

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .clock import async_start_clock_polling
from .const import DOMAIN, PLATFORMS
from .discovery import discover_mapping
from .runtime import AlfeaRuntimeMonitor
from .polling import async_start_data_polling


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
            )
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
    entry.async_on_unload(lambda: feedback.pop(entry.entry_id, None))

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
            feedback[entry.entry_id][_circuit] = on
            async_dispatcher_send(hass, f"{DOMAIN}_pump_feedback_{entry.entry_id}")

        unsub = await async_subscribe(
            hass, f"BSB-LAN/+/+/{parameter}/status", _handle_pump, qos=0
        )
        entry.async_on_unload(unsub)

    monitor = AlfeaRuntimeMonitor(hass, entry)
    entry.runtime_data = monitor
    await monitor.async_start()
    entry.async_on_unload(async_start_clock_polling(hass))
    entry.async_on_unload(async_start_data_polling(hass))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and isinstance(entry.runtime_data, AlfeaRuntimeMonitor):
        await entry.runtime_data.async_stop()
    return unloaded
