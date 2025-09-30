import pandas as pd  # type: ignore
import logging
from daq_system.config.settings import DAQConfig, DEFAULT_DEVICE_PATHS
from daq_system.core.daq_system import DAQSystem
from daq_system.utils.exceptions import DAQError
from daq_system.utils.logging_config import setup_logging

# Configure logging only once at the start of the application
setup_logging()
logger = logging.getLogger(__name__)

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
            logger.info(f"\nProcessing {device_name}...")

            # Get device
            device = daq_system.client.hardware.devices.retrieve(
                model="USB-6343", location=device_name
            )

            # Read configuration files
            data_wiring = pd.ExcelFile(paths.data_wiring)
            control_wiring = pd.ExcelFile(paths.control_wiring)

            # Use the new setup_device method which handles everything
            daq_system.setup_device(device, data_wiring, control_wiring, device_name)

    except DAQError as e:
        logger.error(f"DAQ Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
