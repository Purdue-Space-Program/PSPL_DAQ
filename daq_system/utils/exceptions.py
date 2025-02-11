class DAQError(Exception):
    """Base exception for DAQ system errors"""
    pass

class ConnectionError(DAQError):
    """Raised when connection to Synnax server fails"""
    pass

class ConfigurationError(DAQError):
    """Raised when configuration related errors occur"""
    pass

class DeviceError(DAQError):
    """Raised when device related errors occur"""
    pass

class TaskError(DAQError):
    """Raised when task related errors occur"""
    pass