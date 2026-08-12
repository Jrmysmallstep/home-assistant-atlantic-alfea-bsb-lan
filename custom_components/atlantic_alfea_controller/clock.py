"""Clock helpers for Atlantic Alfea BSB-LAN."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
import re

from homeassistant.components.mqtt import async_publish
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    CLOCK_INITIAL_POLL_DELAY_SECONDS,
    CLOCK_POLL_INTERVAL_SECONDS,
    CLOCK_POLL_TOPIC,
    CLOCK_SOURCE_STALE_SECONDS,
    CONF_CLOCK_DATETIME,
)
from .discovery import discover_candidates
from .helpers import state_value
from .parameters import SPEC_BY_PARAMETER

# BSB-LAN writes parameter 0 as DD.MM.YYYY_HH:MM:SS.  The parser also
# accepts a space or T separator and common date separators, because the
# MQTT state presentation may vary slightly with language/firmware versions.
_DATETIME_RE = re.compile(
    r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})"
    r"\s*[_T ]\s*(\d{1,2})\s*[:.]\s*(\d{1,2})"
    r"(?:\s*[:.]\s*(\d{1,2}))?(?!\d)"
)
_WRITABLE_DOMAINS = {"text"}
_LOGGER = logging.getLogger(__name__)


def _clock_candidate_ids(hass: HomeAssistant, entry: ConfigEntry) -> list[str]:
    """Return every plausible BSB-LAN source for parameter 0.

    BSB-LAN commonly exposes parameter 0 as a ``text`` entity.  A config
    entry can however keep an older entity id after MQTT discovery has been
    rebuilt.  Track both the configured id and freshly discovered candidates
    so the clock can move to the live source without requiring a reconfigure.
    """
    candidates: list[str] = []
    configured = entry.data.get(CONF_CLOCK_DATETIME)
    if configured and hass.states.get(configured) is not None:
        candidates.append(configured)

    spec = SPEC_BY_PARAMETER.get(0)
    if spec is not None:
        for entity_id in discover_candidates(hass, spec):
            if entity_id not in candidates:
                candidates.append(entity_id)
    return candidates


def clock_source_id(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    """Return the freshest valid BSB-LAN source entity for parameter 0.

    Prefer a valid ``text`` source because it is also writable for clock
    synchronization.  Within the same domain, prefer the entity whose state
    was updated most recently.  This avoids staying attached to a stale MQTT
    entity after BSB-LAN discovery has created a replacement.
    """
    timezone = dt_util.get_time_zone(hass.config.time_zone) or dt_util.UTC
    ranked: list[tuple[int, float, str]] = []

    for entity_id in _clock_candidate_ids(hass, entry):
        source_state = hass.states.get(entity_id)
        if source_state is None:
            continue
        if _parse_datetime(state_value(hass, entity_id), timezone) is None:
            continue
        domain = entity_id.split(".", 1)[0]
        domain_rank = 2 if domain == "text" else 1
        updated = source_state.last_updated.timestamp()
        ranked.append((domain_rank, updated, entity_id))

    if not ranked:
        return None
    ranked.sort(reverse=True)
    return ranked[0][2]


def clock_source_ids(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> tuple[str | None, ...]:
    """Return all plausible clock sources for entity tracking helpers."""
    candidates = tuple(_clock_candidate_ids(hass, entry))
    return candidates if candidates else (None,)


def _parse_datetime(value: str | None, timezone) -> datetime | None:
    """Parse the full BSB parameter 0 date/time."""
    if value is None:
        return None
    match = _DATETIME_RE.search(value)
    if match is None:
        return None

    day, month, year, hour, minute, second = (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        int(match.group(4)),
        int(match.group(5)),
        int(match.group(6) or 0),
    )
    if year < 2000 or year > 2199 or hour > 23 or minute > 59 or second > 59:
        return None
    try:
        return datetime(year, month, day, hour, minute, second, tzinfo=timezone)
    except ValueError:
        return None


def _clock_sample(hass: HomeAssistant, entry: ConfigEntry) -> tuple[datetime, int, float] | None:
    """Return parsed PAC time, measured offset and source age.

    The offset is measured at the instant Home Assistant received the BSB state.
    Keeping that offset fixed prevents a stale MQTT sample from creating a
    fictitious clock drift that grows every second.
    """
    entity_id = clock_source_id(hass, entry)
    if entity_id is None:
        return None
    source_state = hass.states.get(entity_id)
    if source_state is None:
        return None

    timezone = dt_util.get_time_zone(hass.config.time_zone) or dt_util.UTC
    parsed = _parse_datetime(state_value(hass, entity_id), timezone)
    if parsed is None:
        return None

    received_local = source_state.last_updated.astimezone(timezone).replace(microsecond=0)
    measured_offset = round((parsed - received_local).total_seconds())
    age = max(0.0, (dt_util.utcnow() - source_state.last_updated).total_seconds())
    return parsed, measured_offset, age


def pac_clock_datetime(hass: HomeAssistant, entry: ConfigEntry) -> datetime | None:
    """Return the last date/time actually read from BSB parameter 0.

    The value deliberately stays fixed until the next real BSB poll. This keeps
    the Home Assistant history clean and prevents a synthetic 30-second clock
    from being recorded as if it came from the regulator.
    """
    sample = _clock_sample(hass, entry)
    return None if sample is None else sample[0]


def clock_offset_seconds(hass: HomeAssistant, entry: ConfigEntry) -> int | None:
    """Return the stable PAC-minus-Home-Assistant offset measured at reception."""
    sample = _clock_sample(hass, entry)
    return None if sample is None else sample[1]


def clock_source_age_seconds(hass: HomeAssistant, entry: ConfigEntry) -> int | None:
    """Return age in seconds of the last BSB parameter 0 publication."""
    sample = _clock_sample(hass, entry)
    return None if sample is None else round(sample[2])


def clock_source_is_fresh(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Return whether the BSB clock sample is recent enough for an alarm."""
    age = clock_source_age_seconds(hass, entry)
    return age is not None and age <= CLOCK_SOURCE_STALE_SECONDS


def clock_is_writable(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Return whether BSB parameter 0 can be written."""
    entity_id = clock_source_id(hass, entry)
    return bool(
        entity_id
        and entity_id.split(".", 1)[0] in _WRITABLE_DOMAINS
    )


async def _async_set_value(
    hass: HomeAssistant,
    entity_id: str,
    value: str,
) -> None:
    """Write the full date/time to a BSB-LAN text entity."""
    domain = entity_id.split(".", 1)[0]
    if domain != "text":
        raise HomeAssistantError(
            f"L’entité {entity_id} n’est pas accessible en écriture. "
            "Une entité BSB-LAN de domaine text pour le paramètre 0 est nécessaire."
        )
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": entity_id, "value": value},
        blocking=True,
    )


async def async_sync_pac_clock(
    hass: HomeAssistant,
    entry: ConfigEntry,
    value: datetime | None = None,
) -> datetime:
    """Set the PAC clock from Home Assistant local time using BSB parameter 0."""
    current = (value or dt_util.now()).replace(microsecond=0)
    clock_entity = clock_source_id(hass, entry)
    if clock_entity is None:
        raise HomeAssistantError(
            "Le paramètre BSB 0 doit être associé avant la synchronisation."
        )

    # Official BSB-LAN format used by set(0, ...): DD.MM.YYYY_HH:MM:SS.
    formatted = (
        f"{current.day:02d}.{current.month:02d}.{current.year:04d}_"
        f"{current.hour:02d}:{current.minute:02d}:{current.second:02d}"
    )
    await _async_set_value(hass, clock_entity, formatted)
    return current


async def async_poll_pac_clock(hass: HomeAssistant) -> bool:
    """Request a fresh read of BSB parameter 0 through MQTT.

    BSB-LAN only refreshes the Home Assistant text entity when parameter 0 is
    explicitly polled (or otherwise included in its own periodic publication).
    Polling once per hour is sufficient here: the purpose is to detect a PAC
    clock lost after a power cut, not to use MQTT as a real-time clock source.
    """
    try:
        await async_publish(
            hass,
            CLOCK_POLL_TOPIC,
            "0",
            qos=0,
            retain=False,
        )
    except Exception:  # Home Assistant service errors must not break the integration.
        _LOGGER.exception("Impossible de demander le poll BSB-LAN du paramètre 0")
        return False
    return True


def async_start_clock_polling(hass: HomeAssistant) -> Callable[[], None]:
    """Start one initial clock poll and then poll BSB parameter 0 hourly."""

    @callback
    def _request_poll(_now) -> None:
        hass.async_create_task(async_poll_pac_clock(hass))

    unsubs: list[Callable[[], None]] = [
        async_call_later(hass, CLOCK_INITIAL_POLL_DELAY_SECONDS, _request_poll),
        async_track_time_interval(
            hass,
            _request_poll,
            timedelta(seconds=CLOCK_POLL_INTERVAL_SECONDS),
        ),
    ]

    @callback
    def _unsubscribe() -> None:
        for unsub in unsubs:
            unsub()

    return _unsubscribe
