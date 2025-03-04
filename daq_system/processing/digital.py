import pandas as pd
import synnax as sy
from synnax.hardware import ni
from .channel_factory import ChannelFactory

STATE_RATE = 1000  # Hz


def process_digital_input(
    data: pd.ExcelFile,
    digital_read_task: ni.DigitalReadTask,
    device: sy.Device,
    channel_factory: ChannelFactory,
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

    state_time_chan = channel_factory.client.channels.create(
        name="state_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )

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
