import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util
from datetime import datetime, timezone

from custom_components.powertag_gateway.coordinator import PowerTagCoordinator
from custom_components.powertag_gateway.schneider_modbus import SchneiderModbus, LinkStatus, Phase, LineVoltage
from custom_components.powertag_gateway.device_features import FeatureClass
from custom_components.powertag_gateway.data_models import PowerTagData
from custom_components.powertag_gateway.coordinator_data import CoordinatorData
from custom_components.powertag_gateway.sensor import (
    PowerTagTotalActiveEnergy,
    PowerTagActivePower,
    PowerTagVoltage,
    PowerTagCurrent,
    GatewayTime,
    list_sensors
)
from custom_components.powertag_gateway import UniqueIdVersion

@pytest.fixture
def mock_coordinator(hass):
    client = MagicMock(spec=SchneiderModbus)
    coordinator = PowerTagCoordinator(hass, client)
    coordinator.data = CoordinatorData()
    return coordinator

@pytest.fixture
def mock_device_info():
    return DeviceInfo(
        identifiers={("powertag_gateway", "test_serial")},
        name="Test Device",
        manufacturer="Schneider",
        model="PowerTag",
        sw_version="1.0.0"
    )

@pytest.mark.asyncio
async def test_gateway_time_sensor(hass: HomeAssistant, mock_coordinator, mock_device_info):
    mock_client = mock_coordinator.client
    sensor = GatewayTime(mock_coordinator, mock_client, mock_device_info, "gateway_serial")
    sensor.hass = hass
    sensor.entity_id = "sensor.gateway_time"

    now = datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    mock_coordinator.data.gateway_data.date_time = now

    sensor._handle_coordinator_update()

    assert sensor.native_value == now

@pytest.mark.asyncio
async def test_powertag_total_active_energy(hass: HomeAssistant, mock_coordinator, mock_device_info):
    modbus_index = 1
    sensor = PowerTagTotalActiveEnergy(
        mock_coordinator,
        mock_coordinator.client,
        modbus_index,
        mock_device_info,
        UniqueIdVersion.V0,
        "serial123"
    )
    sensor.hass = hass
    sensor.entity_id = "sensor.total_active_energy"

    mock_coordinator.data.devices_data[modbus_index] = PowerTagData(
        energy_active_delivered_plus_received_total=12345
    )

    sensor._handle_coordinator_update()

    assert sensor.native_value == 12345

@pytest.mark.asyncio
async def test_powertag_active_power(hass: HomeAssistant, mock_coordinator, mock_device_info):
    modbus_index = 2
    sensor = PowerTagActivePower(
        mock_coordinator,
        mock_coordinator.client,
        modbus_index,
        mock_device_info,
        UniqueIdVersion.V0,
        "serial123"
    )
    sensor.hass = hass
    sensor.entity_id = "sensor.active_power"

    mock_coordinator.data.devices_data[modbus_index] = PowerTagData(
        active_power_total=500.5
    )

    sensor._handle_coordinator_update()

    assert sensor.native_value == 500.5

@pytest.mark.asyncio
async def test_powertag_voltage(hass: HomeAssistant, mock_coordinator, mock_device_info):
    modbus_index = 3
    # Test LineVoltage.A_N
    sensor = PowerTagVoltage(
        mock_coordinator,
        mock_coordinator.client,
        modbus_index,
        mock_device_info,
        LineVoltage.A_N,
        UniqueIdVersion.V0,
        "serial123"
    )
    sensor.hass = hass
    sensor.entity_id = "sensor.voltage"

    mock_coordinator.data.devices_data[modbus_index] = PowerTagData(
        voltage_an=230.1
    )

    sensor._handle_coordinator_update()

    assert sensor.native_value == 230.1

@pytest.mark.asyncio
async def test_powertag_current(hass: HomeAssistant, mock_coordinator, mock_device_info):
    modbus_index = 4
    # Test Phase A
    sensor = PowerTagCurrent(
        mock_coordinator,
        mock_coordinator.client,
        modbus_index,
        mock_device_info,
        Phase.A,
        UniqueIdVersion.V0,
        "serial123"
    )
    sensor.hass = hass
    sensor.entity_id = "sensor.current"

    mock_coordinator.data.devices_data[modbus_index] = PowerTagData(
        current_a=10.5
    )

    sensor._handle_coordinator_update()

    assert sensor.native_value == 10.5

@pytest.mark.asyncio
async def test_sensor_availability(hass: HomeAssistant, mock_coordinator, mock_device_info):
    modbus_index = 5
    sensor = PowerTagActivePower(
        mock_coordinator,
        mock_coordinator.client,
        modbus_index,
        mock_device_info,
        UniqueIdVersion.V0,
        "serial123"
    )
    sensor.hass = hass
    sensor.entity_id = "sensor.active_power_avail"

    # Simulate missing data (None)
    mock_coordinator.data.devices_data[modbus_index] = PowerTagData(
        active_power_total=None
    )

    sensor._handle_coordinator_update()

    assert sensor.available is False
    assert sensor.native_value is None

    # Simulate valid data
    mock_coordinator.data.devices_data[modbus_index] = PowerTagData(
        active_power_total=100.0
    )

    sensor._handle_coordinator_update()

    assert sensor.available is True
    assert sensor.native_value == 100.0
