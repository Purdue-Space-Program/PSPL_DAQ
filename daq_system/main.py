from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from daq_system.core.daq_system import DAQSystem
from daq_system.utils.exceptions import DAQError

import pandas as pd


def main():
    try:
        # Initialize DAQ system
        config = DAQConfig()
        daq_system = DAQSystem(config)

        # Process each device
        for device_name, paths in DEFAULT_DEVICE_PATHS.items():
            print(f"\nProcessing {device_name}...")

            # Get device
            device = daq_system.client.hardware.devices.retrieve(
                model="USB-6343",
                location=device_name
            )

            # Read configuration files
            data_wiring = pd.ExcelFile(paths.data_wiring)
            control_wiring = pd.ExcelFile(paths.control_wiring)

            # Create and configure tasks
            tasks = daq_system.create_device_tasks(device)

            # Process data
            daq_system.process_device_data(device, data_wiring, control_wiring, tasks)

            # Configure all tasks
            for task, task_type in zip(tasks, ["Analog Read", "Digital Write", "Digital Read"]):
                daq_system.configure_task(task, task_type)

    except DAQError as e:
        print(f"DAQ Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()