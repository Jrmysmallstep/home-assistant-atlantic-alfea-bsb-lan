"""Runtime monitoring and diagnostic calculations."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COMPRESSOR_MIN_OFF,
    CONF_COMPRESSOR_MIN_RUN,
    CONF_COMPRESSOR_STARTS,
    CONF_FLOW_GAP_DEGREES,
    CONF_FLOW_GAP_DURATION_MINUTES,
    CONF_FREQUENT_STARTS_PER_HOUR,
    CONF_SHORT_CYCLE_MINUTES,
    DEFAULT_FLOW_GAP_DEGREES,
    DEFAULT_FLOW_GAP_DURATION_MINUTES,
    DEFAULT_FREQUENT_STARTS_PER_HOUR,
    DEFAULT_SHORT_CYCLE_MINUTES,
    DOMAIN,
    SHORT_CYCLES_PER_HOUR,
    SHORT_CYCLES_PER_SIX_HOURS,
)
from .helpers import (
    dhw_charge_requested,
    generator_is_cooling,
    source_entity,
    state_float,
    state_is_on,
    state_value,
)

_STORAGE_VERSION = 2
_UPDATE_INTERVAL = timedelta(seconds=30)
_START_WINDOW = timedelta(hours=1)
_SHORT_WINDOW_LONG = timedelta(hours=6)


class AlfeaRuntimeMonitor:
    """Track compressor cycles and calculate objective health indicators."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._listeners: set[Callable[[], None]] = set()
        self._unsubs: list[Callable[[], None]] = []
        self._store = Store[dict[str, Any]](
            hass,
            _STORAGE_VERSION,
            f"{DOMAIN}.{entry.entry_id}.monitor",
        )

        self.compressor_on: bool | None = None
        self.defrost_on: bool | None = None
        self.dhw_charging: bool | None = None
        self.current_cycle_start: datetime | None = None
        self.last_cycle_duration_minutes: float | None = None
        self.last_cycle_was_short: bool | None = None
        self.short_cycle_problem = False
        self.short_cycles_last_hour = 0
        self.short_cycles_last_six_hours = 0
        self.last_stop_time: datetime | None = None
        self.last_off_duration_minutes: float | None = None
        self.last_restart_was_too_soon: bool | None = None
        self.restart_too_soon_problem = False
        self.early_restarts_last_hour = 0
        self.early_restarts_last_six_hours = 0
        self.starts_today = 0
        self.starts_today_date = dt_util.now().date().isoformat()
        self.starts_last_hour = 0
        self.frequent_starts_problem = False
        self.flow_gap: float | None = None
        self.flow_gap_started: datetime | None = None
        self.flow_gap_problem: bool | None = None

        self._last_known_compressor: bool | None = None
        self._last_starts_counter: int | None = None
        self._start_events: deque[datetime] = deque()
        self._short_cycle_events: deque[datetime] = deque()
        self._early_restart_events: deque[datetime] = deque()
        self._runtime_started_at = dt_util.now()

    @property
    def configured_min_run_minutes(self) -> float | None:
        """Return the minimum run time configured in BSB parameter 2842."""
        value = state_float(
            self.hass,
            source_entity(self.hass, self.entry, CONF_COMPRESSOR_MIN_RUN, 2842),
        )
        return value if value is not None and value > 0 else None

    @property
    def configured_min_off_minutes(self) -> float | None:
        """Return the minimum off time configured in BSB parameter 2843."""
        value = state_float(
            self.hass,
            source_entity(self.hass, self.entry, CONF_COMPRESSOR_MIN_OFF, 2843),
        )
        return value if value is not None and value > 0 else None

    @property
    def short_cycle_threshold(self) -> float:
        """Use BSB 2842 first, then the integration fallback option."""
        configured = self.configured_min_run_minutes
        if configured is not None:
            return configured
        return float(
            self.entry.options.get(
                CONF_SHORT_CYCLE_MINUTES,
                DEFAULT_SHORT_CYCLE_MINUTES,
            )
        )

    @property
    def short_cycle_threshold_source(self) -> str:
        """Explain where the active short-cycle threshold comes from."""
        return "BSB 2842" if self.configured_min_run_minutes is not None else "Option de secours"

    @property
    def frequent_starts_threshold(self) -> int:
        return int(
            self.entry.options.get(
                CONF_FREQUENT_STARTS_PER_HOUR,
                DEFAULT_FREQUENT_STARTS_PER_HOUR,
            )
        )

    @property
    def flow_gap_threshold(self) -> float:
        return float(self.entry.options.get(CONF_FLOW_GAP_DEGREES, DEFAULT_FLOW_GAP_DEGREES))

    @property
    def flow_gap_duration(self) -> float:
        return float(
            self.entry.options.get(
                CONF_FLOW_GAP_DURATION_MINUTES,
                DEFAULT_FLOW_GAP_DURATION_MINUTES,
            )
        )

    @property
    def starts_window_complete(self) -> bool:
        """Return true after a full one-hour observation window."""
        return dt_util.now() - self._runtime_started_at >= _START_WINDOW

    @property
    def cycle_learning_complete(self) -> bool:
        """Return true after at least one complete compressor cycle is known."""
        return self.last_cycle_duration_minutes is not None

    @property
    def supervision_complete(self) -> bool:
        """Return true when both cycle and hourly-start learning are complete."""
        return self.cycle_learning_complete and self.starts_window_complete

    @property
    def compressor_alert(self) -> bool:
        """Aggregate only confirmed problems, never missing learning data."""
        return any(
            (
                self.short_cycle_problem,
                self.frequent_starts_problem,
                self.flow_gap_problem is True,
                self.restart_too_soon_problem,
            )
        )

    @property
    def average_cycle_duration_minutes(self) -> float | None:
        hours = state_float(
            self.hass,
            source_entity(self.hass, self.entry, "compressor_hours", 8450),
        )
        starts = state_float(
            self.hass,
            source_entity(self.hass, self.entry, "compressor_starts", 8451),
        )
        if hours is None or starts is None or starts <= 0:
            return None
        return round((hours * 60.0) / starts, 1)

    async def async_start(self) -> None:
        """Load state and start tracking BSB-LAN entities."""
        stored = await self._store.async_load() or {}
        self._restore(stored)
        self._runtime_started_at = dt_util.now()

        tracked = [
            source_entity(self.hass, self.entry, "compressor_state", 8400),
            source_entity(self.hass, self.entry, CONF_COMPRESSOR_STARTS, 8451),
            source_entity(self.hass, self.entry, "flow_temp", 8412),
            source_entity(self.hass, self.entry, "target_flow_temp", 8411),
            source_entity(self.hass, self.entry, "dhw_state", 8003),
            source_entity(self.hass, self.entry, "dhw_pump", 8820),
            source_entity(self.hass, self.entry, "dhw_electric_heater", 8821),
            source_entity(self.hass, self.entry, "pac_state", 8006),
            source_entity(self.hass, self.entry, CONF_COMPRESSOR_MIN_RUN, 2842),
            source_entity(self.hass, self.entry, CONF_COMPRESSOR_MIN_OFF, 2843),
        ]
        entity_ids = sorted({entity_id for entity_id in tracked if entity_id})
        if entity_ids:
            self._unsubs.append(
                async_track_state_change_event(self.hass, entity_ids, self._handle_state_event)
            )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._handle_time, _UPDATE_INTERVAL)
        )
        await self.async_update(initial=True)

    async def async_stop(self) -> None:
        """Stop tracking and persist the current runtime state."""
        while self._unsubs:
            self._unsubs.pop()()
        await self._store.async_save(self._serialize())

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register an entity update listener."""
        self._listeners.add(listener)

        @callback
        def _remove() -> None:
            self._listeners.discard(listener)

        return _remove

    @callback
    def _notify(self) -> None:
        for listener in tuple(self._listeners):
            listener()

    @callback
    def _handle_state_event(self, _event: Any) -> None:
        self.hass.async_create_task(self.async_update())

    @callback
    def _handle_time(self, _now: datetime) -> None:
        self.hass.async_create_task(self.async_update())

    async def async_update(self, *, initial: bool = False) -> None:
        """Refresh calculated values from current Home Assistant states."""
        now = dt_util.now()
        self._reset_daily_if_needed(now)

        compressor = state_is_on(
            self.hass,
            source_entity(self.hass, self.entry, "compressor_state", 8400),
        )
        # BSB 7728 is the diagnostic input “Dégivrage DI6”, not a reliable
        # indication that a complete defrost cycle is currently running.
        defrost = None
        self.dhw_charging = self._is_dhw_charging()

        previous_known = self._last_known_compressor
        self.compressor_on = compressor
        self.defrost_on = defrost

        if compressor is True:
            if previous_known is not True:
                self._handle_compressor_start(now, initial=initial)
            self._last_known_compressor = True
        elif compressor is False:
            if previous_known is True:
                self._handle_compressor_stop(now)
            elif previous_known is None:
                # The compressor was already stopped when monitoring began; an
                # old in-progress cycle cannot be closed accurately.
                self.current_cycle_start = None
            self._last_known_compressor = False
        # A transient unknown/unavailable state does not terminate a running cycle.

        self._update_start_counters(now, initial=initial)
        self._update_flow_gap(now)
        self._purge_events(now)
        self._update_short_cycle_problem()
        self._update_early_restart_problem()

        self.starts_last_hour = len(self._start_events)
        self.frequent_starts_problem = (
            self.starts_window_complete
            and self.starts_last_hour >= self.frequent_starts_threshold
        )

        self._store.async_delay_save(self._serialize, 5)
        self._notify()

    def _handle_compressor_start(self, now: datetime, *, initial: bool) -> None:
        """Record a real compressor start from the observed BSB 8400 transition."""
        if self.current_cycle_start is None:
            self.current_cycle_start = now

        # The live start counters must be based on the actual 8400 OFF -> ON
        # transition. The native 8451 counter can be published much later and
        # therefore cannot locate starts accurately inside one-hour windows.
        if not initial:
            self.starts_today += 1
            self._start_events.append(now)

        if initial or self.last_stop_time is None:
            return

        duration = max(0.0, (now - self.last_stop_time).total_seconds() / 60.0)
        self.last_off_duration_minutes = round(duration, 1)
        minimum = self.configured_min_off_minutes
        self.last_restart_was_too_soon = minimum is not None and duration < minimum
        if self.last_restart_was_too_soon:
            self._early_restart_events.append(now)

    def _handle_compressor_stop(self, now: datetime) -> None:
        """Close a complete observed cycle and classify it."""
        if self.current_cycle_start is not None:
            duration = max(0.0, (now - self.current_cycle_start).total_seconds() / 60.0)
            self.last_cycle_duration_minutes = round(duration, 1)
            self.last_cycle_was_short = duration < self.short_cycle_threshold
            if self.last_cycle_was_short:
                self._short_cycle_events.append(now)
        self.current_cycle_start = None
        self.last_stop_time = now

    def _update_start_counters(self, now: datetime, *, initial: bool) -> None:
        raw_counter = state_float(
            self.hass,
            source_entity(self.hass, self.entry, CONF_COMPRESSOR_STARTS, 8451),
        )
        if raw_counter is None:
            return
        counter = int(raw_counter)
        if self._last_starts_counter is None:
            self._last_starts_counter = counter
            return

        if counter < self._last_starts_counter:
            self._last_starts_counter = counter
            return

        # Keep the native counter baseline for diagnostics only. A delayed MQTT
        # publication can jump by many starts at once, so using its delta would
        # incorrectly place all those starts at the current timestamp.
        self._last_starts_counter = counter

    def _update_flow_gap(self, now: datetime) -> None:
        flow = state_float(self.hass, source_entity(self.hass, self.entry, "flow_temp", 8412))
        target = state_float(
            self.hass,
            source_entity(self.hass, self.entry, "target_flow_temp", 8411),
        )
        if flow is None or target is None:
            self.flow_gap = None
            self.flow_gap_started = None
            self.flow_gap_problem = None
            return

        self.flow_gap = round(abs(flow - target), 1)
        condition = (
            self.compressor_on is True
            and self.defrost_on is not True
            and self.dhw_charging is not True
            and self.flow_gap >= self.flow_gap_threshold
        )
        if not condition:
            self.flow_gap_started = None
            self.flow_gap_problem = False
            return

        if self.flow_gap_started is None:
            self.flow_gap_started = now
        elapsed = (now - self.flow_gap_started).total_seconds() / 60.0
        self.flow_gap_problem = elapsed >= self.flow_gap_duration

    def _is_dhw_charging(self) -> bool | None:
        """Detect a genuine DHW charge request from BSB parameter 8003."""
        value = state_value(
            self.hass,
            source_entity(self.hass, self.entry, "dhw_state", 8003),
        )
        return dhw_charge_requested(value)

    @property
    def dhw_production_state(self) -> str:
        """Return the best proven instantaneous DHW production state.

        Parameter 8003 is a logical ECS demand/state and can remain at
        ``Charge...`` while the compressor is actually serving space cooling.
        The 11-Aug-2026 bus captures showed that a genuine PAC DHW charge is
        characterised by the physical ECS pump 8820 being ON together with the
        compressor. 8821 independently proves electric backup operation.

        Using the physical outputs first also removes the brief false
        ``Chauffe par PAC`` state caused by sequential MQTT updates at a
        transition.
        """
        pump = state_is_on(
            self.hass,
            source_entity(self.hass, self.entry, "dhw_pump", 8820),
        )
        electric = state_is_on(
            self.hass,
            source_entity(self.hass, self.entry, "dhw_electric_heater", 8821),
        )
        pac_state = state_value(
            self.hass,
            source_entity(self.hass, self.entry, "pac_state", 8006),
        )
        generator_cooling = generator_is_cooling(pac_state)

        # Physical outputs are stronger evidence than the logical 8003 label.
        pac_heating_dhw = (
            pump is True
            and self.compressor_on is True
            and generator_cooling is not True
        )
        if pac_heating_dhw and electric is True:
            return "PAC + appoint électrique"
        if electric is True:
            return "Appoint électrique"
        if pac_heating_dhw:
            return "Chauffe par PAC"

        # 8003 can legitimately ask for ECS while the generator is unavailable
        # or finishing another duty. Without 8820/8821 there is no proof of
        # actual ECS heat production.
        if self.dhw_charging is True:
            return "Demande / attente"
        return "Inactive"

    def _update_short_cycle_problem(self) -> None:
        self.short_cycles_last_hour = sum(
            event >= dt_util.now() - _START_WINDOW for event in self._short_cycle_events
        )
        self.short_cycles_last_six_hours = len(self._short_cycle_events)
        self.short_cycle_problem = (
            self.short_cycles_last_hour >= SHORT_CYCLES_PER_HOUR
            or self.short_cycles_last_six_hours >= SHORT_CYCLES_PER_SIX_HOURS
        )

    def _update_early_restart_problem(self) -> None:
        now = dt_util.now()
        self.early_restarts_last_hour = sum(
            event >= now - _START_WINDOW for event in self._early_restart_events
        )
        self.early_restarts_last_six_hours = len(self._early_restart_events)
        self.restart_too_soon_problem = (
            self.early_restarts_last_hour >= SHORT_CYCLES_PER_HOUR
            or self.early_restarts_last_six_hours >= SHORT_CYCLES_PER_SIX_HOURS
        )

    def _reset_daily_if_needed(self, now: datetime) -> None:
        today = now.date().isoformat()
        if today != self.starts_today_date:
            self.starts_today_date = today
            self.starts_today = 0

    def _purge_events(self, now: datetime) -> None:
        starts_cutoff = now - _START_WINDOW
        while self._start_events and self._start_events[0] < starts_cutoff:
            self._start_events.popleft()

        short_cutoff = now - _SHORT_WINDOW_LONG
        while self._short_cycle_events and self._short_cycle_events[0] < short_cutoff:
            self._short_cycle_events.popleft()
        while self._early_restart_events and self._early_restart_events[0] < short_cutoff:
            self._early_restart_events.popleft()

    def _restore(self, stored: dict[str, Any]) -> None:
        self.last_cycle_duration_minutes = _as_float(stored.get("last_cycle_duration_minutes"))
        self.last_cycle_was_short = _as_bool_or_none(stored.get("last_cycle_was_short"))
        self.last_off_duration_minutes = _as_float(stored.get("last_off_duration_minutes"))
        self.last_restart_was_too_soon = _as_bool_or_none(stored.get("last_restart_was_too_soon"))
        self.restart_too_soon_problem = bool(stored.get("restart_too_soon_problem", False))
        self.starts_today = int(stored.get("starts_today", 0) or 0)
        self.starts_today_date = str(
            stored.get("starts_today_date") or dt_util.now().date().isoformat()
        )
        self._last_starts_counter = _as_int_or_none(stored.get("last_starts_counter"))
        self.current_cycle_start = _parse_datetime(stored.get("current_cycle_start"))
        self.last_stop_time = _parse_datetime(stored.get("last_stop_time"))
        self.flow_gap_started = _parse_datetime(stored.get("flow_gap_started"))
        self.flow_gap_problem = _as_bool_or_none(stored.get("flow_gap_problem"))
        for value in stored.get("start_events", []):
            parsed = _parse_datetime(value)
            if parsed is not None:
                self._start_events.append(parsed)
        for value in stored.get("short_cycle_events", []):
            parsed = _parse_datetime(value)
            if parsed is not None:
                self._short_cycle_events.append(parsed)
        for value in stored.get("early_restart_events", []):
            parsed = _parse_datetime(value)
            if parsed is not None:
                self._early_restart_events.append(parsed)
        self._purge_events(dt_util.now())

    def _serialize(self) -> dict[str, Any]:
        return {
            "last_cycle_duration_minutes": self.last_cycle_duration_minutes,
            "last_cycle_was_short": self.last_cycle_was_short,
            "last_off_duration_minutes": self.last_off_duration_minutes,
            "last_restart_was_too_soon": self.last_restart_was_too_soon,
            "restart_too_soon_problem": self.restart_too_soon_problem,
            "starts_today": self.starts_today,
            "starts_today_date": self.starts_today_date,
            "last_starts_counter": self._last_starts_counter,
            "current_cycle_start": _iso(self.current_cycle_start),
            "last_stop_time": _iso(self.last_stop_time),
            "flow_gap_started": _iso(self.flow_gap_started),
            "flow_gap_problem": self.flow_gap_problem,
            "start_events": [_iso(value) for value in self._start_events],
            "short_cycle_events": [_iso(value) for value in self._short_cycle_events],
            "early_restart_events": [_iso(value) for value in self._early_restart_events],
        }


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return parsed


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _as_int_or_none(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _as_bool_or_none(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None
