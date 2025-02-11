import pandas as pd
import synnax as sy
from synnax.hardware import ni
from .channel_factory import ChannelFactory


def process_digital_input(data: pd.ExcelFile,
                          digital_read_task: ni.DigitalReadTask,
                          device: sy.Device,
                          channel_factory: ChannelFactory,
                          stream_rate: int):
    """Process digital input configuration"""
    sensors = data.parse("DI")

    for _, row in sensors.iterrows():
        # Create timestamp channel
        bcls_di_time = channel_factory.create_timestamp_channel("BCLS_di_time")

        # Create sensor channel - note: no units for digital channels
        sensor_channel = channel_factory.create_data_channel(
            name=row["Name"],
            data_type=sy.DataType.UINT8,
            index_key=bcls_di_time.key,
            rate=sy.Rate.HZ * stream_rate
        )

        # Extract channel number
        channel_num = int(''.join(filter(str.isdigit, row["Channel"].split('/')[-1])))

        # Create DI channel
        di_chan = ni.DIChan(
            channel=sensor_channel.key,
            port=0,
            line=channel_num,
        )

        digital_read_task.config.channels.append(di_chan)


def process_digital_output(data: pd.ExcelFile,
                           digital_write_task: ni.DigitalWriteTask,
                           device: sy.Device,
                           channel_factory: ChannelFactory,
                           sample_rate: int):
    """Process digital output configuration"""
    sensors = data.parse("DO")

    for _, row in sensors.iterrows():
        # Create timestamp channels
        bcls_state_time = channel_factory.create_timestamp_channel("BCLS_state_time")
        bcls_cmd_time = channel_factory.create_timestamp_channel("BCLS_cmd_time")

        # Extract line number
        line = int(row["Channel"].split('/')[-1][4:])

        # Create state and command channels - note: no units for digital channels
        state_chan = channel_factory.create_data_channel(
            name=f"{row['Name']}_state",
            data_type=sy.DataType.UINT8,
            index_key=bcls_state_time.key,
            rate=sy.Rate.HZ * sample_rate
        )

        cmd_chan = channel_factory.create_data_channel(
            name=f"{row['Name']}_cmd",
            data_type=sy.DataType.UINT8,
            index_key=bcls_cmd_time.key,
            rate=sy.Rate.HZ * sample_rate
        )

        # Create DO channel
        do_chan = ni.DOChan(
            cmd_channel=cmd_chan.key,
            state_channel=state_chan.key,
            port=0,
            line=line,
        )

        digital_write_task.config.channels.append(do_chan)