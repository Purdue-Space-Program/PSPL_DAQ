from typing import Optional, Tuple, List
import logging
import synnax as sy
from synnax.hardware import ni
import pandas as pd

from ..config.settings import DAQConfig
from ..utils.exceptions import ConnectionError, TaskError
from ..processing.channel_factory import ChannelFactory
from ..processing.analog import process_analog_input
from ..processing.digital import process_digital_input, process_digital_output

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DAQSystem:
    """Main DAQ system class handling device management and task creation"""

    def __init__(self, config: DAQConfig):
        self.config = config
        self.client = self._connect_to_synnax()
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
            ("Analog Input", self._create_analog_read_task),
            ("Digital Output", self._create_digital_write_task),
            ("Digital Input", self._create_digital_read_task),
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
            self.client.hardware.tasks.configure(task=task, timeout=5)
            logger.info(f"Successfully configured {task_type} task.")
        except Exception as e:
            raise TaskError(f"Failed to configure {task_type} task: {e}")

    def process_device_data(
        self,
        device: sy.Device,
        data_wiring: pd.ExcelFile,
        control_wiring: pd.ExcelFile,
        tasks: Tuple[ni.AnalogReadTask, ni.DigitalWriteTask, ni.DigitalReadTask],
    ) -> None:
        """Process all data for a device"""
        analog_read_task, digital_write_task, digital_read_task = tasks

        logger.info(f"Processing device data for {device.location}")

        # Process inputs and outputs
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
            self.config.stream_rate,
        )

        process_digital_output(
            control_wiring,
            digital_write_task,
            device,
            self.channel_factory,
            self.config.sample_rate,
        )

        logger.info(f"Completed processing device data for {device.location}")
