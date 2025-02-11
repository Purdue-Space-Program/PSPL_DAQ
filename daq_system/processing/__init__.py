"""
Data processing modules for different types of inputs and outputs.
"""

from .analog import process_analog_input
from .digital import process_digital_input, process_digital_output
from .channel_factory import ChannelFactory

__all__ = [
    "process_analog_input",
    "process_digital_input",
    "process_digital_output",
    "ChannelFactory",
]
