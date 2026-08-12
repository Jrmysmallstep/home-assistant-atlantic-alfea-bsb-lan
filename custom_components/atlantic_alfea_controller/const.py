"""Constants for Atlantic Alfea BSB-LAN."""

from typing import Final

DOMAIN: Final = "atlantic_alfea_controller"
PLATFORMS: Final = ["select", "number", "climate", "water_heater", "sensor", "binary_sensor", "button"]

CONF_CLOCK_DATETIME: Final = "clock_datetime"

CONF_HEAT_MODE_C1: Final = "heat_mode_c1"
CONF_HEAT_SETPOINT_C1: Final = "heat_setpoint_c1"
CONF_HEAT_REDUCED_SETPOINT_C1: Final = "heat_reduced_setpoint_c1"
CONF_COOL_MODE_C1: Final = "cool_mode_c1"
CONF_COOL_SETPOINT_C1: Final = "cool_setpoint_c1"
CONF_COOL_REDUCED_SETPOINT_C1: Final = "cool_reduced_setpoint_c1"
CONF_ROOM_TEMP_C1: Final = "room_temp_c1"
CONF_EFFECTIVE_SETPOINT_C1: Final = "effective_setpoint_c1"
CONF_HEAT_FLOW_TARGET_C1: Final = "heat_flow_target_c1"
CONF_HEAT_STATE_C1: Final = "heat_state_c1"
CONF_OVERRIDE_C1: Final = "override_c1"
CONF_OVERRIDE_OFFSET_C1: Final = "override_offset_c1"
CONF_OVERRIDE_DURATION_C1: Final = "override_duration_c1"
CONF_COOL_STATE_C1: Final = "cool_state_c1"

CONF_HEAT_MODE_C2: Final = "heat_mode_c2"
CONF_HEAT_SETPOINT_C2: Final = "heat_setpoint_c2"
CONF_HEAT_REDUCED_SETPOINT_C2: Final = "heat_reduced_setpoint_c2"
CONF_COOL_MODE_C2: Final = "cool_mode_c2"
CONF_COOL_SETPOINT_C2: Final = "cool_setpoint_c2"
CONF_COOL_REDUCED_SETPOINT_C2: Final = "cool_reduced_setpoint_c2"
CONF_ROOM_TEMP_C2: Final = "room_temp_c2"
CONF_EFFECTIVE_SETPOINT_C2: Final = "effective_setpoint_c2"
CONF_HEAT_FLOW_TARGET_C2: Final = "heat_flow_target_c2"
CONF_HEAT_STATE_C2: Final = "heat_state_c2"
CONF_OVERRIDE_C2: Final = "override_c2"
CONF_OVERRIDE_OFFSET_C2: Final = "override_offset_c2"
CONF_OVERRIDE_DURATION_C2: Final = "override_duration_c2"
CONF_COOL_STATE_C2: Final = "cool_state_c2"

CONF_DHW_MODE: Final = "dhw_mode"
CONF_DHW_NOMINAL_SETPOINT: Final = "dhw_nominal_setpoint"
CONF_DHW_REDUCED_SETPOINT: Final = "dhw_reduced_setpoint"
CONF_DHW_STATE: Final = "dhw_state"
CONF_DHW_TEMPERATURE: Final = "dhw_temperature"
CONF_DHW_ELECTRIC_HEATER: Final = "dhw_electric_heater"
CONF_DHW_PUMP: Final = "dhw_pump"

CONF_PAC_STATE: Final = "pac_state"
CONF_COMPRESSOR_STATE: Final = "compressor_state"
CONF_COMPRESSOR_MODULATION: Final = "compressor_modulation"
CONF_ENERGY_TOTAL: Final = "energy_total"
CONF_FLOW_TEMP: Final = "flow_temp"
CONF_RETURN_TEMP: Final = "return_temp"
CONF_TARGET_FLOW_TEMP: Final = "target_flow_temp"
CONF_OUTDOOR_TEMP: Final = "outdoor_temp"
CONF_DEFROST: Final = "defrost"
CONF_COMPRESSOR_HOURS: Final = "compressor_hours"
CONF_COMPRESSOR_STARTS: Final = "compressor_starts"
CONF_COMPRESSOR_MIN_RUN: Final = "compressor_min_run"
CONF_COMPRESSOR_MIN_OFF: Final = "compressor_min_off"
CONF_COMPRESSOR_STARTS_MAX_RATE: Final = "compressor_starts_max_rate"
CONF_COMPRESSOR_STARTS_CURRENT_RATE: Final = "compressor_starts_current_rate"

CONF_SHORT_CYCLE_MINUTES: Final = "short_cycle_minutes"
CONF_FREQUENT_STARTS_PER_HOUR: Final = "frequent_starts_per_hour"
CONF_FLOW_GAP_DEGREES: Final = "flow_gap_degrees"
CONF_FLOW_GAP_DURATION_MINUTES: Final = "flow_gap_duration_minutes"

DEFAULT_SHORT_CYCLE_MINUTES: Final = 5.0
DEFAULT_FREQUENT_STARTS_PER_HOUR: Final = 4
DEFAULT_FLOW_GAP_DEGREES: Final = 3.0
DEFAULT_FLOW_GAP_DURATION_MINUTES: Final = 15.0

CLOCK_DESYNC_THRESHOLD_SECONDS: Final = 120
CLOCK_SOURCE_STALE_SECONDS: Final = 4500
CLOCK_POLL_INTERVAL_SECONDS: Final = 3600
CLOCK_INITIAL_POLL_DELAY_SECONDS: Final = 30
CLOCK_POLL_TOPIC: Final = "BSB-LAN/poll"

# Read-only BSB refreshes. These do not alter regulator settings; they only
# request a fresh MQTT publication from BSB-LAN.
BSB_REFRESH_FAST_INTERVAL_SECONDS: Final = 300
BSB_REFRESH_SLOW_INTERVAL_SECONDS: Final = 900
BSB_REFRESH_INITIAL_DELAY_SECONDS: Final = 45
BSB_REFRESH_FAST_PARAMETERS: Final = (8411,)
BSB_REFRESH_SLOW_PARAMETERS: Final = (3113, 8450, 8451)

SHORT_CYCLES_PER_HOUR: Final = 2
SHORT_CYCLES_PER_SIX_HOURS: Final = 3

MODE_OFF: Final = "off"
MODE_HEAT: Final = "heat"
MODE_COOL: Final = "cool"

SELECT_OPTIONS: Final = ["Off", "Chauffage", "Refroidissement"]

BSB_PROTECTION: Final = "0 - Mode protection"
BSB_AUTO: Final = "1 - Automatique"

DHW_OFF: Final = "Arrêt"
DHW_ON: Final = "Marche"
DHW_ECO: Final = "Eco"
DHW_OPERATIONS: Final = [DHW_OFF, DHW_ON, DHW_ECO]

TEMPERATURE_STEP: Final = 0.5
