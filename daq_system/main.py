import pandas as pd  # type: ignore
from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from daq_system.core.daq_system import DAQSystem
from daq_system.utils.exceptions import DAQError

# TODO: Bug fix. Dev6 AI tasks does not stop correctly after it is started.
# TODO: Bug fix. BCLS_state_time does not want to delete. Needs EMU_PWR to be deleted first.
# TODO: Bug fix (Top Priority) Default state for valves and solenoids is on.
# TODO: Make function to delete all channels and all tasks


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

            # Use the new setup_device method which handles everything
            daq_system.setup_device(device, data_wiring, control_wiring)

    except DAQError as e:
        print(f"DAQ Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
