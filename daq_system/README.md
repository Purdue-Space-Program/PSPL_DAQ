# DAQ System

A robust Data Acquisition System built with Synnax for managing NI USB-6343 devices and handling various types of data inputs and outputs.

## Features

- Automated device discovery and configuration
- Support for analog and digital I/O
- Real-time data processing
- Configurable sampling rates
- Automatic task management
- Excel-based configuration system
- Comprehensive error handling
- Extensive logging

## Installation

### Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- National Instruments DAQmx drivers
- Synnax server running and accessible

### Installing from source

1. Clone the repository:
```bash
git clone https://github.com/Purdue-Space-Program/PSPL_DAQ.git
cd PSPL_DAQ/daq-system
uv sync
```

2. Run the program:
```bash
uv run main.py
```

## Project Structure

```
daq_system/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration settings
├── core/
│   ├── __init__.py
│   └── daq_system.py     # Main DAQ system implementation
├── processing/
│   ├── __init__.py
│   ├── analog.py         # Analog input processing
│   ├── digital.py        # Digital I/O processing
│   └── channel_factory.py # Channel creation utilities
└── utils/
    ├── __init__.py
    └── exceptions.py     # Custom exceptions
```

## Usage

### Basic Usage

```python
from daq_system import DAQSystem, DAQConfig
from pathlib import Path

# Configure the system
config = DAQConfig(
    sample_rate=1000,  # Hz
    stream_rate=100,   # Hz
    host="your.synnax.server",
    port=9090,
    username="user",
    password="pass"
)

# Initialize the system
daq = DAQSystem(config)

# Configure device paths
device_paths = {
    "Dev5": DeviceWiringPaths(
        data_wiring=Path("inputs/CMS_Data_Test_Dev5.xlsx"),
        control_wiring=Path("inputs/CMS_Control_Test_Dev5.xlsx")
    )
}

# Process devices
for device_name, paths in device_paths.items():
    # Get device
    device = daq.client.hardware.devices.retrieve(
        model="USB-6343", 
        location=device_name
    )
    
    # Create and configure tasks
    tasks = daq.create_device_tasks(device)
    
    # Process data
    daq.process_device_data(
        device,
        pd.ExcelFile(paths.data_wiring),
        pd.ExcelFile(paths.control_wiring),
        tasks
    )
```

### Configuration Files

The system uses Excel files for configuration:

#### Data Wiring (CMS_Data_Test_DevX.xlsx):
- Sheet "AI_slope-offset": Analog input configuration
- Sheet "DI": Digital input configuration

#### Control Wiring (CMS_Control_Test_DevX.xlsx):
- Sheet "DO": Digital output configuration

### Error Handling

The system provides custom exceptions for different error types:
- `DAQError`: Base exception
- `ConnectionError`: Connection issues
- `ConfigurationError`: Configuration problems
- `DeviceError`: Device-related errors
- `TaskError`: Task creation/configuration errors

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Synnax](https://synnaxlabs.com/)
- Uses National Instruments DAQmx
