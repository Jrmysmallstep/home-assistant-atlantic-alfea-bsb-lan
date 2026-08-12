"""Periodic read-only BSB-LAN refresh requests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import timedelta
import logging

from homeassistant.components.mqtt import async_publish
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import (
    BSB_REFRESH_FAST_INTERVAL_SECONDS,
    BSB_REFRESH_FAST_PARAMETERS,
    BSB_REFRESH_INITIAL_DELAY_SECONDS,
    BSB_REFRESH_SLOW_INTERVAL_SECONDS,
    BSB_REFRESH_SLOW_PARAMETERS,
    CLOCK_POLL_TOPIC,
)

_LOGGER = logging.getLogger(__name__)


async def async_poll_parameters(hass: HomeAssistant, parameters: tuple[int, ...]) -> None:
    """Ask BSB-LAN to republish selected read-only parameters through MQTT."""
    for parameter in parameters:
        try:
            await async_publish(
                hass,
                CLOCK_POLL_TOPIC,
                str(parameter),
                qos=0,
                retain=False,
            )
        except Exception:  # MQTT availability must never break the integration.
            _LOGGER.exception("Impossible de demander le poll BSB-LAN du paramètre %s", parameter)
        # Avoid sending a burst of bus requests at exactly the same instant.
        await asyncio.sleep(0.15)


def async_start_data_polling(hass: HomeAssistant) -> Callable[[], None]:
    """Refresh dynamic diagnostics/counters independently of BSB-LAN log lists."""

    @callback
    def _fast(_now) -> None:
        hass.async_create_task(async_poll_parameters(hass, BSB_REFRESH_FAST_PARAMETERS))

    @callback
    def _slow(_now) -> None:
        hass.async_create_task(async_poll_parameters(hass, BSB_REFRESH_SLOW_PARAMETERS))

    unsubs: list[Callable[[], None]] = [
        async_call_later(hass, BSB_REFRESH_INITIAL_DELAY_SECONDS, _fast),
        async_call_later(hass, BSB_REFRESH_INITIAL_DELAY_SECONDS + 10, _slow),
        async_track_time_interval(
            hass,
            _fast,
            timedelta(seconds=BSB_REFRESH_FAST_INTERVAL_SECONDS),
        ),
        async_track_time_interval(
            hass,
            _slow,
            timedelta(seconds=BSB_REFRESH_SLOW_INTERVAL_SECONDS),
        ),
    ]

    @callback
    def _unsubscribe() -> None:
        for unsub in unsubs:
            unsub()

    return _unsubscribe
