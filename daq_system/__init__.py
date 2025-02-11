"""
DAQ System package for handling data acquisition tasks.
"""
from .core.daq_system import DAQSystem
from .config.settings import DAQConfig, DeviceWiringPaths

__version__ = "1.0.0"
__all__ = ['DAQSystem', 'DAQConfig', 'DeviceWiringPaths']
