"""Read-only polling of the PAC's ten historical fault entries (6800-6819)."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .regime_api import valid_base_url

_LOGGER = logging.getLogger(__name__)
_INTERVAL = timedelta(minutes=15)
_EMPTY = {"", "---", "--", "aucun", "aucun défaut", "pas de défaut", "no fault", "0"}


def parse_fault_history(data: dict[str, dict]) -> list[dict[str, str]]:
    """Preserve both raw fields per historical slot; never fabricate a fault code.

    The device-specific meaning of each odd/even field still needs verification.
    """
    result = []
    for index in range(10):
        first, second = 6800 + 2 * index, 6801 + 2 * index
        parts = []
        for parameter in (first, second):
            item = data.get(str(parameter))
            if not isinstance(item, dict) or str(item.get("error")) != "0":
                raise ValueError(f"Paramètre historique {parameter} non disponible")
            value = str(item.get("value") if item.get("value") is not None else "").strip()
            desc = str(item.get("desc") or "").strip()
            parts.append({"parametre": str(parameter), "valeur": value, "description": desc})
        if all(p["valeur"].lower() in _EMPTY and p["description"].lower() in _EMPTY for p in parts):
            continue
        result.append({"rang": str(index + 1), "parametres": f"{first}/{second}",
                       "premier": parts[0]["valeur"], "second": parts[1]["valeur"],
                       "description_premier": parts[0]["description"],
                       "description_second": parts[1]["description"]})
    return result


async def async_start_fault_history(hass: HomeAssistant, entry: ConfigEntry):
    """Start 15-minute snapshots; missing/failed reads never become 'no faults'."""
    url = str(entry.options.get("bsb_base_url", "")).strip()
    if not valid_base_url(url):
        return lambda: None
    base = url.rstrip("/")
    cache = hass.data.setdefault(DOMAIN, {}).setdefault("fault_history", {})
    cache[entry.entry_id] = {"status": "Indisponible", "entries": [], "updated": None}
    session = async_get_clientsession(hass)
    lock = asyncio.Lock()
    active = True

    async def refresh():
        if not active or lock.locked():
            return
        async with lock:
            try:
                values = {}
                for parameter in range(6800, 6820):
                    async with asyncio.timeout(8):
                        async with session.get(f"{base}/JQ={parameter}") as response:
                            response.raise_for_status()
                            payload = await response.json(content_type=None)
                    item = payload.get(str(parameter)) if isinstance(payload, dict) else None
                    if not isinstance(item, dict):
                        raise ValueError(f"Réponse invalide pour {parameter}")
                    values[str(parameter)] = item
                    await asyncio.sleep(0.2)
                entries = parse_fault_history(values)
                snapshot = {"status": "Chargé", "entries": entries,
                            "updated": dt_util.now().isoformat(timespec="seconds")}
            except Exception as err:
                _LOGGER.warning("Lecture historique défauts BSB-LAN impossible : %s", err)
                snapshot = {"status": "Indisponible", "entries": [], "updated": None}
            if active:
                cache[entry.entry_id] = snapshot
                async_dispatcher_send(hass, f"{DOMAIN}_fault_history_{entry.entry_id}")

    def tick(_now):
        hass.async_create_task(refresh())

    unsubscribe = async_track_time_interval(hass, tick, _INTERVAL)
    task = hass.async_create_task(refresh())

    def stop():
        nonlocal active
        active = False
        unsubscribe()
        task.cancel()
        cache.pop(entry.entry_id, None)

    return stop
