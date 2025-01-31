import pandas as pd
import synnax as sy
from synnax import DataType
from synnax.hardware.ni import *
import numpy as np
from synnax.hardware.device import Device

client = sy.Synnax(
    host = "128.46.118.59",
    port = 9090,
    username = "Bill",
    password = "Bill",
)

DEBUG = False

dev_5 = client.hardware.devices.retrieve(model="USB-6343", location="Dev6") #
dev_6 = client.hardware.devices.retrieve(model="USB-6343", location="Dev6")

if DEBUG:
    print("Device 5 = ", dev_5)
    print("Device 6 = ", dev_6)
if not dev_5 or not dev_6:
    print("One or both devices not found, please configure manually.")
    exit(1)


# Create analog task
analog_read_task = None

try:
    analog_task = client.hardware.tasks.retrieve(name="Analog Read Task")
except:
    analog_task = None

if analog_task is None:
    print("New analog task is being created.")
    analog_task = AnalogReadTask(
        name = "Analog Read Task",
        sample_rate = sy.Rate.HZ * 1000,
        stream_rate = sy.Rate.HZ * 100,
        data_saving=True,
        channels = []
    )
    client.hardware.tasks.create([analog_task])

if DEBUG:
    print("Analog task = ", analog_task)


# Create digital read task
digital_read_task = None
try:
    digital_read_task = client.hardware.tasks.retrieve(name="Digital Read Task")
except:
    digital_read_task = None
if digital_read_task is None:
    print("New digital read task is being created.")
    digital_task = DigitalReadTask(
        name = "Digital Read Task",

        sample_rate = sy.Rate.HZ * 1000,
        stream_rate = sy.Rate.HZ * 100,
        data_saving=True,
        channels = []
    )
    client.hardware.tasks.create([digital_read_task])
if DEBUG:
    print("Digital task = ", digital_read_task)


# Create digital write task
digital_write_task = None
try:
    digital_write_task = client.hardware.tasks.retrieve(name="Digital Write Task")
except:
    digital_write_task = None
if digital_write_task is None:
    print("New digital write task is being created.")
    digital_write_task = DigitalWriteTask(
        name = "Digital Write Task",
        device = dev_5.key,
        state_rate=sy.Rate.HZ * 1000,
        data_saving=True,
        channels = []
    )
    client.hardware.tasks.create([digital_write_task])
if DEBUG:
    print("Digital task = ", digital_write_task)



def input_excel(file_path: str):
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError as e:
        print("File not found:", e)
        return
    except ValueError as e:
        print("Invalid Excel file or format:", e)
        return
    except Exception as e:
        print("Unexpected error:", e)
        return

    print("Excel file succesfully read")
    return df.head(300)

def process_excel(file: pd.DataFrame):
    print(f"reading {len(file)} rows")
    for _, row in file.iterrows():
        try:
            if row["Sensor Type"] == "VLV":
                populate_digital_out(row)
            # elif row["Sensor Type"] in ["PT", "TC", "LC"]:
            #     populate_analog(row)
            else:
                print("Unexpected sensor type:", row["Sensor Type"])
        except KeyError as e:
            print(f"Missing column in row: {e}")
            return
        except Exception as e:
            print(f"Unexpected error populating tasks: {e}")

#
# def populate_digital_out(row):
#     print(f"processing row: {row}")
#     channel = int(row["Channel"])
#
#     bcls_state_time = client.channels.create(
#         name="bcls_state_time",
#         is_index=True,
#         data_type=sy.DataType.TIMESTAMP,
#         retrieve_if_name_exists=True,
#     )
#
#     state_chan = client.channels.create(
#         name = f"bcls_state_{channel}",
#         data_type = sy.DataType.UINT8,
#         retrieve_if_name_exists=True,
#         index=bcls_state_time.key,
#     )
#
#     cmd_chan = client.channels.create(
#         name = f"bcls_vlv_{channel}",
#         data_type = sy.DataType.UINT8,
#         retrieve_if_name_exists=True,
#     )
#
#     do_channel = DOChan(
#         cmd_channel = cmd_chan.key,
#         state_channel = state_chan.key,
#         port=0,
#         line=channel
#     )
#
#     digital_task.config.channels.append(do_channel)
#     print("Digital task succesfully populated.")
#
#


data = input_excel("test_configuration.xlsx")

# process_excel(data)

