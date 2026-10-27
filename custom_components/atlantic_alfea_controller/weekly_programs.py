"""Read-only import of the PAC's native weekly TIMEPROG schedules.

BSB-LAN JSON /JQ queries do not consume any of the 40 MQTT log slots.
No schedule is ever written or simulated by Home Assistant.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .regime_api import valid_base_url

_LOGGER = logging.getLogger(__name__)
WEEKDAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
# Heating/ECS: Monday is the base, following days use .1 through .6.
# Cooling: custom BSB-LAN parameters 11000-11006 / 11010-11016 are consecutive.
PROGRAMS = {
    "chauffage_c1": ("Chauffage RDC", "mdi:calendar-clock", "501"),
    "chauffage_c2": ("Chauffage étage", "mdi:calendar-clock", "521"),
    "ecs": ("Eau chaude sanitaire", "mdi:calendar-clock", "561"),
    "rafraichissement_c1": ("Rafraîchissement RDC", "mdi:snowflake-clock", "11000"),
    "rafraichissement_c2": ("Rafraîchissement étage", "mdi:snowflake-clock", "11010"),
}
_SLOT_RE = re.compile(r"(\d{2}:\d{2}|##:##)-(\d{2}:\d{2}|##:##)")


def parse_timeprog(value: str) -> list[dict[str, str]]:
    """Parse exactly three TIMEPROG slots; ##:##-##:## means unused."""
    slots = str(value).strip().split()
    if len(slots) != 3:
        raise ValueError(f"Trois plages TIMEPROG attendues : {value!r}")
    result: list[dict[str, str]] = []
    previous_end = -1
    for slot in slots:
        match = _SLOT_RE.fullmatch(slot)
        if match is None:
            raise ValueError(f"Plage TIMEPROG invalide : {slot!r}")
        start, end = match.groups()
        if start == end == "##:##":
            continue
        if "##:##" in (start, end):
            raise ValueError(f"Plage TIMEPROG partiellement vide : {slot!r}")
        def minutes(clock: str, *, is_end: bool = False) -> int:
            hour, minute = (int(part) for part in clock.split(":"))
            if minute > 59 or hour > 24 or (hour == 24 and (minute != 0 or not is_end)):
                raise ValueError(f"Heure TIMEPROG invalide : {clock!r}")
            return hour * 60 + minute
        start_min = minutes(start)
        end_min = minutes(end, is_end=True)
        if start_min >= end_min or start_min < previous_end:
            raise ValueError(f"Plages TIMEPROG chevauchantes ou inversées : {value!r}")
        previous_end = end_min
        result.append({"debut": start, "fin": end})
    return result


def parameter_for_day(key: str, base: str, index: int) -> str:
    """Return the exact BSB-LAN JSON parameter for a weekday (Monday = 0)."""
    if not 0 <= index < len(WEEKDAYS):
        raise ValueError(f"Jour invalide : {index}")
    if key in ("rafraichissement_c1", "rafraichissement_c2"):
        return str(int(base) + index)
    return base if index == 0 else f"{base}.{index}"


@dataclass
class ProgramSnapshot:
    """Last successful import and the most recent refresh status."""
    status: str = "Non chargé"
    updated: str | None = None
    error: str | None = None
    days: dict[str, list[dict[str, str]]] | None = None


class WeeklyProgramImporter:
    """Import five validated schedules only when the user presses Refresh."""

    def __init__(self, hass: HomeAssistant, entry_id: str, base_url: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.base_url = base_url.strip().rstrip("/")
        self.snapshots = {key: ProgramSnapshot() for key in PROGRAMS}
        self._lock = asyncio.Lock()

    @property
    def configured(self) -> bool:
        return valid_base_url(self.base_url)

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, f"{DOMAIN}_weekly_programs_{self.entry_id}")

    async def _read_day(self, session, parameter: str) -> list[dict[str, str]]:
        async with asyncio.timeout(10):
            async with session.get(f"{self.base_url}/JQ={parameter}") as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        item = data.get(parameter) if isinstance(data, dict) else None
        if not isinstance(item, dict) or str(item.get("error")) != "0":
            raise ValueError(f"Réponse BSB-LAN invalide pour {parameter}: {item!r}")
        if item.get("dataType_name") not in (None, "TIMEPROG"):
            raise ValueError(f"Type inattendu pour {parameter}: {item.get('dataType_name')}")
        value = item.get("value")
        if not isinstance(value, str):
            raise ValueError(f"Plages horaires absentes pour {parameter}")
        return parse_timeprog(value)

    async def async_refresh_all(self) -> dict[str, str]:
        """Read 35 days sequentially; commit each weekly program atomically."""
        if not self.configured:
            raise ValueError("Configurer l'adresse BSB-LAN JSON dans les options.")
        errors: dict[str, str] = {}
        async with self._lock:
            session = async_get_clientsession(self.hass)
            for key, (_name, _icon, base) in PROGRAMS.items():
                snapshot = self.snapshots[key]
                days: dict[str, list[dict[str, str]]] = {}
                try:
                    for index, weekday in enumerate(WEEKDAYS):
                        parameter = parameter_for_day(key, base, index)
                        days[weekday] = await self._read_day(session, parameter)
                        # Avoid a burst of 35 consecutive requests on the BSB bus.
                        await asyncio.sleep(0.2)
                except (ValueError, asyncio.TimeoutError, OSError) as err:
                    snapshot.status = "Erreur"
                    snapshot.error = str(err)
                    errors[key] = str(err)
                    _LOGGER.warning("Import programme %s impossible : %s", key, err)
                except Exception as err:
                    # aiohttp client errors are surfaced to HA, not silently ignored.
                    snapshot.status = "Erreur"
                    snapshot.error = str(err)
                    errors[key] = str(err)
                    _LOGGER.warning("Import programme %s impossible : %s", key, err)
                else:
                    snapshot.days = days
                    snapshot.updated = dt_util.now().isoformat(timespec="seconds")
                    snapshot.status = "Chargé"
                    snapshot.error = None
                self._notify()
        return errors
