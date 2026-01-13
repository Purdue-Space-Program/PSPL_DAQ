from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class DAQConfig:
    """Configuration settings for DAQ system"""

    sample_rate: int = 100  # Hz
    stream_rate: int = 10  # Hz
    host: str = "192.168.2.147"
    port: int = 9090
    username: str = "Bill"
    password: str = "Bill"


@dataclass
class DeviceWiringPaths:
    """Paths to wiring configuration files for a device"""

    data_wiring: Path
    control_wiring: Path


# Default device configurations
DEFAULT_DEVICE_PATHS: Dict[str, DeviceWiringPaths] = {
    "Dev5": DeviceWiringPaths(
        data_wiring=Path("daq_system/inputs/CMS_Master_Data_Wiring_Dev5.xlsx"),
        control_wiring=Path("daq_system/inputs/CMS_Master_Control_Wiring_Dev5.xlsx"),
    #     #data_wiring=Path("daq_system/inputs/CMS_Mapping_Data_Wiring_Dev5.xlsx"),   # This contains all channels
    #     #control_wiring=Path("daq_system/inputs/CMS_Mapping_Control_Wiring_Dev5.xlsx"),   # This contains all channels
    ),
    "Dev6": DeviceWiringPaths(
         data_wiring=Path("daq_system/inputs/CMS_Master_Data_Wiring_Dev6.xlsx"),
         control_wiring=Path("daq_system/inputs/CMS_Master_Control_Wiring_Dev6.xlsx"),
         # data_wiring=Path(
         #     "daq_system/inputs/CMS_Mapping_Data_Wiring_Dev6.xlsx"
         # ),  # This contains all channels
         # control_wiring=Path(
         #     "daq_system/inputs/CMS_Mapping_Control_Wiring_Dev6.xlsx"
         # ),  # This contains all channels
     ),
}
