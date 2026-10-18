"""Circuit climate entities."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import BSB_AUTO, BSB_PROTECTION, DOMAIN, MODE_COOL, MODE_HEAT, MODE_OFF, TEMPERATURE_STEP
from .helpers import (
    async_select_option,
    async_set_numeric_entity,
    derive_global_mode,
    effective_season,
    is_protection,
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

_LOGGER = logging.getLogger(__name__)
_OVERRIDE_DEBOUNCE_SECONDS = 2.0

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
        self._pending_target_temperature: float | None = None
        self._pending_base_temperature: float | None = None
        self._pending_override_task: asyncio.Task | None = None
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
        return effective_season(self.hass, self._entry)

    def _circuit_in_protection(self, mode: str) -> bool:
        """Check circuit-specific protection, independently of the global PAC season."""
        if mode not in (MODE_HEAT, MODE_COOL):
            return False
        prefix = "heat" if mode == MODE_HEAT else "cool"
        key = f"{prefix}_mode_c{self._circuit}"
        return is_protection(state_value(self.hass, self._entry.data.get(key)))

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
        """Expose the same three circuit choices year-round."""
        return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]

    async def _write_circuit_mode_verified(self, entity_id: str, option: str) -> None:
        """Send the known V1.3.3 BSB option and wait for feedback."""
        await async_select_option(self.hass, entity_id, option)
        for _ in range(20):
            current = state_value(self.hass, entity_id)
            if current is not None and is_protection(current) == (option == BSB_PROTECTION):
                return
            await asyncio.sleep(0.5)
        raise HomeAssistantError(
            f"Le régulateur n'a pas confirmé {option} sur {entity_id} après 10 secondes."
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Act on this circuit only, using the validated BSB protection/auto values."""
        if hvac_mode not in (HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL):
            raise HomeAssistantError("Mode de circuit non pris en charge.")
        data = self._entry.data
        heat_id = data[f"heat_mode_c{self._circuit}"]
        cool_id = data[f"cool_mode_c{self._circuit}"]
        heat_state = state_value(self.hass, heat_id)
        cool_state = state_value(self.hass, cool_id)
        if heat_state is None or cool_state is None:
            raise HomeAssistantError("États BSB-LAN indisponibles : aucune commande envoyée.")

        if hvac_mode == HVACMode.OFF:
            if not is_protection(heat_state):
                await self._write_circuit_mode_verified(heat_id, BSB_PROTECTION)
            if not is_protection(cool_state):
                await self._write_circuit_mode_verified(cool_id, BSB_PROTECTION)
            self.async_write_ha_state()
            return

        requested = MODE_HEAT if hvac_mode == HVACMode.HEAT else MODE_COOL
        observed = derive_global_mode(
            state_value(self.hass, data["heat_mode_c1"]),
            state_value(self.hass, data["cool_mode_c1"]),
            state_value(self.hass, data["heat_mode_c2"]),
            state_value(self.hass, data["cool_mode_c2"]),
        )
        if observed not in (MODE_OFF, requested):
            raise HomeAssistantError("Saison opposée active : changement de circuit refusé.")
        global_id = er.async_get(self.hass).async_get_entity_id(
            "select", DOMAIN, f"{self._entry.entry_id}_global_mode"
        )
        global_value = state_value(self.hass, global_id)
        expected = "Chauffage" if requested == MODE_HEAT else "Refroidissement"
        if global_value != expected:
            raise HomeAssistantError(
                f"Sélectionner d'abord {expected} dans le mode global Home Assistant."
            )
        other = cool_state if requested == MODE_HEAT else heat_state
        if not is_protection(other):
            raise HomeAssistantError("Mode saisonnier opposé actif sur ce circuit.")
        selected_id = heat_id if requested == MODE_HEAT else cool_id
        selected = heat_state if requested == MODE_HEAT else cool_state
        if is_protection(selected):
            await self._write_circuit_mode_verified(selected_id, BSB_AUTO)
        self.async_write_ha_state()

    @property
    def hvac_mode(self) -> HVACMode:
        mode = self._mode()
        if self._circuit_in_protection(mode):
            return HVACMode.OFF
        return {MODE_HEAT: HVACMode.HEAT, MODE_COOL: HVACMode.COOL, MODE_OFF: HVACMode.OFF}[mode]

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
        if mode == MODE_OFF or self._circuit_in_protection(mode):
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
        if mode == MODE_OFF or self._circuit_in_protection(mode):
            return None

        # Optimistic target while rapid +/- clicks are grouped.
        if self._pending_target_temperature is not None:
            return self._pending_target_temperature

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
        if mode == MODE_OFF or self._circuit_in_protection(mode):
            return {
                "etat_circuit_bsb": self._circuit_status(mode),
                "mode_circuit": "protection" if self._circuit_in_protection(mode) else "arrêt",
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

    def _cancel_pending_override(self) -> None:
        """Cancel a not-yet-sent debounced override command."""
        task = self._pending_override_task
        self._pending_override_task = None
        if task is not None and not task.done():
            task.cancel()

    async def _async_apply_pending_override(self) -> None:
        """Wait 2 s after the last click, then send one native BSB override."""
        try:
            await asyncio.sleep(_OVERRIDE_DEBOUNCE_SECONDS)
            requested = self._pending_target_temperature
            base = self._pending_base_temperature
            if requested is None or base is None:
                return

            override_active, _override_code, _override_text = self._override_state()
            if override_active is True:
                _LOGGER.warning(
                    "Dérogation circuit %s non envoyée: une dérogation native est déjà active",
                    self._circuit,
                )
                return
            mode = self._mode()
            if override_active is None or mode not in (MODE_HEAT, MODE_COOL) or self._circuit_in_protection(mode):
                _LOGGER.warning(
                    "Dérogation circuit %s non envoyée: état BSB ou mode PAC devenu indisponible",
                    self._circuit,
                )
                return

            delta = round(requested - base, 1)
            offset = abs(delta)
            if offset < 0.1 or offset > 5.0:
                _LOGGER.warning(
                    "Dérogation circuit %s non envoyée: écart %.1f °C hors plage",
                    self._circuit, offset,
                )
                return

            offset_key, offset_parameter = _PARAM[self._circuit]["override_offset"]
            offset_entity = self._source(offset_key, offset_parameter)
            if not offset_entity or offset_entity.split(".", 1)[0] not in {"number", "text"}:
                _LOGGER.error("Paramètre BSB %s d'écart indisponible", offset_parameter)
                return

            duration = self._preferred_override_duration()
            duration_key, duration_parameter = _PARAM[self._circuit]["override_duration"]
            duration_entity = self._source(duration_key, duration_parameter)
            if not duration_entity or duration_entity.split(".", 1)[0] not in {"number", "text"}:
                _LOGGER.error("Paramètre BSB %s de durée indisponible", duration_parameter)
                return

            await async_set_numeric_entity(self.hass, offset_entity, offset)
            await async_set_numeric_entity(self.hass, duration_entity, duration)
            override_entity, direction_option = self._override_option(2 if delta > 0 else 0)
            await async_select_option(self.hass, override_entity, direction_option)
            await async_poll_parameters(
                self.hass,
                (offset_parameter, duration_parameter, _PARAM[self._circuit]["override"][1],
                 _PARAM[self._circuit]["effective_setpoint"]),
            )
        except asyncio.CancelledError:
            return
        except Exception:
            _LOGGER.exception("Échec de l'envoi de la dérogation native du circuit %s", self._circuit)
        finally:
            self._pending_override_task = None
            self._pending_target_temperature = None
            self._pending_base_temperature = None
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs) -> None:
        """Aggregate Climate clicks for 2 s, then create one native override."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        mode = self._mode()
        if mode == MODE_OFF or self._circuit_in_protection(mode):
            raise HomeAssistantError("Circuit en protection ou PAC arrêtée : aucune dérogation envoyée.")
        if mode not in (MODE_HEAT, MODE_COOL):
            raise HomeAssistantError("Saison indéterminée : dérogation refusée.")

        override_active, _override_code, _override_text = self._override_state()
        if override_active is True:
            raise HomeAssistantError(
                "Une dérogation native est déjà active. Annule-la avec le bouton du "
                "circuit avant de choisir une nouvelle consigne."
            )
        if override_active is None:
            raise HomeAssistantError(
                "Impossible de confirmer l’état 701/1001 de la dérogation. Aucune "
                "commande n’a été envoyée."
            )

        if self._pending_base_temperature is None:
            base = state_float(
                self.hass,
                self._source(
                    f"effective_setpoint_c{self._circuit}",
                    _PARAM[self._circuit]["effective_setpoint"],
                ),
            )
            if base is None:
                raise HomeAssistantError(
                    "Consigne effective 8741/8771 indisponible : impossible de calculer "
                    "l’écart de dérogation en sécurité."
                )
            self._pending_base_temperature = base
        else:
            base = self._pending_base_temperature

        requested = round_temperature_step(float(temperature), TEMPERATURE_STEP)
        # Keep the V1.3.3 cooling path unchanged for colder requests.
        # Heating may request either native direction: 0 colder, 2 warmer.
        if mode == MODE_COOL and requested > base:
            raise HomeAssistantError(
                "En rafraîchissement, seule une dérogation plus froide est validée."
            )

        offset = abs(round(requested - base, 1))
        if offset > 5.0:
            raise HomeAssistantError(
                f"Écart demandé {offset:.1f} °C hors plage de sécurité 0,1–5,0 °C."
            )
        if offset < 0.1:
            self._cancel_pending_override()
            self._pending_target_temperature = None
            self._pending_base_temperature = None
            self.async_write_ha_state()
            return

        self._pending_target_temperature = requested
        self._cancel_pending_override()
        self._pending_override_task = self.hass.async_create_task(
            self._async_apply_pending_override(),
            f"alfea_override_c{self._circuit}_debounce",
        )
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._cancel_pending_override)
        data = self._entry.data
        global_select = er.async_get(self.hass).async_get_entity_id(
            "select", DOMAIN, f"{self._entry.entry_id}_global_mode"
        )
        tracked: list[str | None] = [
            global_select,
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
