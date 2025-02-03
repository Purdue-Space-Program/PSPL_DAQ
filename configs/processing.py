import synnax as sy
from synnax.hardware import ni
import pandas as pd

client = sy.Synnax(
    host = "128.46.118.59",
    port = 9090,
    username = "Bill",
    password = "Bill",
)


def process_digital_output(data: pd.ExcelFile, digital_write_task: ni.DigitalWriteTask, card: sy.Device, sample_rate: int, stream_rate: int):

    sensors = data.parse("DO")

    for _, row in sensors.iterrows():

        channel = row["Channel"]
        line = int(channel.split('/')[-1][4:])

        device_name = row["Name"]

        bcls_state_time = client.channels.create(
            name="BCLS_state_time",
            is_index=True,
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
        )

        bcls_cmd_time = client.channels.create(
            name="BCLS_cmd_time",
            is_index=True,
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
        )

        state_chan = client.channels.create(
            name=f"{device_name}_state",
            data_type=sy.DataType.UINT8,
            retrieve_if_name_exists=True,
            index=bcls_state_time.key,
            rate=sy.Rate.HZ * sample_rate,
        )
        cmd_chan = client.channels.create(
            name=f"{device_name}_cmd",
            data_type=sy.DataType.UINT8,
            retrieve_if_name_exists=True,
            index=bcls_cmd_time.key,
            rate=sy.Rate.HZ * sample_rate,
        )
        do_chan = ni.DOChan(
            cmd_channel=cmd_chan.key,
            state_channel=state_chan.key,
            port = 0,
            line = line,
        )

        digital_write_task.config.channels.append(do_chan)

def process_analog_input(data: pd.ExcelFile, analog_read_task: ni.AnalogReadTask, card: sy.Device, stream_rate: int, sample_rate: int):


    sensors = data.parse("AI_slope-offset")

    for _, row in sensors.iterrows():

        sensor_name = row["Name"]

        channel = row["Channel"]
        channel_num = int(channel.split('/')[-1][2:])



        bcls_ai_time = client.channels.create(
            name="BCLS_ai_time",
            is_index=True,
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
        )

        sensor_channel = client.channels.create(
            name=f"{sensor_name}",
            data_type=sy.DataType.FLOAT32,
            retrieve_if_name_exists=True,
            index=bcls_ai_time.key,
            rate=sy.Rate.HZ * stream_rate,
        )

        ai_chan = ni.AIVoltageChan(
            channel=sensor_channel.key,
            port=channel_num,
            device=card.key,
            custom_scale=ni.LinScale(
                slope=row["Slope"],
                y_intercept=row["Offset"],
                pre_scaled_units="Volts",
                scaled_units=row["Engineering Units"],
            ),
            terminal_config="Diff",
        )

        analog_read_task.config.channels.append(ai_chan)

def process_digital_input(data: pd.ExcelFile, digital_read_task: ni.DigitalReadTask, card: sy.Device, sample_rate: int, stream_rate: int):

    sensors = data.parse("DI")

    for _, row in sensors.iterrows():

        sensor_name = row["Name"]
        channel = row["Channel"]
        channel_num = int(''.join(filter(str.isdigit, channel.split('/')[-1])))



        bcls_di_time = client.channels.create(
            name="BCLS_di_time",
            is_index=True,
            data_type=sy.DataType.TIMESTAMP,
            retrieve_if_name_exists=True,
        )

        sensor_channel = client.channels.create(
            name=f"{sensor_name}",
            data_type=sy.DataType.UINT8,
            retrieve_if_name_exists=True,
            index=bcls_di_time.key,
            rate=sy.Rate.HZ * stream_rate,
        )

        di_chan = ni.DIChan(
            channel=sensor_channel.key,
            port=0,
            line=channel_num,
        )

        digital_read_task.config.channels.append(di_chan)















