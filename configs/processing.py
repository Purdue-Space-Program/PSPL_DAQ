import synnax as sy
from numpy.f2py.auxfuncs import process_f2cmap_dict
from synnax.hardware import ni
import pandas as pd

client = sy.Synnax(
    host = "128.46.118.59",
    port = 9090,
    username = "Bill",
    password = "Bill",
)

def process_vlv(row: pd.Series, digital_write_task: ni.DigitalWriteTask, card: sy.Device):

    channel = int(row["Channel"])
    device_name = row["Name"]

    BCLS_state_time = client.channels.create(
        name="BCLS_state_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )

    BCLS_cmd_time = client.channels.create(
        name="BCLS_cmd_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )

    state_chan = client.channels.create(
        name=f"{device_name}_state",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        index=BCLS_state_time.key,
        rate=sy.Rate.HZ * 50,

    )

    cmd_chan = client.channels.create(
        name=f"{device_name}",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        index=BCLS_cmd_time.key,
        rate=sy.Rate.HZ * 50,
    )

    do_chan = ni.DOChan(
        cmd_channel=cmd_chan.key,
        state_channel=state_chan.key,
        port = 0,
        line = channel,
        rate=sy.Rate.HZ * 50,
    )

    digital_write_task.config.channels.append(do_chan)
    print("Added channel:", channel)


def process_pt(row: pd.Series, analog_read_task: ni.AnalogReadTask, card: sy.Device):
    device_name = row["Name"]
    channel_num = int(row["Channel"])

    BCLS_ai_time = client.channels.create(
        name="BCLS_ai_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )

    pt_chan = client.channels.create(
        name=f"{device_name}",
        data_type=sy.DataType.FLOAT32, # Idk data types, this is just what was suggested
        retrieve_if_name_exists=True,
        index=BCLS_ai_time.key,
        rate=sy.Rate.HZ * 50,
    )

    ai_chan = ni.AIVoltageChan(
        channel=pt_chan.key,
        port = 0,
        device=card.key,
        custom_scale = ni.LinScale(
            slope = row["Slope"],
            y_intercept = row["Offset"],
            pre_scaled_units = "Volts",
            scaled_units = "PoundsPerSquareInch",
        ),
        terminal_config = "Diff",
        rate=sy.Rate.HZ * 50,
    )

    analog_read_task.config.channels.append(ai_chan)
    print("Added channel:", channel_num)

def process_tc(row: pd.Series, analog_read_task: ni.AnalogReadTask, card: sy.Device):
    device_name = row["Name"]
    channel_num = int(row["Channel"])
    port = 0

    BCLS_ai_time = client.channels.create(
        name="BCLS_ai_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )

    tc_chan = client.channels.create(
        name=f"{device_name}",
        data_type=sy.DataType.FLOAT32,
        retrieve_if_name_exists=True,
        rate=sy.Rate.HZ * 50,
    )

    ai_chan = ni.AIVoltageChan(
        channel = tc_chan.key,
        port = 0,
        device = card.key,
        custom_scale = ni.LinScale(
            slope = row["Slope"],
            y_intercept = row["Offset"],
            pre_scaled_units = "Volts",
            scaled_units ="Celsius",
        ),

        terminal_config = "Diff",
        rate = sy.Rate.HZ * 50,

    )
    analog_read_task.config.channels.append(ai_chan)
    print("Added channel:", channel_num)


def process_pi(row: pd.Series, digital_read_task: ni.DigitalReadTask, card: sy.Device):
    device_name = row["Name"]
    line = int(row["Channel"])
    port = 0

    BCLS_di_time = client.channels.create(
        name="BCLS_di_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )

    pi_chan = client.channels.create(
        name=f"{device_name}",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        index=BCLS_di_time.key,
        rate=sy.Rate.HZ * 50,
    )

    di_chan = ni.DIChan(
        channel=pi_chan.key,
        port=0,
        line=line,
    )

    digital_read_task.config.channels.append(di_chan)
    print("Added channel:", line)

# TODO: combine TC & PT processing (they are the same except for the scale)