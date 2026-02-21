"""Platform for Schneider Energy."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_INTERNAL_URL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import CONF_CLIENT, DOMAIN, UniqueIdVersion
from .device_features import FeatureClass
from .entity_base import (
    GatewayEntity,
    WirelessDeviceEntity,
    async_setup_entities,
    gateway_device_info,
)
from .schneider_modbus import (
    LineVoltage,
    Phase,
    PowerFactorSignConvention,
    SchneiderModbus,
    TypeOfGateway,
)
from .coordinator import PowerTagCoordinator

PLATFORMS: list[str] = ["sensor"]

_LOGGER = logging.getLogger(__name__)


def list_sensors() -> list[type[WirelessDeviceEntity]]:
    return [
        PowerTagTotalActiveEnergy,
        PowerTagReactivePower,
        PowerTagReactivePowerPerPhase,
        PowerTagApparentPower,
        PowerTagApparentPowerPerPhase,
        PowerTagPowerFactor,
        PowerTagPowerFactorPerPhase,
        PowerTagPartialActiveEnergyDelivered,
        PowerTagTotalActiveEnergyDelivered,
        PowerTagPartialActiveEnergyDeliveredPerPhase,
        PowerTagTotalActiveEnergyDeliveredPerPhase,
        PowerTagPartialActiveEnergyReceived,
        PowerTagTotalActiveEnergyReceived,
        PowerTagPartialActiveEnergyReceivedPerPhase,
        PowerTagTotalActiveEnergyReceivedPerPhase,
        PowerTagPartialActiveEnergyDeliveredAndReceived,
        PowerTagPartialReactiveEnergyDelivered,
        PowerTagTotalReactiveEnergyDelivered,
        PowerTagPartialReactiveEnergyDeliveredPerPhase,
        PowerTagTotalReactiveEnergyDeliveredPerPhase,
        PowerTagPartialReactiveEnergyReceived,
        PowerTagTotalReactiveEnergyReceived,
        PowerTagPartialReactiveEnergyReceivedPerPhase,
        PowerTagTotalReactiveEnergyReceivedPerPhase,
        PowerTagPartialApparentEnergy,
        PowerTagTotalApparentEnergy,
        PowerTagPartialApparentEnergyPerPhase,
        PowerTagTotalApparentEnergyPerPhase,
        PowerTagCurrent,
        PowerTagCurrentNeutral,
        PowerTagVoltage,
        PowerTagFrequency,
        PowerTagTemperature,
        PowerTagActivePower,
        PowerTagActivePowerPerPhase,
        PowerTagDemandActivePower,
        EnvTagBatteryVoltage,
        EnvTagTemperature,
        EnvTagHumidity,
        EnvTagCO2,
        DeviceRssiTag,
        DeviceRssiGateway,
        DeviceLqiTag,
        DeviceLqiGateway,
        DevicePerTag,
        DevicePerGateway,
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PowerTag Link Gateway from a config entry."""
    sensors = list_sensors()
    entities = await async_setup_entities(hass, config_entry, sensors)

    data = hass.data[DOMAIN][config_entry.entry_id]
    presentation_url = data[CONF_INTERNAL_URL]
    client = data[CONF_CLIENT]
    coordinator = data["coordinator"]
    gateway_device = await gateway_device_info(client, presentation_url)
    gateway_serial = await client.serial_number()

    entities.extend(
        [
            GatewayTime(coordinator, client, gateway_device, gateway_serial),
        ]
    )

    async_add_entities(entities, update_before_add=False)


class GatewayTime(GatewayEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self, coordinator: PowerTagCoordinator, client: SchneiderModbus, tag_device: DeviceInfo, serial_number: str
    ):
        super().__init__(coordinator, client, tag_device, "datetime", serial_number)

    @callback
    def _handle_coordinator_update(self) -> None:
        raw_date = self.coordinator.data.gateway_data.date_time
        if self._handle_availability(raw_date):
            self._attr_native_value = dt_util.as_utc(raw_date)
        self.async_write_ha_state()

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalActiveEnergy(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "total active energy",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_active_delivered_plus_received_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagReactivePower(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.REACTIVE_POWER
    _attr_native_unit_of_measurement = "var"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "reactive power",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.reactive_power_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagReactivePowerPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.REACTIVE_POWER
    _attr_native_unit_of_measurement = "var"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"reactive power phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.reactive_power_a
            elif self.__phase == Phase.B:
                value = data.reactive_power_b
            elif self.__phase == Phase.C:
                value = data.reactive_power_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagApparentPower(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "apparent power",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.apparent_power_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagApparentPowerPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_native_unit_of_measurement = "VA"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"apparent power phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.apparent_power_a
            elif self.__phase == Phase.B:
                value = data.apparent_power_b
            elif self.__phase == Phase.C:
                value = data.apparent_power_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPowerFactor(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        feature_class: FeatureClass,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "power factor",
            unique_id_version,
            serial_number,
        )
        self._feature_class = feature_class
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        if self._feature_class == FeatureClass.R1:
            # This one is tricky as it's a one-time read, maybe keep it direct or move to coordinator if needed repeatedly?
            # For now keeping it direct as it seems static configuration
            convention = await self._client.tag_power_factor_sign_convention(
                self._modbus_index
            )
            if convention != PowerFactorSignConvention.INVALID:
                self._attr_extra_state_attributes = {
                    "Power factor sign convention": convention
                }

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            power_factor = data.power_factor_total
            if self._handle_availability(power_factor):
                self._attr_native_value = power_factor * 100
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPowerFactorPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"power factor phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        convention = await self._client.tag_power_factor_sign_convention(
            self._modbus_index
        )
        if convention != PowerFactorSignConvention.INVALID:
            self._attr_extra_state_attributes = {
                "Power factor sign convention": convention
            }

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            power_factor = None
            if self.__phase == Phase.A:
                power_factor = data.power_factor_a
            elif self.__phase == Phase.B:
                power_factor = data.power_factor_b
            elif self.__phase == Phase.C:
                power_factor = data.power_factor_c

            if self._handle_availability(power_factor):
                self._attr_native_value = power_factor * 100
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialActiveEnergyDelivered(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "partial active energy delivered",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_active_delivered_partial
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalActiveEnergyDelivered(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "total active energy delivered",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_active_delivered_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialActiveEnergyDeliveredPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"partial active energy delivered phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_active_delivered_partial_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_active_delivered_partial_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_active_delivered_partial_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            # Assumption, documentation actually doesn't list these.
            FeatureClass.A1,
            FeatureClass.F1,
            FeatureClass.F3,
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalActiveEnergyDeliveredPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"total active energy delivered phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_active_delivered_total_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_active_delivered_total_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_active_delivered_total_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            # Assumption, documentation actually doesn't list these.
            FeatureClass.A1,
            FeatureClass.F1,
            FeatureClass.F3,
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialActiveEnergyReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "partial active energy received",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_active_received_partial
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalActiveEnergyReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "total active energy received",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_active_received_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialActiveEnergyReceivedPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"partial active energy received phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_active_received_partial_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_active_received_partial_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_active_received_partial_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            # Assumption, documentation actually doesn't list these.
            FeatureClass.A1,
            FeatureClass.F1,
            FeatureClass.F3,
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalActiveEnergyReceivedPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"total active energy received phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_active_received_total_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_active_received_total_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_active_received_total_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            # Assumption, documentation actually doesn't list these.
            FeatureClass.A1,
            FeatureClass.F1,
            FeatureClass.F3,
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialActiveEnergyDeliveredAndReceived(
    WirelessDeviceEntity, SensorEntity
):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "partial energy delivered and received",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_active_delivered_plus_received_partial
            if self._handle_availability(value):
                self._attr_native_value = value

            last_reset = data.load_operating_time_start
            if self._handle_availability(value):
                self._attr_last_reset = last_reset
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialReactiveEnergyDelivered(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = "reactive_energy"
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "partial reactive energy delivered",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_reactive_delivered_partial
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalReactiveEnergyDelivered(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = "reactive_energy"
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "total reactive energy delivered",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_reactive_delivered_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialReactiveEnergyDeliveredPerPhase(
    WirelessDeviceEntity, SensorEntity
):
    _attr_device_class = "reactive_energy"
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"partial reactive energy delivered phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_reactive_delivered_partial_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_reactive_delivered_partial_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_reactive_delivered_partial_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalReactiveEnergyDeliveredPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = "reactive_energy"
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"total reactive energy delivered phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_reactive_delivered_total_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_reactive_delivered_total_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_reactive_delivered_total_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialReactiveEnergyReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = "reactive_energy"
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "partial reactive energy received",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_reactive_received_partial
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalReactiveEnergyReceived(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = "reactive_energy"
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "total reactive energy received",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_reactive_received_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            # Documentation implies only the resettable variant would exist, not this one. Wtf?
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialReactiveEnergyReceivedPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = "reactive_energy"
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"partial reactive energy received phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_reactive_received_partial_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_reactive_received_partial_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_reactive_received_partial_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalReactiveEnergyReceivedPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = "reactive_energy"
    _attr_native_unit_of_measurement = "VARh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"total reactive energy received phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_reactive_received_total_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_reactive_received_total_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_reactive_received_total_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            # Assumption, documentation actually doesn't list these.
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialApparentEnergy(WirelessDeviceEntity, SensorEntity):
    # TODO APPARENT_ENERGY maybe?
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "partial apparent energy",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_apparent_partial
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalApparentEnergy(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "total apparent energy",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.energy_apparent_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagPartialApparentEnergyPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"partial apparent energy phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_apparent_partial_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_apparent_partial_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_apparent_partial_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTotalApparentEnergyPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "VAh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"total apparent energy phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.energy_apparent_total_phase_a
            elif self.__phase == Phase.B:
                value = data.energy_apparent_total_phase_b
            elif self.__phase == Phase.C:
                value = data.energy_apparent_total_phase_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagCurrent(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = "A"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"current {phase.name}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        self._attr_extra_state_attributes = {
            "Rated current": await self._client.tag_rated_current(self._modbus_index)
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.current_a
            elif self.__phase == Phase.B:
                value = data.current_b
            elif self.__phase == Phase.C:
                value = data.current_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagCurrentNeutral(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = "A"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "current neutral",
            unique_id_version,
            serial_number,
        )

        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        self._attr_extra_state_attributes = {
            "Rated current": await self._client.tag_rated_current(self._modbus_index)
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.current_neutral
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.FL, FeatureClass.R1]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagVoltage(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        line: LineVoltage,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"voltage {line.name}",
            unique_id_version,
            serial_number,
        )
        self.__line = line
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        rated_voltage = await self._client.tag_rated_voltage(self._modbus_index)

        if rated_voltage:
            self._attr_extra_state_attributes = {"Rated voltage": rated_voltage}

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__line == LineVoltage.A_B:
                value = data.voltage_ab
            elif self.__line == LineVoltage.B_C:
                value = data.voltage_bc
            elif self.__line == LineVoltage.C_A:
                value = data.voltage_ca
            elif self.__line == LineVoltage.A_N:
                value = data.voltage_an
            elif self.__line == LineVoltage.B_N:
                value = data.voltage_bn
            elif self.__line == LineVoltage.C_N:
                value = data.voltage_cn

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagFrequency(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_native_unit_of_measurement = "Hz"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "frequency",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.frequency
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagTemperature(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "temperature",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.device_temperature
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        """
        The documentation says that A1, A2, P1, F1, F2 and F3 do not support internal temperature.
        However, they do seem to report temperature values, so let's use them. Let's not tell Schneider about this. ;)
        """
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]

    @staticmethod
    def supports_firmware_version(firmware_version: str) -> bool:
        import re

        major_version = re.sub(r"[^0-9.]", "", firmware_version).split(".")[0]
        return int(major_version) >= 4


class PowerTagActivePower(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "active power",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.active_power_total
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagActivePowerPerPhase(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        phase: Phase,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            f"active power phase {phase}",
            unique_id_version,
            serial_number,
        )
        self.__phase = phase

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = None
            if self.__phase == Phase.A:
                value = data.active_power_a
            elif self.__phase == Phase.B:
                value = data.active_power_b
            elif self.__phase == Phase.C:
                value = data.active_power_c

            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A1, # Duplicate?
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class PowerTagDemandActivePower(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "demand active power",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.power_active_demand_total
            if self._handle_availability(value):
                self._attr_native_value = value

            self._attr_extra_state_attributes = {
                "Maximum demand active power (W)": data.power_active_power_demand_total_maximum,
                "Maximum demand active power timestamp": data.power_active_demand_total_maximum_timestamp,
            }
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.C]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.SMARTLINK,
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class EnvTagBatteryVoltage(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "battery voltage",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.env_battery_voltage
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


class EnvTagTemperature(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "temperature",
            unique_id_version,
            serial_number,
        )
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._attr_extra_state_attributes = {
            "Minimum measurable temperature (°C)": await self._client.env_temperature_minimum(
                self._modbus_index
            ),
            "Maximum measurable temperature (°C)": await self._client.env_temperature_maximum(
                self._modbus_index
            ),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.env_temperature
            if self._handle_availability(value):
                self._attr_native_value = value
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.TEMP0,
            FeatureClass.TEMP1,
            FeatureClass.CO2,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


class EnvTagHumidity(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "humidity",
            unique_id_version,
            serial_number,
        )
        self._client = client
        self._modbus_index = modbus_index
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._attr_extra_state_attributes = {
            "Minimum measurable humidity (%)": (
                await self._client.env_humidity_minimum(self._modbus_index) or 0
            )
            * 100,
            "Maximum measurable humidity (%)": (
                await self._client.env_humidity_maximum(self._modbus_index) or 0
            )
            * 100,
        }
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.env_humidity
            if self._handle_availability(value):
                self._attr_native_value = value * 100
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


class EnvTagCO2(WirelessDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.CO2
    _attr_native_unit_of_measurement = "ppm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator, client, modbus_index, tag_device, "CO2", unique_id_version, serial_number
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.env_co2
            if self._handle_availability(value):
                self._attr_native_value = value * 1000
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.PANEL_SERVER]


class DeviceRssiTag(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "RSSI in tag",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.radio_rssi_inside_tag
            if self._handle_availability(value):
                self._attr_native_value = value

            self._attr_extra_state_attributes = {
                "Minimum": data.radio_rssi_minimum
            }
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
            FeatureClass.TEMP0,
            FeatureClass.TEMP1,
            FeatureClass.CO2,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class DeviceRssiGateway(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "RSSI in gateway",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.radio_rssi_inside_gateway
            if self._handle_availability(value):
                self._attr_native_value = value

            self._attr_extra_state_attributes = {
                "Minimum": data.radio_rssi_minimum
            }
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
            FeatureClass.TEMP0,
            FeatureClass.TEMP1,
            FeatureClass.CO2,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class DeviceLqiTag(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "LQI in tag",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.radio_lqi_tag
            if self._handle_availability(value):
                self._attr_native_value = value

            self._attr_extra_state_attributes = {
                "Minimum": data.radio_lqi_minimum
            }
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
            FeatureClass.TEMP0,
            FeatureClass.TEMP1,
            FeatureClass.CO2,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class DeviceLqiGateway(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "LQI in gateway",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.radio_lqi_gateway
            if self._handle_availability(value):
                self._attr_native_value = value

            self._attr_extra_state_attributes = {
                "Minimum": data.radio_lqi_minimum
            }
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
            FeatureClass.TEMP0,
            FeatureClass.TEMP1,
            FeatureClass.CO2,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class DevicePerTag(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PowerTagCoordinator,
        client: SchneiderModbus,
        modbus_index: int,
        tag_device: DeviceInfo,
        unique_id_version: UniqueIdVersion,
        serial_number: str,
    ):
        super().__init__(
            coordinator,
            client,
            modbus_index,
            tag_device,
            "packet error rate in tag",
            unique_id_version,
            serial_number,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.radio_per_tag
            if self._handle_availability(value):
                self._attr_native_value = value

            self._attr_extra_state_attributes = {
                "Maximum": data.radio_per_maximum
            }
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [
            FeatureClass.A1,
            FeatureClass.A2,
            FeatureClass.P1,
            FeatureClass.F1,
            FeatureClass.F2,
            FeatureClass.F3,
            FeatureClass.FL,
            FeatureClass.M0,
            FeatureClass.M1,
            FeatureClass.M2,
            FeatureClass.M3,
            FeatureClass.R1,
            FeatureClass.C,
            FeatureClass.TEMP0,
            FeatureClass.TEMP1,
            FeatureClass.CO2,
        ]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [
            TypeOfGateway.POWERTAG_LINK,
            TypeOfGateway.PANEL_SERVER,
        ]


class DevicePerGateway(WirelessDeviceEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PowerTagCoordinator, client: SchneiderModbus, modbus_index: int, tag_device: DeviceInfo, unique_id_version: UniqueIdVersion, serial_number: str):
        super().__init__(coordinator, client, modbus_index, tag_device, "packet error rate in gateway", unique_id_version, serial_number)

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.devices_data.get(self._modbus_index)
        if data:
            value = data.radio_per_gateway
            if self._handle_availability(value):
                self._attr_native_value = value
            self._attr_extra_state_attributes = {
                "Maximum": data.radio_per_maximum
            }
        self.async_write_ha_state()

    @staticmethod
    def supports_feature_set(feature_class: FeatureClass) -> bool:
        return feature_class in [FeatureClass.A1, FeatureClass.A2, FeatureClass.P1, FeatureClass.F1, FeatureClass.F2,
                                 FeatureClass.F3, FeatureClass.FL, FeatureClass.M0, FeatureClass.M1, FeatureClass.M2,
                                 FeatureClass.M3, FeatureClass.R1, FeatureClass.C,
                                 FeatureClass.TEMP0, FeatureClass.TEMP1, FeatureClass.CO2]

    @staticmethod
    def supports_gateway(type_of_gateway: TypeOfGateway) -> bool:
        return type_of_gateway in [TypeOfGateway.POWERTAG_LINK, TypeOfGateway.PANEL_SERVER]
