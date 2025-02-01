import synnax as sy
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

    BCLS_state_time = client.channels.create(
        name="BCLS_state_time",
        is_index=True,
        data_type=sy.DataType.TIMESTAMP,
        retrieve_if_name_exists=True,
    )
    state_chan = client.channels.create(
        name=f"BCLS_state_{channel}",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        index=BCLS_state_time.key,
        rate=sy.Rate.HZ * 1000,

    )

    cmd_chan = client.channels.create(
        name=f"BCLS_cmd_{channel}",
        data_type=sy.DataType.UINT8,
        retrieve_if_name_exists=True,
        rate=sy.Rate.HZ * 1000,
    )

    do_chan = ni.DOChan(
        cmd_channel=cmd_chan.key,
        state_channel=state_chan.key,
        port = 0,
        line = channel,
        rate=sy.Rate.HZ * 1000,
    )

    digital_write_task.config.channels.append(do_chan)
    print("Added channel:", channel)

