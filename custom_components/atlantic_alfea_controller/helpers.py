"""Helpers for Atlantic Alfea BSB-LAN."""

from __future__ import annotations

from collections.abc import Callable
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import BSB_AUTO, BSB_PROTECTION, MODE_COOL, MODE_HEAT, MODE_OFF
from .discovery import discover_parameter_entity as _discover_parameter_entity

_INVALID_STATES = {"unknown", "unavailable", "none", "---", ""}
_TRUE_STATES = {"on", "1", "true", "activé", "active", "enabled", "marche"}
_FALSE_STATES = {"off", "0", "false", "désactivé", "desactive", "disabled", "arrêt"}
_BSB_STATUS_RE = re.compile(r"^\s*(-?\d+)\s*-\s*(.*?)\s*$")


_REDUCED_STATUS_MARKERS = (
    "réduit",
    "reduit",
    "reduced",
    "éco",
    "eco",
)

_COMFORT_STATUS_MARKERS = (
    "confort",
    "comfort",
)

_IDLE_STATUS_MARKERS = (
    "arrêt",
    "protection",
    "attente",
    "bloqu",
    "limitation",
    "satisf",
    "régime d'été",
    "régime eco de jour actif",
    "régime éco de jour actif",
    "regime eco de jour actif",
    "hors gel",
    "pas de demande",
    "veille",
    "temporisation",
    "délai",
    "verrou",
)


def discover_parameter_entity(hass: HomeAssistant, parameter: int) -> str | None:
    """Find the best BSB-LAN entity for a parameter."""
    return _discover_parameter_entity(hass, parameter)


def source_entity(
    hass: HomeAssistant,
    entry: ConfigEntry,
    key: str,
    parameter: int | None = None,
) -> str | None:
    """Resolve a configured entity, falling back to BSB parameter discovery."""
    configured = entry.data.get(key)
    if configured and hass.states.get(configured) is not None:
        return configured
    if parameter is not None:
        discovered = discover_parameter_entity(hass, parameter)
        if discovered is not None:
            return discovered
    return configured


def state_value(hass: HomeAssistant, entity_id: str | None) -> str | None:
    """Return a state string, excluding unavailable values."""
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return None
    value = str(state.state).strip()
    if value.lower() in _INVALID_STATES:
        return None
    return value


def state_float(hass: HomeAssistant, entity_id: str | None) -> float | None:
    """Return a numeric state, accepting decimal commas and units."""
    raw = state_value(hass, entity_id)
    if raw is None:
        return None
    try:
        normalized = raw.replace("\u202f", "").replace(" ", "").replace(",", ".")
        number = ""
        for char in normalized:
            if char.isdigit() or char in {"-", "+", "."}:
                number += char
            elif number:
                break
        return float(number)
    except (ValueError, AttributeError):
        return None


def state_is_on(hass: HomeAssistant, entity_id: str | None) -> bool | None:
    """Convert a BSB-LAN boolean-like entity state to a bool."""
    value = state_value(hass, entity_id)
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in _TRUE_STATES or normalized.startswith("1 -"):
        return True
    if normalized in _FALSE_STATES or normalized.startswith("0 -"):
        return False
    return None


def split_bsb_status(value: str | None) -> tuple[int | None, str | None]:
    """Split a BSB status into its optional numeric code and readable text."""
    if value is None:
        return None, None
    match = _BSB_STATUS_RE.match(value)
    if match is None:
        return None, value.strip() or None
    try:
        code = int(match.group(1))
    except ValueError:
        code = None
    text = match.group(2).strip()
    return code, text or value.strip()


def clean_bsb_status(value: str | None) -> str | None:
    """Remove the leading BSB status number from a readable state."""
    _code, text = split_bsb_status(value)
    return text


def is_protection(value: str | None) -> bool:
    """Return whether a BSB select is in protection mode."""
    return value is not None and (value.startswith("0 -") or "protection" in value.lower())


def is_enabled(value: str | None) -> bool:
    """Return whether a BSB circuit is enabled."""
    return value is not None and not is_protection(value)


def derive_global_mode(
    heat_c1: str | None,
    cool_c1: str | None,
    heat_c2: str | None,
    cool_c2: str | None,
) -> str:
    """Derive the global PAC mode from the four BSB circuit selectors."""
    heat = is_enabled(heat_c1) or is_enabled(heat_c2)
    cool = is_enabled(cool_c1) or is_enabled(cool_c2)
    if heat and not cool:
        return MODE_HEAT
    if cool and not heat:
        return MODE_COOL
    return MODE_OFF


async def async_select_option(hass: HomeAssistant, entity_id: str, option: str) -> None:
    """Set an option on a Home Assistant select entity."""
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": option},
        blocking=True,
    )


async def async_set_numeric_entity(hass: HomeAssistant, entity_id: str, value: float) -> None:
    """Write a numeric value to a BSB-LAN text or number entity."""
    domain = entity_id.split(".", 1)[0]
    if domain == "number":
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": float(value)},
            blocking=True,
        )
        return
    if domain == "text":
        await hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": entity_id, "value": f"{value:.1f}"},
            blocking=True,
        )
        return
    raise ValueError(f"Unsupported writable numeric entity: {entity_id}")


async def async_apply_global_mode(hass: HomeAssistant, data: dict[str, Any], mode: str) -> None:
    """Apply a mutually exclusive global mode to both hydraulic circuits."""
    heat_entities = [data["heat_mode_c1"], data["heat_mode_c2"]]
    cool_entities = [data["cool_mode_c1"], data["cool_mode_c2"]]

    if mode == MODE_OFF:
        for entity_id in (*heat_entities, *cool_entities):
            await async_select_option(hass, entity_id, BSB_PROTECTION)
        return

    if mode == MODE_HEAT:
        for entity_id in cool_entities:
            await async_select_option(hass, entity_id, BSB_PROTECTION)
        for entity_id in heat_entities:
            await async_select_option(hass, entity_id, BSB_AUTO)
        return

    if mode == MODE_COOL:
        for entity_id in heat_entities:
            await async_select_option(hass, entity_id, BSB_PROTECTION)
        for entity_id in cool_entities:
            await async_select_option(hass, entity_id, BSB_AUTO)
        return

    raise ValueError(f"Unsupported PAC mode: {mode}")



def status_uses_reduced_setpoint(value: str | None) -> bool:
    """Return whether a BSB circuit state explicitly indicates reduced/Eco."""
    if not value:
        return False
    text = value.lower()
    return any(marker in text for marker in _REDUCED_STATUS_MARKERS)


def status_uses_comfort_setpoint(value: str | None) -> bool:
    """Return whether a BSB circuit state explicitly indicates comfort."""
    if not value:
        return False
    text = value.lower()
    return any(marker in text for marker in _COMFORT_STATUS_MARKERS)


def status_is_blocked_or_idle(value: str | None) -> bool:
    """Return true for circuit states that do not prove active heating/cooling."""
    if not value:
        return True
    text = value.lower()
    return any(marker in text for marker in _IDLE_STATUS_MARKERS)


def dhw_charge_requested(value: str | None) -> bool | None:
    """Return whether BSB 8003 represents an actual DHW charge request.

    A label beginning with ``Charge`` can describe a real request, but some
    controller states explicitly say that charging is blocked, waiting or
    restricted. Those must not be treated as active DHW production.
    """
    if value is None:
        return None
    _code, text = split_bsb_status(value)
    normalized = (text or value).strip().lower()
    if not normalized:
        return None

    inactive_markers = (
        "chargé",
        "charge bloquée",
        "blocage de charge",
        "charge en veille",
        "charge restreinte",
        "arrêt",
        "pas de demande",
    )
    if any(marker in normalized for marker in inactive_markers):
        return False
    return normalized.startswith("charge")


def generator_is_cooling(value: str | None) -> bool | None:
    """Return whether BSB 8006 explicitly reports cold-mode generator operation.

    This is intentionally conservative: only explicit ``mode froid`` / cooling
    wording is treated as proof that the compressor is serving cooling rather
    than domestic hot water.
    """
    if value is None:
        return None
    _code, text = split_bsb_status(value)
    normalized = (text or value).strip().lower()
    if not normalized:
        return None
    return any(
        marker in normalized
        for marker in (
            "mode froid",
            "mode refroidissement",
            "régime refroidissement",
            "regime refroidissement",
        )
    )


def round_temperature_step(value: float, step: float = 0.5) -> float:
    """Round a requested target temperature to the configured UI step."""
    return round(round(value / step) * step, 1)


def track_entities(
    hass: HomeAssistant,
    entity_ids: list[str | None],
    update_callback: Callable[[], None],
) -> Callable[[], None]:
    """Track source entity changes and invoke an entity update callback."""
    tracked = sorted({entity_id for entity_id in entity_ids if entity_id})

    @callback
    def _handle_event(_event: Any) -> None:
        update_callback()

    return async_track_state_change_event(hass, tracked, _handle_event)
