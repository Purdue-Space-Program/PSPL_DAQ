import synnax as sy # type: ignore
from datetime import datetime

ENERGIZE = 0
DEENERGIZE = 1
import time

def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"Test: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})

def read_data():
    #aquire synnax connection
    try:
        client = sy.Synnax(
            host="128.46.118.59",
            port=9090,
            username="Bill",
            password="Bill",
            secure=False,
        )
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {f"Failed to connect to Synnax system for trigger monitoring: {str(e)}"}")
        return

    log_channel = client.channels.create(
        name="HBR_LOG",
        data_type="String",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    total_shutdown_channel = client.channels.create(
        name="HBR_ALL_SHUTDOWN",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    pt_test_channel = client.channels.create(
        name="PT-N2-01",
        data_type="Float32",
        virtual=False,
        retrieve_if_name_exists=True,
    )

    valve_test_state_channel = client.channels.create(
        name="PV-ETH-INLET_cmd",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    valve_test_cmd_channel = client.channels.create(
        name="SV-N2-TANK-VENT_cmd",
        data_type="uint8",
        virtual=False,
        retrieve_if_name_exists=True,
    )

    log_key = log_channel.key
    pt_test_key = pt_test_channel.key
    shutdown_key = total_shutdown_channel.key
    valve_state_key = valve_test_state_channel.key
    valve_cmd_key = valve_test_cmd_channel.key

    shutdown_flag = False
    open_flag = False

    with client.open_streamer([pt_test_key, shutdown_key, valve_cmd_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[log_key, valve_state_key], enable_auto_commit=True) as writer:
        
        log_event("Connected to Synnax for trigger monitoring", writer, log_key)
        log_event("Listening for trigger signals", writer, log_key)

        for frame in streamer:
            '''
            for v in frame[pt_test_key]:
                log_event(v, writer, log_key)
            '''
            for v in frame[valve_cmd_key]:
                log_event(f"cmd: {v}", writer, log_key)
                if v == 1:
                    open_flag = True
                else:
                    open_flag = False
            for v in frame[shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            writer.write({valve_state_key: [1 if open_flag else 0]})
            if shutdown_flag:
                log_event('Shutting down test script', writer, log_key)
                break  


if __name__ == "__main__":
    read_data()    