from dataclasses import dataclass, field
from .schneider_modbus import SchneiderModbus
from .device_features import FeatureClass
from .data_models import PowerTagData

@dataclass
class CoordinatorData:
    gateway_data: PowerTagData = field(default_factory=PowerTagData)
    devices_data: dict[int, PowerTagData] = field(default_factory=dict)
