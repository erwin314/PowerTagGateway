from dataclasses import dataclass
from datetime import datetime

from .schneider_modbus import (
    AlarmDetails,
    LinkStatus,
    PanelHealth,
    Phase,
    LineVoltage,
    PowerFactorSignConvention,
)


@dataclass
class PowerTagData:
    # Status
    status: LinkStatus | None = None
    health: PanelHealth | None = None

    # Date and Time
    date_time: datetime | None = None

    # Current Metering Data
    current_a: float | None = None
    current_b: float | None = None
    current_c: float | None = None
    current_neutral: float | None = None

    # Voltage Metering Data
    voltage_ab: float | None = None
    voltage_bc: float | None = None
    voltage_ca: float | None = None
    voltage_an: float | None = None
    voltage_bn: float | None = None
    voltage_cn: float | None = None

    # Power Metering Data
    active_power_a: float | None = None
    active_power_b: float | None = None
    active_power_c: float | None = None
    active_power_total: float | None = None

    reactive_power_a: float | None = None
    reactive_power_b: float | None = None
    reactive_power_c: float | None = None
    reactive_power_total: float | None = None

    apparent_power_a: float | None = None
    apparent_power_b: float | None = None
    apparent_power_c: float | None = None
    apparent_power_total: float | None = None

    # Power Factor Metering Data
    power_factor_a: float | None = None
    power_factor_b: float | None = None
    power_factor_c: float | None = None
    power_factor_total: float | None = None
    power_factor_sign_convention: PowerFactorSignConvention | None = None

    # Frequency Metering Data
    frequency: float | None = None

    # Device Temperature Metering Data
    device_temperature: float | None = None

    # Energy Data – Legacy Zone (Non-resettable / Resettable)
    energy_active_delivered_plus_received_total: int | None = None
    energy_active_delivered_plus_received_partial: int | None = None

    # Energy Data – New Zone (Resettable)
    energy_active_delivered_partial: int | None = None
    energy_active_received_partial: int | None = None
    energy_reactive_delivered_partial: int | None = None
    energy_reactive_received_partial: int | None = None
    energy_apparent_partial: int | None = None

    energy_active_delivered_partial_phase_a: int | None = None
    energy_active_delivered_partial_phase_b: int | None = None
    energy_active_delivered_partial_phase_c: int | None = None

    energy_active_received_partial_phase_a: int | None = None
    energy_active_received_partial_phase_b: int | None = None
    energy_active_received_partial_phase_c: int | None = None

    energy_reactive_delivered_partial_phase_a: int | None = None
    energy_reactive_delivered_partial_phase_b: int | None = None
    energy_reactive_delivered_partial_phase_c: int | None = None

    energy_reactive_received_partial_phase_a: int | None = None
    energy_reactive_received_partial_phase_b: int | None = None
    energy_reactive_received_partial_phase_c: int | None = None

    energy_apparent_partial_phase_a: int | None = None
    energy_apparent_partial_phase_b: int | None = None
    energy_apparent_partial_phase_c: int | None = None

    # Energy Data – New Zone (Not Resettable)
    energy_active_delivered_total: int | None = None
    energy_active_received_total: int | None = None
    energy_reactive_delivered_total: int | None = None
    energy_reactive_received_total: int | None = None
    energy_apparent_total: int | None = None

    energy_active_delivered_total_phase_a: int | None = None
    energy_active_delivered_total_phase_b: int | None = None
    energy_active_delivered_total_phase_c: int | None = None

    energy_active_received_total_phase_a: int | None = None
    energy_active_received_total_phase_b: int | None = None
    energy_active_received_total_phase_c: int | None = None

    energy_reactive_delivered_total_phase_a: int | None = None
    energy_reactive_delivered_total_phase_b: int | None = None
    energy_reactive_delivered_total_phase_c: int | None = None

    energy_reactive_received_total_phase_a: int | None = None
    energy_reactive_received_total_phase_b: int | None = None
    energy_reactive_received_total_phase_c: int | None = None

    energy_apparent_total_phase_a: int | None = None
    energy_apparent_total_phase_b: int | None = None
    energy_apparent_total_phase_c: int | None = None

    # Power Demand Data
    power_active_demand_total: float | None = None
    power_active_power_demand_total_maximum: float | None = None
    power_active_demand_total_maximum_timestamp: datetime | None = None

    # Alarm
    alarm_valid: bool | None = None
    alarm: AlarmDetails | None = None
    current_at_voltage_loss_a: float | None = None
    current_at_voltage_loss_b: float | None = None
    current_at_voltage_loss_c: float | None = None

    # Load Operating Time
    load_operating_time: int | None = None
    load_operating_time_active_power_threshold: float | None = None
    load_operating_time_start: datetime | None = None

    # Diagnostic Data Registers
    radio_communication_valid: bool | None = None
    wireless_communication_valid: bool | None = None
    radio_per_tag: float | None = None
    radio_rssi_inside_tag: float | None = None
    radio_lqi_tag: int | None = None
    radio_per_gateway: float | None = None
    radio_rssi_inside_gateway: float | None = None
    radio_lqi_gateway: float | None = None
    radio_per_maximum: float | None = None
    radio_rssi_minimum: float | None = None
    radio_lqi_minimum: float | None = None

    # Environmental sensors
    env_battery_voltage: float | None = None
    env_temperature: float | None = None
    env_temperature_maximum: float | None = None
    env_temperature_minimum: float | None = None
    env_humidity: float | None = None
    env_humidity_maximum: float | None = None
    env_humidity_minimum: float | None = None
    env_co2: float | None = None
