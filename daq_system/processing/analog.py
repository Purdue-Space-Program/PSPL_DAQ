import pandas as pd
import synnax as sy
from synnax.hardware import ni
from .channel_factory import ChannelFactory


def process_analog_input(
    data: pd.ExcelFile,
    analog_read_task: ni.AnalogReadTask,
    device: sy.Device,
    channel_factory: ChannelFactory,
    stream_rate: int,
):
    """Process analog input configuration"""
    sensors = data.parse("AI_slope-offset")

    for _, row in sensors.iterrows():
        # Create timestamp channel
        bcls_time = channel_factory.create_timestamp_channel("BCLS_time")

        # Create sensor channel
        sensor_channel = channel_factory.create_data_channel(
            name=row["Name"],
            data_type=sy.DataType.FLOAT32,
            index_key=bcls_time.key,
            rate=sy.Rate.HZ * stream_rate,
        )

        # Extract channel number
        channel_num = int(row["Channel"].split("/")[-1][2:])

        # Create AI voltage channel
        ai_chan = ni.AIVoltageChan(
            channel=sensor_channel.key,
            port=channel_num,
            device=device.key,
            custom_scale=ni.LinScale(
                slope=row["Slope"],
                y_intercept=row["Offset"],
                pre_scaled_units="Volts",
                scaled_units=row["Engineering Units"],
            ),
            terminal_config="Diff",
        )

        analog_read_task.config.channels.append(ai_chan)
