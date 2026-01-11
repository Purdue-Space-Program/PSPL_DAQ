from logging import NOTSET, DEBUG, INFO, WARN, WARNING, ERROR, FATAL, CRITICAL
import synnax as sy
import pandas as pd
from pathlib import Path
import logging

# Common Synnax client
sy_client = sy.Synnax(
    host= "192.168.2.147",
    port= "9090",
    username= "Bill",
    password= "Bill",
    secure=False,
)
def get_synnax_client():
    return sy_client

telem_config_df = pd.read_excel(Path(__file__).parent / 'CMS_Avionics_Channels.xlsx', sheet_name='telem_channels')
def get_telem_configs():
    return telem_config_df

command_config_df = pd.read_excel(Path(__file__).parent / 'CMS_Avionics_Channels.xlsx', sheet_name='command_channels')
def get_command_configs():
    return command_config_df

LOGGING_FORMAT = '[%(levelname)s] %(name)s: %(message)s'

log_channel = sy_client.channels.create(
    name="avi_logs",
    data_type=sy.DataType.STRING,
    virtual=True,
    retrieve_if_name_exists=True,
)

writer = sy_client.open_writer(
    start=sy.TimeStamp.now(),
    channels=[log_channel.key],
)
def get_logger(name: str):
    class SynnaxLogger:
        def __init__(self, name: str) -> None:
            self.name = name

        def info(self, msg: str):
            writer.write({
                log_channel.key: f'[INFO] ({self.name}) {msg}',
            })

        def error(self, msg: str):
            writer.write({
                log_channel.key: f'[ERROR] ({self.name}) {msg}',
            })

    return SynnaxLogger(name)

