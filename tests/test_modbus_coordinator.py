from unittest.mock import MagicMock, AsyncMock, call
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.core import HomeAssistant
from custom_components.powertag_gateway.coordinator import PowerTagCoordinator
from custom_components.powertag_gateway.schneider_modbus import SchneiderModbus, GATEWAY_SLAVE_ID
from custom_components.powertag_gateway.device_features import FeatureClass
from custom_components.powertag_gateway.coordinator_data import CoordinatorData
from custom_components.powertag_gateway.data_models import PowerTagData
from custom_components.powertag_gateway.schneider_modbus import LinkStatus
import pytest

@pytest.mark.asyncio
async def test_coordinator_updates_data(hass: HomeAssistant):
    """Test that the coordinator fetches and stores data correctly."""
    mock_client = MagicMock(spec=SchneiderModbus)
    # Mock async_read_metrics to return dummy data
    mock_client.async_read_metrics = AsyncMock()

    gateway_data = PowerTagData(status=LinkStatus.OPERATING)
    device_data = PowerTagData(active_power_total=123.45)

    # First call for gateway, second for device 1
    mock_client.async_read_metrics.side_effect = [
        gateway_data, # For gateway
        device_data   # For device
    ]

    coordinator = PowerTagCoordinator(hass, mock_client)
    coordinator.add_device(1, FeatureClass.A1)

    await coordinator.async_refresh()

    assert coordinator.data.gateway_data == gateway_data
    assert coordinator.data.devices_data[1] == device_data

    assert mock_client.async_read_metrics.call_count == 2
    mock_client.async_read_metrics.assert_any_call(GATEWAY_SLAVE_ID, FeatureClass.C)
    mock_client.async_read_metrics.assert_any_call(1, FeatureClass.A1)

@pytest.mark.asyncio
async def test_modbus_bulk_read_calls(hass: HomeAssistant):
    """Test that async_read_metrics calls read_holding_registers (via private method) for bulk reading."""
    # We need to instantiate a real SchneiderModbus but with a mocked client to verify calls
    # However, SchneiderModbus.__init__ tries to connect. We can mock that.

    # Mocking pymodbus client
    mock_pymodbus_client = MagicMock()
    mock_pymodbus_client.connected = True

    # We can't easily instantiate SchneiderModbus without it trying to connect/logging.
    # Let's mock the class and just test the method logic if we can, or subclass it for testing.

    # Better approach: Instantiate SchneiderModbus with mocked params and swap the internal client
    client = SchneiderModbus("1.2.3.4", FeatureClass.A1) # Host doesn't matter if we mock client
    client.client = mock_pymodbus_client

    # Mock internal methods to avoid actual network calls and decoding logic dependencies for this test
    # We want to verify that async_read_metrics calls __async_read with expected ranges

    # Mocking _SchneiderModbus__async_read because it's name mangled

    # Helper to return a list of zeros for registers, but handle valid date for the date parsing part
    async def mock_async_read(address, count, slave_id):
        # Return a valid date-time struct for 0xCE1 block to avoid ValueError in datetime()
        # year_raw (offset 14) needs to be valid (e.g. 23 -> 2023)
        # month (offset 15) needs to be valid (e.g. 1)
        if address == 0xCE1:
            regs = [0] * 18
            regs[14] = 23 # Year 2023
            regs[15] = 1 | (1 << 8) # Day 1, Month 1
            regs[16] = 0 # Hour 0, Minute 0
            regs[17] = 0 # Second 0
            return regs
        return [0] * count

    client._SchneiderModbus__async_read = AsyncMock(side_effect=mock_async_read)

    # Mock specific tag methods that are still called individually
    client.tag_energy_active_delivered_plus_received_total = AsyncMock(return_value=100)
    client.tag_energy_active_delivered_plus_received_partial = AsyncMock(return_value=50)

    # Mock other dependent methods that might be called
    client.tag_power_active_demand_total = AsyncMock(return_value=0)
    client.tag_power_active_power_demand_total_maximum = AsyncMock(return_value=0)
    client.tag_power_active_demand_total_maximum_timestamp = AsyncMock(return_value=None)
    client.tag_get_alarm = AsyncMock(return_value=None)
    client.tag_current_at_voltage_loss = AsyncMock(return_value=0)
    client.tag_load_operating_time = AsyncMock(return_value=0)
    client.tag_load_operating_time_active_power_threshold = AsyncMock(return_value=0)
    client.tag_load_operating_time_start = AsyncMock(return_value=None)


    # Test reading metrics for a standard device (not gateway)
    slave_id = 1
    feature_class = FeatureClass.A1

    await client.async_read_metrics(slave_id, feature_class)

    # Verify bulk read calls
    # Block 1: 0xBB7, 74 registers
    client._SchneiderModbus__async_read.assert_any_call(0xBB7, 74, slave_id)

    # Block 2: 0xC01, 60 registers
    client._SchneiderModbus__async_read.assert_any_call(0xC01, 60, slave_id)

    # Check that individual tag methods that were replaced by bulk reads are NOT called
    # For example, tag_current is now read from block1
    # We can't easily check 'not called' on methods we didn't mock or wrap,
    # but we can check that __async_read was NOT called for individual register addresses
    # if we assume standard flow.

    # Let's ensure we didn't call __async_read for 0xBB7 with count 2 (individual current read)
    assert call(0xBB7, 2, slave_id) not in client._SchneiderModbus__async_read.call_args_list
