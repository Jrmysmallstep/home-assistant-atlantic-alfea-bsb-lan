"""Automatic entity discovery for Atlantic Alfea BSB-LAN."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Mapping

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .parameters import (
    GROUP_COMMANDS,
    PARAMETER_SPECS,
    SPEC_BY_PARAMETER,
    ParameterSpec,
)

_INVALID_STATES: Final = {"unknown", "unavailable", "none", "---", ""}


@dataclass(slots=True)
class DiscoveryResult:
    """Result of a complete entity discovery pass."""

    mapping: dict[str, str]
    unresolved: dict[str, list[str]]
    missing_required: list[str]
    missing_optional: list[str]

    @property
    def found_count(self) -> int:
        """Return the number of automatically associated parameters."""
        return len(self.mapping)


@dataclass(frozen=True, slots=True)
class _Candidate:
    entity_id: str
    score: int
    exact_id_match: bool
    exact_name_match: bool


def _matches_parameter(entity_id: str, friendly_name: str, parameter: int) -> tuple[bool, bool]:
    """Return exact entity-id and friendly-name matches for a parameter."""
    object_id = entity_id.split(".", 1)[-1]
    id_match = re.search(rf"(?:^|_){parameter}(?:_|$)", object_id) is not None
    name_match = re.search(rf"(?<!\d){parameter}(?!\d)", friendly_name) is not None
    return id_match, name_match


def _domain_priority(spec: ParameterSpec, domain: str) -> int:
    """Prefer domains in the order declared by the parameter specification."""
    try:
        index = spec.domains.index(domain)
    except ValueError:
        return -1
    return len(spec.domains) - index


def _candidate_score(
    hass: HomeAssistant,
    entity_id: str,
    friendly_name: str,
    spec: ParameterSpec,
) -> _Candidate | None:
    """Score a possible BSB-LAN source entity."""
    id_match, name_match = _matches_parameter(entity_id, friendly_name, spec.parameter)
    if not id_match and not name_match:
        return None

    domain = entity_id.split(".", 1)[0]
    if domain == DOMAIN or "atlantic_alfea" in entity_id:
        return None

    domain_priority = _domain_priority(spec, domain)
    if domain_priority < 0:
        return None

    registry = er.async_get(hass)
    registry_entry = registry.async_get(entity_id)
    platform = registry_entry.platform if registry_entry is not None else ""

    object_id = entity_id.split(".", 1)[-1].lower()
    friendly_lower = friendly_name.lower()
    score = domain_priority * 25

    if platform == "mqtt":
        score += 1000
    elif platform in {"bsblan", "bsb_lan"}:
        score += 500

    if "bsb_lan" in object_id or "bsblan" in object_id:
        score += 400
    elif "bsb-lan" in friendly_lower or "bsb lan" in friendly_lower:
        score += 250

    if id_match:
        score += 300
    if name_match:
        score += 150

    state = hass.states.get(entity_id)
    if state is not None and str(state.state).strip().lower() not in _INVALID_STATES:
        score += 20
        age = max(0.0, (dt_util.utcnow() - state.last_updated).total_seconds())
        if age <= 300:
            score += 60
        elif age <= 3600:
            score += 40
        elif age <= 86400:
            score += 15

    return _Candidate(entity_id, score, id_match, name_match)


def _scored_candidates(hass: HomeAssistant, spec: ParameterSpec) -> list[_Candidate]:
    """Return scored candidates for one BSB parameter."""
    candidates: list[_Candidate] = []
    for state in hass.states.async_all():
        friendly_name = str(state.attributes.get("friendly_name", ""))
        candidate = _candidate_score(hass, state.entity_id, friendly_name, spec)
        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(key=lambda candidate: (-candidate.score, candidate.entity_id))
    return candidates


def discover_candidates(hass: HomeAssistant, spec: ParameterSpec) -> list[str]:
    """Return candidate entity IDs, best candidate first."""
    return [candidate.entity_id for candidate in _scored_candidates(hass, spec)]


def discover_parameter_entity(
    hass: HomeAssistant,
    parameter: int,
    current_entity: str | None = None,
) -> str | None:
    """Find the safest entity for one BSB parameter."""
    spec = SPEC_BY_PARAMETER.get(parameter)
    if spec is None:
        spec = ParameterSpec(
            str(parameter),
            parameter,
            False,
            ("sensor", "binary_sensor", "select", "text", "number"),
            "measurements",
        )

    if current_entity and hass.states.get(current_entity) is not None:
        current_domain = current_entity.split(".", 1)[0]
        if current_domain in spec.domains and spec.group == GROUP_COMMANDS:
            # Writable mappings remain pinned once validated so an automatic
            # refresh can never redirect a command to another entity.
            return current_entity

    candidates = _scored_candidates(hass, spec)
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0].entity_id

    first, second = candidates[0], candidates[1]
    if first.score > second.score:
        return first.entity_id

    # Read-only states and diagnostics are safe to associate when the tied
    # candidates both match the exact BSB number. Writable command parameters
    # remain unresolved in a tie to prevent writing to the wrong entity.
    if (
        spec.group != GROUP_COMMANDS
        and first.exact_id_match
        and second.exact_id_match
        and first.entity_id.split(".", 1)[0] == spec.domains[0]
    ):
        return first.entity_id

    return None


def discover_mapping(
    hass: HomeAssistant,
    current: Mapping[str, str] | None = None,
) -> DiscoveryResult:
    """Discover all supported BSB-LAN source entities."""
    current = current or {}
    mapping: dict[str, str] = {}
    unresolved: dict[str, list[str]] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for spec in PARAMETER_SPECS:
        current_entity = current.get(spec.key)
        selected = discover_parameter_entity(
            hass,
            spec.parameter,
            current_entity=current_entity,
        )
        if selected is not None:
            mapping[spec.key] = selected
            continue

        candidates = discover_candidates(hass, spec)
        if candidates:
            unresolved[spec.key] = candidates
        elif spec.required:
            missing_required.append(spec.key)
        else:
            missing_optional.append(spec.key)

    return DiscoveryResult(mapping, unresolved, missing_required, missing_optional)
