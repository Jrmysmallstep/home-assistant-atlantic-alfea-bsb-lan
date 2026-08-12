"""Circuit climate entities."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, MODE_COOL, MODE_HEAT, MODE_OFF, TEMPERATURE_STEP
from .helpers import (
    async_select_option,
    async_set_numeric_entity,
    derive_global_mode,
    round_temperature_step,
    source_entity,
    split_bsb_status,
    state_float,
    state_is_on,
    state_value,
    status_is_blocked_or_idle,
    status_uses_comfort_setpoint,
    status_uses_reduced_setpoint,
    track_entities,
)
from .polling import async_poll_parameters

_PROFILE_COMFORT = "comfort"
_PROFILE_REDUCED = "reduced"

_PARAM = {
    1: {
        "room": 8740,
        "effective_setpoint": 8741,
        "heat_state": 8000,
        "override": ("override_c1", 701),
        "override_offset": ("override_offset_c1", 10991),
        "override_duration": ("override_duration_c1", 10990),
        "cool_state": 8004,
        "setpoints": {
            MODE_HEAT: {
                _PROFILE_COMFORT: ("heat_setpoint_c1", 710),
                _PROFILE_REDUCED: ("heat_reduced_setpoint_c1", 712),
            },
            MODE_COOL: {
                _PROFILE_COMFORT: ("cool_setpoint_c1", 902),
                _PROFILE_REDUCED: ("cool_reduced_setpoint_c1", 903),
            },
        },
    },
    2: {
        "room": 8770,
        "effective_setpoint": 8771,
        "heat_state": 8001,
        "override": ("override_c2", 1001),
        "override_offset": ("override_offset_c2", 10993),
        "override_duration": ("override_duration_c2", 10992),
        "cool_state": 8025,
        "setpoints": {
            MODE_HEAT: {
                _PROFILE_COMFORT: ("heat_setpoint_c2", 1010),
                _PROFILE_REDUCED: ("heat_reduced_setpoint_c2", 1012),
            },
            MODE_COOL: {
                _PROFILE_COMFORT: ("cool_setpoint_c2", 1202),
                _PROFILE_REDUCED: ("cool_reduced_setpoint_c2", 1203),
            },
        },
    },
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([AlfeaCircuitClimate(hass, entry, 1), AlfeaCircuitClimate(hass, entry, 2)])


class AlfeaCircuitClimate(ClimateEntity):
    """Temperature control for one circuit, inheriting the global PAC mode."""

    _attr_has_entity_name = True
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = "°C"
    _attr_target_temperature_step = TEMPERATURE_STEP
    _attr_min_temp = 5.0
    _attr_max_temp = 35.0

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, circuit: int) -> None:
        self.hass = hass
        self._entry = entry
        self._circuit = circuit
        self._attr_name = f"Circuit {circuit}"
        self._attr_unique_id = f"{entry.entry_id}_circuit_{circuit}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Atlantic Alfea BSB-LAN",
            manufacturer="Atlantic",
            model="Alfea via BSB-LAN",
        )

    def _source(self, key: str, parameter: int | None = None) -> str | None:
        return source_entity(self.hass, self._entry, key, parameter)

    def _mode(self) -> str:
        data = self._entry.data
        return derive_global_mode(
            state_value(self.hass, data["heat_mode_c1"]),
            state_value(self.hass, data["cool_mode_c1"]),
            state_value(self.hass, data["heat_mode_c2"]),
            state_value(self.hass, data["cool_mode_c2"]),
        )

    def _circuit_status(self, mode: str) -> str | None:
        if mode not in (MODE_HEAT, MODE_COOL):
            return None
        state_key = f"{'heat' if mode == MODE_HEAT else 'cool'}_state_c{self._circuit}"
        state_param = _PARAM[self._circuit]["heat_state" if mode == MODE_HEAT else "cool_state"]
        return state_value(self.hass, self._source(state_key, state_param))

    def _active_profile(self, mode: str) -> str | None:
        """Return the profile explicitly reported by the active circuit status.

        The integration deliberately does not assume comfort when the BSB state is
        ambiguous. This prevents a Home Assistant command from being written to
        the wrong setpoint while the controller is transitioning between states.
        """
        status = self._circuit_status(mode)
        if status_uses_reduced_setpoint(status):
            return _PROFILE_REDUCED
        if status_uses_comfort_setpoint(status):
            return _PROFILE_COMFORT
        return None

    def _setpoint(self, mode: str, profile: str) -> tuple[str | None, int]:
        key, parameter = _PARAM[self._circuit]["setpoints"][mode][profile]
        return self._source(key, parameter), parameter

    def _override_state(self) -> tuple[bool | None, int | None, str | None]:
        """Return native override active state from validated BSB 701/1001 semantics."""
        key, parameter = _PARAM[self._circuit]["override"]
        raw = state_value(self.hass, self._source(key, parameter))
        code, text = split_bsb_status(raw)
        if code is None:
            return None, None, text
        return code != 1, code, text

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return [self.hvac_mode]

    @property
    def hvac_mode(self) -> HVACMode:
        return {MODE_HEAT: HVACMode.HEAT, MODE_COOL: HVACMode.COOL, MODE_OFF: HVACMode.OFF}[self._mode()]

    @property
    def hvac_action(self) -> HVACAction:
        """Return real circuit activity, not merely the selected season/program.

        BSB 8004/8025 can report a cooling regime while there is no thermal
        demand at all. Conversely, compressor state 8400 is global and can be
        active for the other circuit or for ECS. We therefore combine the
        compressor state with this circuit's room temperature and effective
        target (8741/8771).
        """
        mode = self._mode()
        if mode == MODE_OFF:
            return HVACAction.OFF

        circuit_state = self._circuit_status(mode)
        if status_is_blocked_or_idle(circuit_state):
            return HVACAction.IDLE

        # A logical 8003 ``Charge...`` request is not sufficient to stop the
        # climate action: it can stay present while the generator is cooling.
        # The physical ECS outputs are the reliable proof that the generator is
        # actually assigned to DHW. This logic is season-independent.
        dhw_pump = state_is_on(self.hass, self._source("dhw_pump", 8820))
        if dhw_pump is True:
            return HVACAction.IDLE

        compressor_on = state_is_on(self.hass, self._source("compressor_state", 8400))
        if compressor_on is False:
            return HVACAction.IDLE

        current = self.current_temperature
        target = self.target_temperature
        if compressor_on is True and current is not None and target is not None:
            # Small margin only prevents floating point chatter; the PAC itself
            # remains responsible for its true hysteresis and regulation.
            margin = 0.05
            if mode == MODE_COOL:
                return HVACAction.COOLING if current > target + margin else HVACAction.IDLE
            return HVACAction.HEATING if current < target - margin else HVACAction.IDLE

        # If a source is temporarily unavailable, do not invent inactivity when
        # the BSB circuit state clearly reports an active regime.
        if compressor_on is True:
            return HVACAction.HEATING if mode == MODE_HEAT else HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def current_temperature(self) -> float | None:
        source = self._source(f"room_temp_c{self._circuit}", _PARAM[self._circuit]["room"])
        return state_float(self.hass, source)

    @property
    def target_temperature(self) -> float | None:
        """Expose the effective target displayed by the PAC (8741/8771).

        The programmed Comfort/Eco values remain the writable setpoints. The
        controller can offset those values, so the effective target is the value
        that best matches the PAC's own screen.
        """
        mode = self._mode()
        if mode == MODE_OFF:
            return None

        effective = state_float(
            self.hass,
            self._source(
                f"effective_setpoint_c{self._circuit}",
                _PARAM[self._circuit]["effective_setpoint"],
            ),
        )
        if effective is not None:
            return effective

        # Fallback to the programmed setpoint if the effective target is absent.
        profile = self._active_profile(mode)
        if profile is None:
            return None
        source, _parameter = self._setpoint(mode, profile)
        return state_float(self.hass, source)

    @property
    def extra_state_attributes(self) -> dict[str, object | None]:
        mode = self._mode()
        if mode == MODE_OFF:
            return {
                "etat_circuit_bsb": None,
                "regime_consigne": None,
                "ecriture_consigne_autorisee": False,
                "parametre_consigne_actif": None,
                "entite_consigne_active": None,
                "derogation_native_active": None,
            }

        status = self._circuit_status(mode)
        profile = self._active_profile(mode)
        comfort_source, comfort_parameter = self._setpoint(mode, _PROFILE_COMFORT)
        reduced_source, reduced_parameter = self._setpoint(mode, _PROFILE_REDUCED)

        active_source: str | None = None
        active_parameter: int | None = None
        if profile is not None:
            active_source, active_parameter = self._setpoint(mode, profile)

        override_active, override_code, override_text = self._override_state()

        return {
            "etat_circuit_bsb": status,
            "derogation_native_active": override_active,
            "derogation_code_bsb": override_code,
            "derogation_etat_bsb": override_text,
            "parametre_derogation": 701 if self._circuit == 1 else 1001,
            "ecart_derogation": state_float(
                self.hass,
                self._source(*_PARAM[self._circuit]["override_offset"]),
            ),
            "parametre_ecart_derogation": _PARAM[self._circuit]["override_offset"][1],
            "duree_derogation_configuree": state_float(
                self.hass,
                self._source(*_PARAM[self._circuit]["override_duration"]),
            ),
            "duree_derogation_ha": self._preferred_override_duration_or_none(),
            "parametre_duree_derogation": _PARAM[self._circuit]["override_duration"][1],
            "regime_consigne": (
                "réduit"
                if profile == _PROFILE_REDUCED
                else "confort"
                if profile == _PROFILE_COMFORT
                else "indéterminé"
            ),
            "ecriture_consigne_autorisee": profile is not None,
            "parametre_consigne_actif": active_parameter,
            "entite_consigne_active": active_source,
            "consigne_confort": state_float(self.hass, comfort_source),
            "parametre_consigne_confort": comfort_parameter,
            "consigne_reduite": state_float(self.hass, reduced_source),
            "parametre_consigne_reduite": reduced_parameter,
            "consigne_effective": state_float(
                self.hass,
                self._source(
                    f"effective_setpoint_c{self._circuit}",
                    _PARAM[self._circuit]["effective_setpoint"],
                ),
            ),
            "parametre_consigne_effective": _PARAM[self._circuit]["effective_setpoint"],
        }

    def _override_option(self, code: int) -> tuple[str, str]:
        """Return the writable BSB override select and the option matching *code*."""
        key, parameter = _PARAM[self._circuit]["override"]
        entity_id = self._source(key, parameter)
        if not entity_id or not entity_id.startswith("select."):
            raise HomeAssistantError(
                f"Le paramètre BSB {parameter} de dérogation du circuit {self._circuit} "
                "n’est pas disponible comme select modifiable."
            )
        state = self.hass.states.get(entity_id)
        options = state.attributes.get("options") if state is not None else None
        for option in options or []:
            text = str(option).strip()
            if text == str(code) or text.startswith(f"{code} -"):
                return entity_id, str(option)
        raise HomeAssistantError(
            f"L’option BSB {code} n’est pas disponible sur {entity_id}. "
            f"Options reçues : {options!r}."
        )

    def _preferred_override_duration_or_none(self) -> float | None:
        """Return the HA-selected override duration without raising from attributes."""
        registry = er.async_get(self.hass)
        unique_id = f"{self._entry.entry_id}_override_duration_c{self._circuit}"
        entity_id = registry.async_get_entity_id("number", DOMAIN, unique_id)
        duration = state_float(self.hass, entity_id) if entity_id else None
        if duration is None:
            return None
        return float(round(duration))

    def _preferred_override_duration(self) -> float:
        """Return the duration selected in Home Assistant for this circuit."""
        registry = er.async_get(self.hass)
        unique_id = f"{self._entry.entry_id}_override_duration_c{self._circuit}"
        entity_id = registry.async_get_entity_id("number", DOMAIN, unique_id)
        duration = state_float(self.hass, entity_id) if entity_id else None
        if duration is None:
            # Safe fallback: use the duration currently configured in the PAC.
            duration = state_float(
                self.hass,
                self._source(*_PARAM[self._circuit]["override_duration"]),
            )
        if duration is None:
            raise HomeAssistantError(
                "Durée de dérogation indisponible. Vérifie le réglage "
                f"‘Circuit {self._circuit} — Durée dérogation’."
            )
        if duration < 1 or duration > 24:
            raise HomeAssistantError(
                f"Durée de dérogation {duration:g} h hors plage 1–24 h. "
                "Aucune commande n’a été envoyée."
            )
        return float(round(duration))

    async def async_set_temperature(self, **kwargs) -> None:
        """Create the PAC native temporary override from a Climate target change.

        Safety scope for the first implementation:
        * only cooling is enabled, because this is the direction validated on the bus;
        * only a colder target is accepted (BSB ``Plus froid`` / code 0);
        * Comfort/Eco programmed setpoints are never modified;
        * duration comes from the HA per-circuit selector (1–24 h).
        """
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        mode = self._mode()
        if mode == MODE_OFF:
            raise HomeAssistantError("La PAC est arrêtée : aucune dérogation n’a été envoyée.")
        if mode != MODE_COOL:
            raise HomeAssistantError(
                "La dérogation depuis Home Assistant est volontairement limitée au "
                "rafraîchissement pour ce premier test. Le comportement chauffage sera "
                "validé séparément en saison de chauffe."
            )

        override_active, _override_code, _override_text = self._override_state()
        if override_active is True:
            raise HomeAssistantError(
                "Une dérogation native est déjà active. Annule-la avec le bouton du "
                "circuit avant de choisir une nouvelle consigne pour ce premier test."
            )
        if override_active is None:
            raise HomeAssistantError(
                "Impossible de confirmer l’état 701/1001 de la dérogation. Aucune "
                "commande n’a été envoyée."
            )

        base = self.target_temperature
        if base is None:
            raise HomeAssistantError(
                "Consigne effective 8741/8771 indisponible : impossible de calculer "
                "l’écart de dérogation en sécurité."
            )

        requested = round_temperature_step(float(temperature), TEMPERATURE_STEP)
        if abs(requested - base) < 0.05:
            return
        if requested > base:
            raise HomeAssistantError(
                "Pour cette première version de test, seule une consigne plus froide "
                "est autorisée. Le sens ‘Plus chaud’ n’a pas encore été validé sur le bus."
            )

        offset = round(base - requested, 1)
        if offset < 0.1 or offset > 5.0:
            raise HomeAssistantError(
                f"Écart demandé {offset:.1f} °C hors plage de sécurité 0,1–5,0 °C. "
                "Aucune commande n’a été envoyée."
            )

        offset_key, offset_parameter = _PARAM[self._circuit]["override_offset"]
        offset_entity = self._source(offset_key, offset_parameter)
        if not offset_entity or offset_entity.split(".", 1)[0] not in {"number", "text"}:
            raise HomeAssistantError(
                f"Le paramètre d’écart BSB {offset_parameter} n’a pas été détecté "
                "comme entité number/text modifiable. Relance la détection BSB-LAN."
            )

        duration = self._preferred_override_duration()
        duration_key, duration_parameter = _PARAM[self._circuit]["override_duration"]
        duration_entity = self._source(duration_key, duration_parameter)
        if not duration_entity or duration_entity.split(".", 1)[0] not in {"number", "text"}:
            raise HomeAssistantError(
                f"Le paramètre de durée BSB {duration_parameter} n’a pas été détecté "
                "comme entité number/text modifiable. Relance la détection BSB-LAN."
            )

        # Sequence observed from the native room unit: neutral state, offset, duration,
        # then activation of BSB 'Plus froid'. Comfort/Eco remain untouched.
        await async_set_numeric_entity(self.hass, offset_entity, offset)
        await async_set_numeric_entity(self.hass, duration_entity, duration)
        override_entity, plus_cold_option = self._override_option(0)
        await async_select_option(self.hass, override_entity, plus_cold_option)

        await async_poll_parameters(
            self.hass,
            (offset_parameter, duration_parameter, _PARAM[self._circuit]["override"][1],
             _PARAM[self._circuit]["effective_setpoint"]),
        )

    async def async_added_to_hass(self) -> None:
        data = self._entry.data
        tracked: list[str | None] = [
            data["heat_mode_c1"], data["cool_mode_c1"],
            data["heat_mode_c2"], data["cool_mode_c2"],
            self._source(f"room_temp_c{self._circuit}", _PARAM[self._circuit]["room"]),
            self._source(
                f"effective_setpoint_c{self._circuit}",
                _PARAM[self._circuit]["effective_setpoint"],
            ),
            self._source(f"heat_state_c{self._circuit}", _PARAM[self._circuit]["heat_state"]),
            self._source(f"cool_state_c{self._circuit}", _PARAM[self._circuit]["cool_state"]),
            self._source("compressor_state", 8400),
            self._source("dhw_state", 8003),
            self._source("dhw_pump", 8820),
            self._source("pac_state", 8006),
            self._source(*_PARAM[self._circuit]["override"]),
            self._source(*_PARAM[self._circuit]["override_offset"]),
            self._source(*_PARAM[self._circuit]["override_duration"]),
        ]
        for mode in (MODE_HEAT, MODE_COOL):
            for profile in (_PROFILE_COMFORT, _PROFILE_REDUCED):
                source, _parameter = self._setpoint(mode, profile)
                tracked.append(source)

        self.async_on_remove(
            track_entities(self.hass, tracked, self.async_write_ha_state)
        )
