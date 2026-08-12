"""BSB parameter mapping, grouped by purpose."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .const import (
    CONF_CLOCK_DATETIME,
    CONF_COMPRESSOR_HOURS,
    CONF_COMPRESSOR_MIN_OFF,
    CONF_COMPRESSOR_MIN_RUN,
    CONF_COMPRESSOR_MODULATION,
    CONF_COMPRESSOR_STARTS,
    CONF_COMPRESSOR_STARTS_CURRENT_RATE,
    CONF_COMPRESSOR_STARTS_MAX_RATE,
    CONF_COMPRESSOR_STATE,
    CONF_COOL_MODE_C1,
    CONF_COOL_REDUCED_SETPOINT_C1,
    CONF_COOL_MODE_C2,
    CONF_COOL_REDUCED_SETPOINT_C2,
    CONF_COOL_SETPOINT_C1,
    CONF_COOL_SETPOINT_C2,
    CONF_COOL_STATE_C1,
    CONF_COOL_STATE_C2,
    CONF_DEFROST,
    CONF_DHW_ELECTRIC_HEATER,
    CONF_DHW_PUMP,
    CONF_DHW_MODE,
    CONF_DHW_NOMINAL_SETPOINT,
    CONF_DHW_REDUCED_SETPOINT,
    CONF_DHW_STATE,
    CONF_DHW_TEMPERATURE,
    CONF_ENERGY_TOTAL,
    CONF_FLOW_TEMP,
    CONF_EFFECTIVE_SETPOINT_C1,
    CONF_EFFECTIVE_SETPOINT_C2,
    CONF_HEAT_MODE_C1,
    CONF_HEAT_FLOW_TARGET_C1,
    CONF_OVERRIDE_C1,
    CONF_OVERRIDE_OFFSET_C1,
    CONF_OVERRIDE_DURATION_C1,
    CONF_HEAT_REDUCED_SETPOINT_C1,
    CONF_HEAT_MODE_C2,
    CONF_HEAT_FLOW_TARGET_C2,
    CONF_OVERRIDE_C2,
    CONF_OVERRIDE_OFFSET_C2,
    CONF_OVERRIDE_DURATION_C2,
    CONF_HEAT_REDUCED_SETPOINT_C2,
    CONF_HEAT_SETPOINT_C1,
    CONF_HEAT_SETPOINT_C2,
    CONF_HEAT_STATE_C1,
    CONF_HEAT_STATE_C2,
    CONF_OUTDOOR_TEMP,
    CONF_PAC_STATE,
    CONF_RETURN_TEMP,
    CONF_ROOM_TEMP_C1,
    CONF_ROOM_TEMP_C2,
    CONF_TARGET_FLOW_TEMP,
)

GROUP_COMMANDS: Final = "commands"
GROUP_STATES: Final = "states"
GROUP_MEASUREMENTS: Final = "measurements"


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """Describe one BSB-LAN source entity."""

    key: str
    parameter: int
    required: bool
    domains: tuple[str, ...]
    group: str


COMMAND_PARAMETERS: Final[tuple[ParameterSpec, ...]] = (
    ParameterSpec(CONF_CLOCK_DATETIME, 0, False, ("text", "sensor"), GROUP_COMMANDS),
    ParameterSpec(CONF_HEAT_MODE_C1, 700, True, ("select",), GROUP_COMMANDS),
    ParameterSpec(CONF_HEAT_SETPOINT_C1, 710, True, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_HEAT_REDUCED_SETPOINT_C1, 712, False, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_COOL_MODE_C1, 901, True, ("select",), GROUP_COMMANDS),
    ParameterSpec(CONF_COOL_SETPOINT_C1, 902, True, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_COOL_REDUCED_SETPOINT_C1, 903, False, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_HEAT_MODE_C2, 1000, True, ("select",), GROUP_COMMANDS),
    ParameterSpec(CONF_HEAT_SETPOINT_C2, 1010, True, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_HEAT_REDUCED_SETPOINT_C2, 1012, False, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_COOL_MODE_C2, 1201, True, ("select",), GROUP_COMMANDS),
    ParameterSpec(CONF_COOL_SETPOINT_C2, 1202, True, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_COOL_REDUCED_SETPOINT_C2, 1203, False, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_DHW_MODE, 1600, False, ("select",), GROUP_COMMANDS),
    ParameterSpec(CONF_DHW_NOMINAL_SETPOINT, 1610, False, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_DHW_REDUCED_SETPOINT, 1612, False, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_OVERRIDE_DURATION_C1, 10990, False, ("text", "number", "sensor"), GROUP_COMMANDS),
    ParameterSpec(CONF_OVERRIDE_OFFSET_C1, 10991, False, ("text", "number"), GROUP_COMMANDS),
    ParameterSpec(CONF_OVERRIDE_DURATION_C2, 10992, False, ("text", "number", "sensor"), GROUP_COMMANDS),
    ParameterSpec(CONF_OVERRIDE_OFFSET_C2, 10993, False, ("text", "number"), GROUP_COMMANDS),
)

STATE_PARAMETERS: Final[tuple[ParameterSpec, ...]] = (
    ParameterSpec(CONF_OVERRIDE_C1, 701, False, ("select", "sensor", "text", "number"), GROUP_STATES),
    ParameterSpec(CONF_OVERRIDE_C2, 1001, False, ("select", "sensor", "text", "number"), GROUP_STATES),
    ParameterSpec(CONF_HEAT_STATE_C1, 8000, False, ("sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_COOL_STATE_C1, 8004, False, ("sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_HEAT_STATE_C2, 8001, False, ("sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_COOL_STATE_C2, 8025, False, ("sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_DHW_STATE, 8003, False, ("sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_PAC_STATE, 8006, False, ("sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_COMPRESSOR_STATE, 8400, False, ("binary_sensor", "sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_DEFROST, 7728, False, ("binary_sensor", "sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_DHW_ELECTRIC_HEATER, 8821, False, ("binary_sensor", "sensor", "text"), GROUP_STATES),
    ParameterSpec(CONF_DHW_PUMP, 8820, False, ("binary_sensor", "sensor", "text"), GROUP_STATES),
)

MEASUREMENT_PARAMETERS: Final[tuple[ParameterSpec, ...]] = (
    ParameterSpec(CONF_ROOM_TEMP_C1, 8740, True, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_EFFECTIVE_SETPOINT_C1, 8741, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_HEAT_FLOW_TARGET_C1, 8744, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_ROOM_TEMP_C2, 8770, True, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_EFFECTIVE_SETPOINT_C2, 8771, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_HEAT_FLOW_TARGET_C2, 8774, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_DHW_TEMPERATURE, 8830, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_COMPRESSOR_MODULATION, 8413, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_ENERGY_TOTAL, 3113, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_FLOW_TEMP, 8412, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_RETURN_TEMP, 8410, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_TARGET_FLOW_TEMP, 8411, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_OUTDOOR_TEMP, 8700, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_COMPRESSOR_HOURS, 8450, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_COMPRESSOR_STARTS, 8451, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_COMPRESSOR_MIN_RUN, 2842, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_COMPRESSOR_MIN_OFF, 2843, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_COMPRESSOR_STARTS_MAX_RATE, 7072, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
    ParameterSpec(CONF_COMPRESSOR_STARTS_CURRENT_RATE, 7073, False, ("sensor", "text", "number"), GROUP_MEASUREMENTS),
)

PARAMETER_GROUPS: Final = {
    GROUP_COMMANDS: COMMAND_PARAMETERS,
    GROUP_STATES: STATE_PARAMETERS,
    GROUP_MEASUREMENTS: MEASUREMENT_PARAMETERS,
}

PARAMETER_SPECS: Final[tuple[ParameterSpec, ...]] = (
    *COMMAND_PARAMETERS,
    *STATE_PARAMETERS,
    *MEASUREMENT_PARAMETERS,
)
SPEC_BY_KEY: Final = {spec.key: spec for spec in PARAMETER_SPECS}
SPEC_BY_PARAMETER: Final = {spec.parameter: spec for spec in PARAMETER_SPECS}
REQUIRED_KEYS: Final = tuple(spec.key for spec in PARAMETER_SPECS if spec.required)
