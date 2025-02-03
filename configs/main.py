from random import sample

import pandas as pd
import synnax as sy
from synnax.hardware import ni
from synnax.io.factory import READERS
from configs.processing import process_analog_input, process_digital_input, process_digital_output


SAMPLE_RATE = 1000 # Hz
STREAM_RATE = 100 # Hz

DEV_5_DATA_WIRING_FILEPATH = "CMS_Data_Wiring_Dev5.xlsx"
DEV_5_CONTROL_WIRING_FILEPATH = "CMS_Control_Wiring_Dev5.xlsx"

DEV_6_DATA_WIRING_FILEPATH = "CMS_Data_Wiring_Dev6.xlsx"
DEV_6_CONTROL_WIRING_FILEPATH = "CMS_Control_Wiring_Dev6.xlsx"

# TODO: Add zeroin data and fix tare = 14.7


# Connect to Synnax
client = sy.Synnax(
    host = "128.46.118.59",
    port = 9090,
    username = "Bill",
    password = "Bill",
)


def main():
    dev_5 = client.hardware.devices.retrieve(model="USB-6343", location="Dev5")
    dev_6 = client.hardware.devices.retrieve(model="USB-6343", location="Dev6")


    # Dev 5 Data
    dev_5_data_wiring = input_excel(DEV_5_DATA_WIRING_FILEPATH)
    dev_5_control_wiring = input_excel(DEV_5_CONTROL_WIRING_FILEPATH)

    # Dev 6 Data
    dev_6_data_wiring = input_excel(DEV_6_DATA_WIRING_FILEPATH)
    dev_6_control_wiring = input_excel(DEV_6_CONTROL_WIRING_FILEPATH)



    # Create tasks
    dev_5_analog_read_task, dev_5_digital_write_task, dev_5_digital_read_task = create_tasks(dev_5)
    dev_6_analog_read_task, dev_6_digital_write_task, dev_6_digital_read_task = create_tasks(dev_6)

    # Process data
    print("Processing data...")

    process_analog_input(dev_5_data_wiring, dev_5_analog_read_task, dev_5, stream_rate=STREAM_RATE, sample_rate=SAMPLE_RATE)
    process_analog_input(dev_6_data_wiring, dev_6_analog_read_task, dev_6, stream_rate=STREAM_RATE, sample_rate=SAMPLE_RATE)

    process_digital_input(dev_5_data_wiring, dev_5_digital_read_task, dev_5, stream_rate=STREAM_RATE, sample_rate=SAMPLE_RATE)
    process_digital_input(dev_6_data_wiring, dev_6_digital_read_task, dev_6, stream_rate=STREAM_RATE, sample_rate=SAMPLE_RATE)

    process_digital_output(dev_5_control_wiring, dev_5_digital_write_task, dev_5, stream_rate=STREAM_RATE, sample_rate=SAMPLE_RATE)
    process_digital_output(dev_6_control_wiring, dev_6_digital_write_task, dev_6, stream_rate=STREAM_RATE, sample_rate=SAMPLE_RATE)




    if dev_5_digital_write_task.config.channels:
        print("Attempting to configure digital write task...")
        client.hardware.tasks.configure(task=dev_5_digital_write_task, timeout=5)
        print("Digital write task configured.")
    else:
        print("No channels added to digital write task.")

    if dev_6_digital_write_task.config.channels:
        print("Attempting to configure digital write task...")
        client.hardware.tasks.configure(task=dev_6_digital_write_task, timeout=5)
        print("Digital write task configured.")
    else:
        print("No channels added to digital write task.")


    if dev_5_analog_read_task.config.channels:
        print("Attempting to configure analog read task...")
        client.hardware.tasks.configure(task=dev_5_analog_read_task, timeout=5)
        print("Dev 5 Analog read task configured.")
    else:
        print("No channels added to analog read task.")

    if dev_6_analog_read_task.config.channels:
        print("Attempting to configure analog read task...")
        client.hardware.tasks.configure(task=dev_6_analog_read_task, timeout=5)
        print("Dev 6 Analog read task configured.")
    else:
        print("No channels added to analog read task.")


    if dev_5_digital_read_task.config.channels:
        print("Attempting to configure digital read task...")
        client.hardware.tasks.configure(task=dev_5_digital_read_task, timeout=5)
        print("Digital read task configured.")
    else:
        print("No channels added to digital read task.")

    if dev_6_digital_read_task.config.channels:
        print("Attempting to configure digital read task...")
        client.hardware.tasks.configure(task=dev_6_digital_read_task, timeout=5)
        print("Digital read task configured.")
    else:
        print("No channels added to digital read task.")






def create_tasks(card: sy.Device):

    card_name = card.location

    try:
        analog_read_task = client.hardware.tasks.retrieve(name=f"{card_name} Analog Input")
    except:
        analog_read_task = None

    if analog_read_task is not None:
        client.hardware.tasks.delete(analog_read_task.key)

    print("Creating new analog read task...")
    analog_read_task = ni.AnalogReadTask(
        name=f"{card_name} Analog Input",
        device=card.key,
        sample_rate=sy.Rate.HZ * SAMPLE_RATE,
        stream_rate=sy.Rate.HZ * STREAM_RATE,
        data_saving=True,
        channels=[],
    )


    try:
        digital_write_task = client.hardware.tasks.retrieve(name=f"{card_name} Digital Output")
    except:
        digital_write_task = None
    if digital_write_task is not None:
        client.hardware.tasks.delete(digital_write_task.key)


    print("Creating new digital write task...")
    digital_write_task = ni.DigitalWriteTask(
        name=f"{card_name} Digital Output",
        device=card.key,
        state_rate=sy.Rate.HZ * SAMPLE_RATE,
        data_saving=True,
        channels=[],
    )

    try:
        digital_read_task = client.hardware.tasks.retrieve(name=f"{card_name} Digital Input")
    except:
        digital_read_task = None
    if digital_read_task is not None:
        client.hardware.tasks.delete(digital_read_task.key)

    print("Creating new digital read task...")
    digital_read_task = ni.DigitalReadTask(
        name=f"{card_name} Digital Input",
        device=card.key,
        sample_rate=sy.Rate.HZ * SAMPLE_RATE,
        stream_rate=sy.Rate.HZ * STREAM_RATE,
        data_saving=True,
        channels=[],
    )


    return analog_read_task, digital_write_task, digital_read_task


def input_excel(file_path: str):
    """
    Reads all sheets from an Excel file into a dictionary of DataFrames.
    Transposes the 'Header' sheet.

    Parameters:


    """


    try:
        excel_file = pd.ExcelFile(file_path)
    except FileNotFoundError as e:
        print("File not found:", e)
        return
    except ValueError as e:
        print("Invalid EXCEL file or format:", e)
        return
    except Exception as e:
        print("Check sheet read in:", e)
        return

    print("EXCEL file succesfully read.")



    return excel_file



if __name__ == "__main__":
    main()