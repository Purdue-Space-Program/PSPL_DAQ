"""
Utility functions and classes for the DAQ system.
"""

from .exceptions import (
    DAQError,
    ConnectionError,
    ConfigurationError,
    DeviceError,
    TaskError,
)

__all__ = [
    "DAQError",
    "ConnectionError",
    "ConfigurationError",
    "DeviceError",
    "TaskError",
]
