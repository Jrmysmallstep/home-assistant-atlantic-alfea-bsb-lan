"""Read-only, periodic ECS electric heater status via BSB-LAN JSON."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .regime_api import valid_base_url

_LOGGER = logging.getLogger(__name__)
_INTERVAL = timedelta(seconds=60)


def parse_heater_response(data: object) -> bool | None:
    """Accept only a successful 8821 ONOFF response with value 0 or 1."""
    item = data.get("8821") if isinstance(data, dict) else None
    if not isinstance(item, dict):
        return None
    if str(item.get("error")) != "0" or item.get("dataType_name") != "ONOFF":
        return None
    value = str(item.get("value", "")).strip()
    if value not in ("0", "1"):
        return None
    return value == "1"


def heater_state(hass: HomeAssistant, entry: ConfigEntry) -> bool | None:
    """Return JSON state when configured; otherwise use the existing HA source."""
    url = str(entry.options.get("bsb_base_url", "")).strip()
    if valid_base_url(url):
        return hass.data.get(DOMAIN, {}).get("ecs_heater_json", {}).get(entry.entry_id)
    from .helpers import source_entity, state_is_on
    return state_is_on(hass, source_entity(hass, entry, "dhw_electric_heater", 8821))


def json_enabled(entry: ConfigEntry) -> bool:
    return valid_base_url(str(entry.options.get("bsb_base_url", "")).strip())


async def async_start_heater_polling(hass: HomeAssistant, entry: ConfigEntry):
    """Start read-only polling; return an unload callback."""
    if not json_enabled(entry):
        return lambda: None

    url = str(entry.options["bsb_base_url"]).strip().rstrip("/")
    cache = hass.data.setdefault(DOMAIN, {}).setdefault("ecs_heater_json", {})
    cache[entry.entry_id] = None
    session = async_get_clientsession(hass)
    lock = asyncio.Lock()
    active = True

    async def refresh() -> None:
        if not active or lock.locked():
            return
        async with lock:
            value = None
            try:
                async with asyncio.timeout(8):
                    async with session.get(f"{url}/JQ=8821") as response:
                        response.raise_for_status()
                        data = await response.json(content_type=None)
                value = parse_heater_response(data)
            except Exception as err:
                _LOGGER.warning("Lecture JSON BSB-LAN 8821 impossible : %s", err)
            if not active:
                return
            cache[entry.entry_id] = value
            async_dispatcher_send(hass, f"{DOMAIN}_ecs_heater_{entry.entry_id}")
            monitor = entry.runtime_data
            if monitor is not None:
                await monitor.async_update()

    @callback
    def on_interval(_now) -> None:
        hass.async_create_task(refresh())

    unsubscribe = async_track_time_interval(hass, on_interval, _INTERVAL)
    first_task = hass.async_create_task(refresh())

    def stop() -> None:
        nonlocal active
        active = False
        unsubscribe()
        first_task.cancel()
        cache.pop(entry.entry_id, None)

    return stop
