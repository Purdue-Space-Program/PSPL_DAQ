from dataclasses import dataclass
from typing import Optional, Tuple, Dict
from pathlib import Path

import pandas as pd
import synnax as sy
from synnax.hardware import ni
from configs.processing import process_analog_input, process_digital_input, process_digital_output


@dataclass
class DAQConfig:
    """Configuration settings for DAQ system"""
    sample_rate: int = 1000  # Hz
    stream_rate: int = 100  # Hz
    host: str = "128.46.118.59"
    port: int = 9090
    username: str = "Bill"
    password: str = "Bill"


@dataclass
class DeviceWiringPaths:
    """Paths to wiring configuration files for a device"""
    data_wiring: Path
    control_wiring: Path


class DAQSystem:
    def __init__(self, config: DAQConfig):
        self.config = config
        self.client = self._connect_to_synnax()

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

    def get_device(self, location: str) -> sy.Device:
        """Retrieve a device by its location"""
        try:
            return self.client.hardware.devices.retrieve(model="USB-6343", location=location)
        except Exception as e:
            raise ValueError(f"Failed to retrieve device {location}: {e}")

    def read_wiring_config(self, paths: DeviceWiringPaths) -> Tuple[pd.ExcelFile, pd.ExcelFile]:
        """Read wiring configuration files"""
        try:
            data_wiring = pd.ExcelFile(paths.data_wiring)
            control_wiring = pd.ExcelFile(paths.control_wiring)
            return data_wiring, control_wiring
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Wiring configuration file not found: {e}")
        except Exception as e:
            raise ValueError(f"Error reading wiring configuration: {e}")

    def create_device_tasks(self, device: sy.Device) -> Tuple[
        ni.AnalogReadTask, ni.DigitalWriteTask, ni.DigitalReadTask]:
        """Create or recreate all tasks for a device"""
        card_name = device.location
        tasks = []

        task_configs = [
            ("Analog Input", self._create_analog_read_task),
            ("Digital Output", self._create_digital_write_task),
            ("Digital Input", self._create_digital_read_task)
        ]

        for suffix, creator_func in task_configs:
            task_name = f"{card_name} {suffix}"
            self._delete_existing_task(task_name)
            tasks.append(creator_func(card_name, device.key))

        return tuple(tasks)

    def _delete_existing_task(self, task_name: str) -> None:
        """Delete task if it exists"""
        try:
            existing_task = self.client.hardware.tasks.retrieve(name=task_name)
            if existing_task is not None:
                self.client.hardware.tasks.delete(existing_task.key)
        except Exception:
            pass  # Task doesn't exist, continue

    def _create_analog_read_task(self, card_name: str, device_key: str) -> ni.AnalogReadTask:
        return ni.AnalogReadTask(
            name=f"{card_name} Analog Input",
            device=device_key,
            sample_rate=sy.Rate.HZ * self.config.sample_rate,
            stream_rate=sy.Rate.HZ * self.config.stream_rate,
            data_saving=True,
            channels=[],
        )

    def _create_digital_write_task(self, card_name: str, device_key: str) -> ni.DigitalWriteTask:
        return ni.DigitalWriteTask(
            name=f"{card_name} Digital Output",
            device=device_key,
            state_rate=sy.Rate.HZ * self.config.sample_rate,
            data_saving=True,
            channels=[],
        )

    def _create_digital_read_task(self, card_name: str, device_key: str) -> ni.DigitalReadTask:
        return ni.DigitalReadTask(
            name=f"{card_name} Digital Input",
            device=device_key,
            sample_rate=sy.Rate.HZ * self.config.sample_rate,
            stream_rate=sy.Rate.HZ * self.config.stream_rate,
            data_saving=True,
            channels=[],
        )

    def configure_task(self, task: Optional[ni.Task], task_type: str) -> None:
        """Configure a task if it has channels"""
        if not task or not task.config.channels:
            print(f"No channels added to {task_type} task.")
            return

        try:
            print(f"Configuring {task_type} task...")
            self.client.hardware.tasks.configure(task=task, timeout=5)
            print(f"{task_type} task configured successfully.")
        except Exception as e:
            print(f"Failed to configure {task_type} task: {e}")

    def process_device_data(self,
                            device: sy.Device,
                            wiring_config: Tuple[pd.ExcelFile, pd.ExcelFile],
                            tasks: Tuple[ni.AnalogReadTask, ni.DigitalWriteTask, ni.DigitalReadTask]) -> None:
        """Process all data for a device"""
        data_wiring, control_wiring = wiring_config
        analog_read_task, digital_write_task, digital_read_task = tasks

        process_analog_input(data_wiring, analog_read_task, device,
                             stream_rate=self.config.stream_rate,
                             sample_rate=self.config.sample_rate)

        process_digital_input(data_wiring, digital_read_task, device,
                              stream_rate=self.config.stream_rate,
                              sample_rate=self.config.sample_rate)

        process_digital_output(control_wiring, digital_write_task, device,
                               stream_rate=self.config.stream_rate,
                               sample_rate=self.config.sample_rate)


def main():
    # Configuration
    config = DAQConfig()
    wiring_paths = {
        "Dev5": DeviceWiringPaths(
            data_wiring=Path("inputs/CMS_Data_Test_Dev5.xlsx"),
            control_wiring=Path("inputs/CMS_Control_Test_Dev5.xlsx")
        ),
        "Dev6": DeviceWiringPaths(
            data_wiring=Path("inputs/CMS_Data_Test_Dev6.xlsx"),
            control_wiring=Path("inputs/CMS_Control_Test_Dev6.xlsx")
        )
    }

    try:
        # Initialize DAQ system
        daq_system = DAQSystem(config)

        # Process each device
        for device_name, paths in wiring_paths.items():
            print(f"\nProcessing {device_name}...")

            # Get device and configurations
            device = daq_system.get_device(device_name)
            wiring_config = daq_system.read_wiring_config(paths)

            # Create and configure tasks
            tasks = daq_system.create_device_tasks(device)

            # Process data
            daq_system.process_device_data(device, wiring_config, tasks)

            # Configure all tasks
            for task, task_type in zip(tasks, ["Analog Read", "Digital Write", "Digital Read"]):
                daq_system.configure_task(task, task_type)

    except Exception as e:
        print(f"Error in DAQ setup: {e}")
        raise


if __name__ == "__main__":
    main()