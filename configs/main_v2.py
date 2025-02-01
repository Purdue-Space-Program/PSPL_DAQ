import pandas as pd
import synnax as sy
from synnax.hardware import ni
from configs.processing import process_vlv


client = sy.Synnax(
    host = "128.46.118.59",
    port = 9090,
    username = "Bill",
    password = "Bill",
)


def main():
    dev_5 = client.hardware.devices.retrieve(model="USB-6343", location="Dev5")
    dev_6 = client.hardware.devices.retrieve(model="USB-6343", location="Dev6")

    data = input_csv("test_configuration.csv")
    analog_read_task, digital_write_task, digital_read_task = create_tasks(dev_5)

    process_excel(data, analog_read_task, digital_write_task, digital_read_task, dev_5)

    if digital_write_task.config.channels:
        print("Attempting to configure digital write task...")
        client.hardware.tasks.configure(task=digital_write_task, timeout=5)
        print("Digital write task configured.")
    else:
        print("No channels added to digital write task.")




def create_tasks(card: sy.Device):

    analog_read_task = None
    try:
        analog_read_task = client.hardware.tasks.retrieve(name="Analog Input")
    except:
        analog_read_task = None

    if analog_read_task is None:
        print("Creating new analog read task...")
        analog_read_task = ni.AnalogReadTask(
            name="Analog Input",
            device=card.key,
            sample_rate=sy.Rate.HZ * 1000,
            stream_rate=sy.Rate.HZ * 100,
            data_saving=True,
            channels=[],
        )


    digital_write_task = None
    try:
        digital_write_task = client.hardware.tasks.retrieve(name="Digital Output")
    except:
        digital_write_task = None

    if digital_write_task is None:
        print("Creating new digital write task...")
        digital_write_task = ni.DigitalWriteTask(
            name="Digital Output",
            device=card.key,
            state_rate=sy.Rate.HZ * 1000,
            data_saving=True,
            channels=[],
        )
    digital_write_task = client.hardware.tasks.retrieve(name="Digital Output")


    digital_read_task = None
    try:
        digital_read_task = client.hardware.tasks.retrieve(name="Digital Input")
    except:
        digital_read_task = None
    if digital_read_task is None:
        print("Creating new digital read task...")
        digital_read_task = ni.DigitalReadTask(
            name="Digital Input",
            device=card.key,
            sample_rate=sy.Rate.HZ * 1000,
            stream_rate=sy.Rate.HZ * 100,
            data_saving=True,
            channels=[],
        )


    return analog_read_task, digital_write_task, digital_read_task


def input_csv(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError as e:
        print("File not found:", e)
        return
    except ValueError as e:
        print("Invalid CSV file or format:", e)
        return
    except Exception as e:
        print("Check sheet read in:", e)
        return

    print("CSV file succesfully read.")
    return df.head(300)

def process_excel(file: pd.DataFrame, analog_read_task, digital_write_task, digital_read_task, card: sy.Device):

    print("Processing data...")

    for _, row in file.iterrows():
        try:
            if row["Sensor Type"] == "VLV":
                process_vlv(row, digital_write_task, card)
            # elif row["Sensor Type"] == "PT":
            #     process_pt(row, analog_read_task, card)
            # elif row["Sensor Type"] == "TC":
            #     process_tc(row, analog_task, analog_card)
            # elif row["Sensor Type"] == "LC":
            #     process_lc(row, analog_task, analog_card)
            # # elif (
            # #     row["Sensor Type"] == "RAW"
            # # ):  # for thermister and other raw voltage data
            # #     process_raw(row, analog_task, analog_card)
            # else:
            #     print(f"Sensor type {row["Sensor Type"]} not recognized")
        except KeyError as e:
            print(f"Missing column in row: {e}")
            return
        except Exception as e:
            print(f"Error populating tasks: {e}")


if __name__ == "__main__":
    main()