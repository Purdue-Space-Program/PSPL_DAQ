import synnax as sy 
import time
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] Valve Sim: {message}")

def valve_simulator():
    try:
        client = sy.Synnax(
            host="128.46.118.59",
            port=9090,
            username="Bill",
            password="Bill",
            secure=False,
        )
        log("Connected to Synnax system.")
    except Exception as e:
        log(f"Failed to connect to Synnax system: {str(e)}")
        return

    # assign channels
    total_shutdown_channel = client.channels.create(
        name="HBR_ALL_SHUTDOWN",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    tank_vent_cmd_channel = client.channels.create(
        name="SV-N2-TANK-VENT_cmd",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    tank_vent_state_channel = client.channels.create(
        name="SV-N2-TANK-VENT_state2",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    n2_run_cmd_channel = client.channels.create(
        name="PV-N2-RUN_cmd",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    n2_run_state_channel = client.channels.create(
        name="PV-N2-RUN_state2",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    eth_inlet_cmd_channel = client.channels.create(
        name="PV-ETH-INLET_cmd",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    eth_inlet_state_channel = client.channels.create(
        name="PV-ETH-INLET_state2",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    eth_outlet_cmd_channel = client.channels.create(
        name="PV-ETH-OUTLET_cmd",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    eth_outlet_state_channel = client.channels.create(
        name="PV-ETH-OUTLET_state2",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    n2_run_pi_channel = client.channels.create(
        name="PI-N2-RUN2",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    eth_inlet_pi_channel = client.channels.create(
        name="PI-ETH-INLET2",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    eth_outlet_pi_channel = client.channels.create(
        name="PI-ETH-OUTLET2",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    tank_vent_cmd_key = tank_vent_cmd_channel.key
    tank_vent_state_key = tank_vent_state_channel.key
    n2_run_cmd_key = n2_run_cmd_channel.key
    n2_run_state_key = n2_run_state_channel.key
    eth_inlet_cmd_key = eth_inlet_cmd_channel.key
    eth_inlet_state_key = eth_inlet_state_channel.key
    eth_outlet_cmd_key = eth_outlet_cmd_channel.key
    eth_outlet_state_key = eth_outlet_state_channel.key
    n2_run_pi_key = n2_run_pi_channel.key
    eth_inlet_pi_key = eth_inlet_pi_channel.key
    eth_outlet_pi_key = eth_outlet_pi_channel.key

    shutdown_key = total_shutdown_channel.key

    # Initial state
    vent_valve_open = False
    run_valve_open = False
    inlet_valve_open = False
    outlet_valve_open = False
    shutdown_flag = False

    with client.open_streamer([shutdown_key, tank_vent_cmd_key, n2_run_cmd_key, eth_inlet_cmd_key, eth_outlet_cmd_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[tank_vent_state_key, n2_run_state_key, eth_inlet_state_key, eth_outlet_state_key, n2_run_pi_key, eth_inlet_pi_key, eth_outlet_pi_key], enable_auto_commit=True) as writer:
        
        log("Valve simulator is running. Waiting for command...")

        for frame in streamer:
            for v in frame[tank_vent_cmd_key]:
                if v == 1:   
                    vent_valve_open = True
                elif v == 0:
                    vent_valve_open = False
            for v in frame[n2_run_cmd_key]:
                if v == 1:   
                    run_valve_open = True
                elif v == 0:
                    run_valve_open = False
            for v in frame[eth_inlet_cmd_key]:
                if v == 1:   
                    inlet_valve_open = True
                elif v == 0:
                    inlet_valve_open = False
            for v in frame[eth_outlet_cmd_key]:
                if v == 1:   
                    outlet_valve_open = True
                elif v == 0:
                    outlet_valve_open = False
            for v in frame[shutdown_key]:
                if v == 1:
                    shutdown_flag = True

            writer.write({tank_vent_state_key: [1 if vent_valve_open else 0]})
            writer.write({n2_run_state_key: [1 if run_valve_open else 0]})
            writer.write({eth_inlet_state_key: [1 if inlet_valve_open else 0]})
            writer.write({eth_outlet_state_key: [1 if outlet_valve_open else 0]})
            writer.write({n2_run_pi_key: [1 if run_valve_open else 0]})
            writer.write({eth_inlet_pi_key: [1 if inlet_valve_open else 0]})
            writer.write({eth_outlet_pi_key: [1 if outlet_valve_open else 0]})
            
            if shutdown_flag:
                writer.write({tank_vent_state_key: [0]})
                writer.write({n2_run_state_key: [0]})
                writer.write({eth_inlet_state_key: [0]})
                writer.write({eth_outlet_state_key: [0]})
                writer.write({n2_run_pi_key: [0]})
                writer.write({eth_inlet_pi_key: [0]})
                writer.write({eth_outlet_pi_key: [0]})
                break

if __name__ == "__main__":
    valve_simulator()