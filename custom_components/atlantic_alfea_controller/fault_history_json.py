"""Read-only polling of the PAC's ten historical fault entries (6800-6819)."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
    """Decode ten date/code pairs; 65535 and --- indicate an empty slot.

    BSB 6800, 6802, ... hold DATETIME; 6801, 6803, ... hold fault ENUM.
    A malformed read raises rather than pretending the history is empty.
    """
    result = []
    for index in range(10):
        date_param, code_param = 6800 + 2 * index, 6801 + 2 * index
        date_item = data.get(str(date_param))
        code_item = data.get(str(code_param))
        if not isinstance(date_item, dict) or not isinstance(code_item, dict):
            raise ValueError(f"Entrée historique {index + 1} manquante")
        if str(date_item.get("error")) != "0" or str(code_item.get("error")) != "0":
            raise ValueError(f"Erreur lecture historique {index + 1}")
        if date_item.get("dataType_name") != "DATETIME" or code_item.get("dataType_name") != "ENUM":
            raise ValueError(f"Types inattendus pour entrée {index + 1}")
        date = str(date_item.get("value") or "").strip()
        code = str(code_item.get("value") or "").strip()
        description = str(code_item.get("desc") or "").strip()
        if date in ("", "---") and code == "65535" and description in ("", "---"):
            continue
        if date in ("", "---") or code in ("", "65535", "---"):
            raise ValueError(f"Entrée historique {index + 1} incohérente")
        result.append({
            "rang": str(index + 1),
            "date": date,
            "code": code,
            "description": "" if description == "---" else description,
        })
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

    @callback
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
