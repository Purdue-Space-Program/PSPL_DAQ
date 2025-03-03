import pandas as pd
import synnax as sy
from synnax.hardware import ni
from .channel_factory import ChannelFactory


def process_digital_input(
    data: pd.ExcelFile,
    digital_read_task: ni.DigitalReadTask,
    device: sy.Device,
    channel_factory: ChannelFactory,
    stream_rate: int,
):
    """Process digital input configuration"""

    sensors = data.parse("DI")

    for _, row in sensors.iterrows():

        # Create timestamp channel

        name = row["Name"]

        bcls_di_time = channel_factory.create_timestamp_channel(f"BCLS_di_time_{name}")

        # Create sensor channel - note: no units for digital channels

        sensor_channel = channel_factory.create_data_channel(
            name=row["Name"],
            data_type=sy.DataType.UINT8,
            index_key=bcls_di_time.key,
            rate=sy.Rate.HZ * STATE_RATE,
        )

        # Extract channel number

        channel_num = int("".join(filter(str.isdigit, row["Channel"].split("/")[-1])))

        # Create DI channel

        di_chan = ni.DIChan(
            channel=sensor_channel.key,
            port=0,
            line=channel_num,
        )

        digital_read_task.config.channels.append(di_chan)


def process_digital_output(
    data: pd.ExcelFile,
    digital_write_task: ni.DigitalWriteTask,
    device: sy.Device,
    channel_factory: ChannelFactory,
    sample_rate: int,
):
    """Process digital output configuration"""
    sensors = data.parse("DO")
    for _, row in sensors.iterrows():
        name = row["Name"]

        # 1. Create command channel (virtual) - no index or rate for virtual channels
        cmd_chan = channel_factory.client.channels.create(
            name=f"{name}_cmd",
            data_type=sy.DataType.UINT8,
            retrieve_if_name_exists=True,
            virtual=True,
        )

        # 2. Create timestamp channel that will be used as index for the state channel
        state_time_chan = channel_factory.client.channels.create(
            name=f"{name}_state_time",
            is_index=True,
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
        )

        # 3. Create state channel with index pointing to the timestamp channel
        state_chan = channel_factory.client.channels.create(
            name=f"{name}_state",
            data_type=sy.DataType.UINT8,
            index=state_time_chan.key,
            retrieve_if_name_exists=True,
        )

        # Extract line number correctly
        if "line" in row:
            line = int(row["line"])
        else:
            # Extract from channel string as fallback
            try:
                line = int(row["Channel"].split("/")[-1][4:])
            except (IndexError, ValueError):
                line = int("".join(filter(str.isdigit, row["Channel"].split("/")[-1])))

        # Create DO channel configuration
        do_chan = ni.DOChan(
            cmd_channel=cmd_chan.key,
            state_channel=state_chan.key,
            port=0,
            line=line,
        )

        # Add the channel to the task
        digital_write_task.config.channels.append(do_chan)


def process_digital_output_direct(
    data: pd.ExcelFile,
    digital_write_task: ni.DigitalWriteTask,
    device: sy.Device,
    client: sy.Synnax,
    sample_rate: int,
):
    """Process digital output configuration directly based on working example"""
    sensors = data.parse("DO")
    for _, row in sensors.iterrows():
        name = row["Name"]

        # Create command channel (virtual)
        do_cmd = client.channels.create(
            name=f"{name}_cmd",
            data_type=sy.DataType.UINT8,
            retrieve_if_name_exists=True,
            virtual=True,
        )

        # Create time channel for states
        do_state_time = client.channels.create(
            name=f"{name}_state_time",
            is_index=True,
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
        )

        # Create state channel
        do_state = client.channels.create(
            name=f"{name}_state",
            index=do_state_time.key,
            data_type=sy.DataType.UINT8,
            retrieve_if_name_exists=True,
        )

        # Extract line number
        line = int(row["Channel"].split("/")[-1][4:])

        # Create DO channel
        do_chan = ni.DOChan(
            cmd_channel=do_cmd.key,
            state_channel=do_state.key,
            port=0,
            line=line,
        )

        digital_write_task.config.channels.append(do_chan)


def debug_digital_write_task(task: ni.DigitalWriteTask):
    """Print debug information for a digital write task"""
    print(f"Task name: {task.name}")
    print(f"Number of channels: {len(task.config.channels)}")

    for i, chan in enumerate(task.config.channels):
        print(f"Channel {i+1}:")
        print(f"  CMD channel key: {chan.cmd_channel}")
        print(f"  State channel key: {chan.state_channel}")
        print(f"  Port: {chan.port}, Line: {chan.line}")

    return
