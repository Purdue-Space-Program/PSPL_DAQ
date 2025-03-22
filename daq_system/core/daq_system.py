from typing import Optional, Tuple, List
import logging
import synnax as sy
from synnax.hardware import ni
import pandas as pd
import json
import time

from ..config.settings import DAQConfig
from ..utils.exceptions import ConnectionError, TaskError
from ..processing.channel_factory import ChannelFactory
from ..processing.analog import process_analog_input
from ..processing.digital import process_digital_input, process_digital_output

# DEFINE STATES
ENERGIZED = 0
DEENERGIZED = 1

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DAQSystem:
    """Main DAQ system class handling device management and task creation"""

    def __init__(self, config: DAQConfig):
        self.config = config
        self.client = self._connect_to_synnax()
        self._validate_device_connection()  # Add validation step
        self.channel_factory = ChannelFactory(self.client)

    def _connect_to_synnax(self) -> sy.Synnax:
        """Establish connection to Synnax server"""
        try:
            return sy.Synnax(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Synnax: {e}")

    def _check_driver_status(self) -> bool:
        """
        Check if the Synnax driver is running and accessible.
        Returns True if driver is running, False otherwise.
        """
        try:
            # Try to get driver status
            if not hasattr(self.client.hardware, "drivers"):
                logger.warning(
                    "Synnax client does not have drivers attribute. This may indicate an older version or different configuration."
                )
                # Try to verify driver status by attempting to retrieve devices
                try:
                    self.client.hardware.devices.retrieve(location="Dev5")
                    return True
                except Exception as e:
                    logger.error(f"Failed to verify driver status: {e}")
                    return False

            status = self.client.hardware.drivers.status()
            if not status or not status.get("is_running", False):
                logger.error("Synnax driver is not running!")
                if "last_alive" in status:
                    logger.error(f"Driver was last alive: {status['last_alive']}")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to check driver status: {e}")
            return False

    def _validate_device_connection(self) -> None:
        """
        Validate that NI devices are properly connected and accessible.
        Raises ConnectionError if no devices are found or if there are connection issues.
        """
        try:
            logger.info("Validating NI device connections...")

            # First check if driver is running
            if not self._check_driver_status():
                raise ConnectionError(
                    "Synnax driver is not running. Please ensure the driver is started and accessible."
                )

            # Try to retrieve both devices
            device_5 = self.client.hardware.devices.retrieve(location="Dev5")
            device_6 = self.client.hardware.devices.retrieve(location="Dev6")

            devices = [device_5, device_6]
            found_devices = [d for d in devices if d is not None]

            if not found_devices:
                raise ConnectionError(
                    "No NI devices found. Please check your hardware connections."
                )

            # Log information for each found device
            for device in found_devices:
                logger.info("-" * 50)
                logger.info(f"Found NI device:")
                logger.info(f"Device Name: {device.name}")
                logger.info(f"Location: {device.location}")
                logger.info(f"Model: {device.model}")
                logger.info(f"Make: {device.make}")
                logger.info(f"Key: {device.key}")
                logger.info(f"Rack: {device.rack}")

                # Log device properties
                if hasattr(device, "properties"):
                    try:
                        props = json.loads(device.properties)
                        logger.info("\nDevice Properties:")
                        for key, value in props.items():
                            logger.info(f"  {key}: {value}")

                            # Additional validation for simulation mode
                            if key == "is_simulated" and value:
                                logger.warning("Device is running in simulation mode!")

                    except json.JSONDecodeError:
                        logger.warning(
                            f"Could not parse device properties: {device.properties}"
                        )

            logger.info("-" * 50)
            logger.info("Device validation completed successfully.")

        except Exception as e:
            raise ConnectionError(f"Device validation failed: {e}")

    def get_device_info(self) -> dict:
        """
        Get information about the currently connected devices.
        Returns a dictionary containing device details.
        """
        try:
            device_5 = self.client.hardware.devices.retrieve(location="Dev5")
            device_6 = self.client.hardware.devices.retrieve(location="Dev6")

            devices = [device_5, device_6]
            found_devices = [d for d in devices if d is not None]

            if not found_devices:
                return {"error": "No devices found"}

            info = {}
            for device in found_devices:
                device_info = {
                    "name": device.name,
                    "location": device.location,
                    "model": device.model,
                    "make": device.make,
                    "key": device.key,
                    "rack": device.rack,
                }

                if hasattr(device, "properties"):
                    try:
                        device_info["properties"] = json.loads(device.properties)
                    except json.JSONDecodeError:
                        device_info["properties"] = device.properties

                info[device.location] = device_info

            return info

        except Exception as e:
            return {"error": f"Failed to get device info: {e}"}

    def _delete_existing_task(self, task_name: str) -> None:
        """
        Delete task if it exists.

        Args:
            task_name: Name of the task to delete
        """
        try:
            existing_task = self.client.hardware.tasks.retrieve(name=task_name)
            if existing_task is not None:
                logger.info(f"Deleting existing task: {task_name}")
                self.client.hardware.tasks.delete(existing_task.key)
        except Exception as e:
            logger.debug(f"No existing task found for {task_name}: {e}")

    def _create_analog_read_task(
        self, card_name: str, device_key: str
    ) -> ni.AnalogReadTask:
        """Create an analog read task"""
        return ni.AnalogReadTask(
            name=f"{card_name} AI",
            device=device_key,
            sample_rate=sy.Rate.HZ * self.config.sample_rate,
            stream_rate=sy.Rate.HZ * self.config.stream_rate,
            data_saving=True,
            channels=[],
        )

    def _create_digital_write_task(
        self, card_name: str, device_key: str
    ) -> ni.DigitalWriteTask:
        """Create a digital write task"""
        return ni.DigitalWriteTask(
            name=f"{card_name} DO",
            device=device_key,
            state_rate=sy.Rate.HZ * self.config.sample_rate,
            data_saving=True,
            channels=[],
        )

    def _create_digital_read_task(
        self, card_name: str, device_key: str
    ) -> ni.DigitalReadTask:
        """Create a digital read task"""
        return ni.DigitalReadTask(
            name=f"{card_name} DI",
            device=device_key,
            sample_rate=sy.Rate.HZ * self.config.sample_rate,
            stream_rate=sy.Rate.HZ * self.config.stream_rate,
            data_saving=True,
            channels=[],
        )

    def create_device_tasks(
        self, device: sy.Device
    ) -> Tuple[ni.AnalogReadTask, ni.DigitalWriteTask, ni.DigitalReadTask]:
        """
        Create all tasks for a device, deleting any existing tasks with the same names.

        Args:
            device: Synnax device object

        Returns:
            Tuple of (AnalogReadTask, DigitalWriteTask, DigitalReadTask)
        """
        card_name = device.location
        tasks: List[ni.Task] = []

        # Define task configurations
        task_configs = [
            ("AI", self._create_analog_read_task),
            ("DO", self._create_digital_write_task),
            ("DI", self._create_digital_read_task),
        ]

        # Create each task, deleting existing ones first
        for suffix, creator_func in task_configs:
            task_name = f"{card_name} {suffix}"
            logger.info(f"Setting up task: {task_name}")

            # Delete existing task if it exists
            self._delete_existing_task(task_name)

            # Create new task
            try:
                task = creator_func(card_name, device.key)
                tasks.append(task)
                logger.info(f"Successfully created task: {task_name}")
            except Exception as e:
                raise TaskError(f"Failed to create task {task_name}: {e}")

        return tuple(tasks)

    def configure_task(self, task: Optional[ni.Task], task_type: str) -> None:
        """Configure a task if it has channels"""
        if not task or not task.config.channels:
            logger.info(f"No channels added to {task_type} task.")
            return

        try:
            logger.info(f"Configuring {task_type} task...")

            # Check driver status before attempting configuration
            if not self._check_driver_status():
                raise TaskError(
                    "Cannot configure task: Synnax driver is not running. Please ensure the driver is started and accessible."
                )

            # Add retry logic for task configuration
            max_retries = 3
            retry_delay = 2  # seconds

            for attempt in range(max_retries):
                try:
                    self.client.hardware.tasks.configure(task=task, timeout=10)
                    logger.info(f"Successfully configured {task_type} task.")
                    return
                except TimeoutError as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Configuration attempt {attempt + 1} failed, retrying in {retry_delay} seconds..."
                        )
                        time.sleep(retry_delay)
                    else:
                        raise TaskError(
                            f"Failed to configure {task_type} task after {max_retries} attempts: {e}"
                        )
        except Exception as e:
            raise TaskError(f"Failed to configure {task_type} task: {e}")

    def start_digital_output_task(
        self, digital_write_task: ni.DigitalWriteTask
    ) -> None:
        """
        Start a digital output task and set all channel states to deenergized (DEENERGIZED)

        Args:
            digital_write_task: The digital write task to start
        """
        if not digital_write_task or not digital_write_task.config.channels:
            logger.info("No digital output task or channels to start.")
            return

        try:
            logger.info(f"Starting digital output task: {digital_write_task.name}")

            # Start the task
            digital_write_task.start()

            # Get all command channel keys from the task
            cmd_channels = [
                chan.cmd_channel for chan in digital_write_task.config.channels
            ]

            # Get corresponding state channel keys for reading
            state_channels = []
            for chan in digital_write_task.config.channels:
                if hasattr(chan, "state_channel") and chan.state_channel:
                    state_channels.append(chan.state_channel)
                else:
                    # If no state channel, use the command channel
                    state_channels.append(chan.cmd_channel)

            logger.info(f"Setting {len(cmd_channels)} channels to DEENERGIZED state")
            logger.debug(f"Command channels: {cmd_channels}")
            logger.debug(f"State channels: {state_channels}")

            # Ensure we have matched arrays for command and state channels
            if len(cmd_channels) != len(state_channels):
                logger.warning(
                    f"Channel count mismatch: {len(cmd_channels)} command channels vs {len(state_channels)} state channels"
                )
                # Only use channels where we have both command and state
                min_length = min(len(cmd_channels), len(state_channels))
                cmd_channels = cmd_channels[:min_length]
                state_channels = state_channels[:min_length]

            # Set all digital outputs to deenergized state one by one to avoid issues
            for i, (cmd_channel, state_channel) in enumerate(
                zip(cmd_channels, state_channels)
            ):
                try:
                    with self.client.control.acquire(
                        name=f"Initialize channel {i} in {digital_write_task.name}",
                        write=[cmd_channel],
                        read=[state_channel],
                        write_authorities=50,
                    ) as ctrl:
                        ctrl[cmd_channel] = DEENERGIZED
                        logger.info(f"Set channel {cmd_channel} to DEENERGIZED")
                except Exception as e:
                    logger.error(f"Failed to set channel {cmd_channel}: {e}")
                    # Continue with other channels

            logger.info(
                f"Successfully started digital output task: {digital_write_task.name}"
            )
        except Exception as e:
            raise TaskError(f"Failed to start digital output task: {e}")

    def setup_device(
        self,
        device: sy.Device,
        data_wiring: pd.ExcelFile,
        control_wiring: pd.ExcelFile,
    ) -> None:
        """
        Complete device setup in the correct sequence:
        1. Create tasks
        2. Process device data to add channels
        3. Configure tasks
        4. Start digital output task

        Args:
            device: Synnax device object
            data_wiring: Excel file containing data wiring information
            control_wiring: Excel file containing control wiring information
        """
        logger.info(f"Setting up device: {device.location}")

        # Step 1: Create tasks
        analog_read_task, digital_write_task, digital_read_task = (
            self.create_device_tasks(device)
        )

        # Step 2: Process device data to add channels to the tasks
        logger.info(f"Processing device data for {device.location}")
        process_analog_input(
            data_wiring,
            analog_read_task,
            device,
            self.channel_factory,
            self.config.stream_rate,
        )

        process_digital_input(
            data_wiring,
            digital_read_task,
            device,
            self.channel_factory,
        )

        process_digital_output(
            control_wiring,
            digital_write_task,
            device,
            self.channel_factory,
            self.config.sample_rate,
        )
        logger.info(f"Completed processing device data for {device.location}")

        # Step 3: Configure tasks with their channels
        self.configure_task(analog_read_task, "Analog Read")
        self.configure_task(digital_write_task, "Digital Write")
        self.configure_task(digital_read_task, "Digital Read")

        # Step 4: Start the digital output task to set all outputs to deenergized state
        self.start_digital_output_task(digital_write_task)

        logger.info(f"Device setup complete: {device.location}")

        return analog_read_task, digital_write_task, digital_read_task
