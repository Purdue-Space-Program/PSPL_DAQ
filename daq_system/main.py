import pandas as pd  # type: ignore

from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from daq_system.core.daq_system import DAQSystem
from daq_system.utils.exceptions import DAQError

# TODO: Bug fix. Dev6 AI tasks does not stop correctly after it is started.
# TODO: Bug fix. BCLS_state_time does not want to delete. Needs EMU_PWR to be deleted first.
# TODO: Bug fix (Top Priority) Default state for valves and solenoids is on.


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
                model="USB-6343", location=device_name
            )
            # Read configuration files
            data_wiring = pd.ExcelFile(paths.data_wiring)
            control_wiring = pd.ExcelFile(paths.control_wiring)

            # Create and configure tasks
            analog_read_task, digital_write_task, digital_read_task = (
                daq_system.create_device_tasks(device)
            )

            # Process data
            daq_system.process_device_data(
                device,
                data_wiring,
                control_wiring,
                (analog_read_task, digital_write_task, digital_read_task),
            )

            daq_system.configure_task(analog_read_task, "Analog Read")
            daq_system.configure_task(digital_write_task, "Digital Write")
            daq_system.configure_task(digital_read_task, "Digital Read")

            # Could I set this up to run this if in daq_system.py instead

            if digital_write_task and digital_write_task.config.channels:
                # Start digital write task
                daq_system.start_task(digital_write_task)

    except DAQError as e:
        print(f"DAQ Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
