from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .schneider_modbus import SchneiderModbus, GATEWAY_SLAVE_ID, TypeOfGateway
from .device_features import FeatureClass, from_wireless_device_type_code, from_commercial_reference, UnknownDevice
from .coordinator_data import CoordinatorData

_LOGGER = logging.getLogger(__name__)


class PowerTagCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Coordinator to manage fetching data from the PowerTag Gateway."""

    def __init__(self, hass: HomeAssistant, client: SchneiderModbus) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self.monitored_devices: dict[int, FeatureClass] = {}

    def add_device(self, slave_id: int, feature_class: FeatureClass):
        """Add a device to be monitored by the coordinator."""
        self.monitored_devices[slave_id] = feature_class

    async def async_discover_devices(self):
        """Discover devices on the gateway and register them."""
        _LOGGER.debug("Starting to scan for devices...")
        for i in range(1, 100):
            modbus_address = await self.client.modbus_address_of_node(i)
            _LOGGER.debug(f"Found device #{i} at address {modbus_address}")

            if modbus_address is None:
                if self.client.type_of_gateway == TypeOfGateway.PANEL_SERVER:
                    # PanelServers can have out of order devices, so make sure to just scan everything
                    continue
                else:
                    break

            feature_class = None
            if self.client.type_of_gateway == TypeOfGateway.SMARTLINK:
                identifier = await self.client.tag_product_identifier(modbus_address)
                if identifier is None:
                    break

                _LOGGER.debug(
                    f"Found device #{modbus_address} to have product wireless device type code {identifier}"
                )

                try:
                    feature_class = from_wireless_device_type_code(identifier)
                except UnknownDevice:
                    _LOGGER.error(
                        f"I don't know what this product identifier is: {identifier}, but we can fix this! :) "
                        f"Please create a GitHub issue and tell me model of the {modbus_address}th wireless "
                        f"device."
                    )
                    continue

            else:
                commercial_reference = await self.client.tag_product_code(modbus_address)

                _LOGGER.debug(f"Device #{modbus_address} is {commercial_reference}")

                try:
                    feature_class = from_commercial_reference(commercial_reference)
                except UnknownDevice:
                    _LOGGER.error(
                        f"Unsupported wireless device: {commercial_reference}, "
                        f"to request support, please create a GitHub issue for this device."
                    )
                    continue

            if self.client.type_of_gateway is not TypeOfGateway.SMARTLINK:
                # Basic reachability check using cached data if possible, but during discovery we might need a live check
                # or just proceed. The original code checked LQI here.
                # To avoid individual reads, maybe we can skip this check or do it during update?
                # For now, keeping original logic but it adds reads.
                # Ideally discovery happens once at startup.
                is_disabled = await self.client.tag_radio_lqi_gateway(modbus_address) is None
                if is_disabled:
                    _LOGGER.warning(
                        f"The device {await self.client.tag_name(modbus_address)} is not reachable; will ignore this one."
                    )
                    continue

            self.add_device(modbus_address, feature_class)
            _LOGGER.info(f"Discovered device at address {modbus_address} with feature class {feature_class}")

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from the API."""
        data = CoordinatorData()

        try:
            # Fetch gateway data
            data.gateway_data = await self.client.async_read_metrics(GATEWAY_SLAVE_ID, FeatureClass.C)

            # Fetch data for all monitored devices
            for slave_id, feature_class in self.monitored_devices.items():
                device_data = await self.client.async_read_metrics(slave_id, feature_class)
                data.devices_data[slave_id] = device_data

            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
