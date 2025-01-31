import synnax as sy
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
