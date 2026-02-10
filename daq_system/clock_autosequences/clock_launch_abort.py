import synnax as sy # type: ignore
from datetime import datetime
import sys
import os
import command as cmd # type: ignore
import time

ENERGIZE = 0
DEENERGIZE = 1

onboard_active = True

def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"Abort: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})

# Manual abort sequence
def run_abort(writer, log_key):
    # Connect to the Synnax system
    try:
        client = sy.Synnax(
            host="192.168.2.59",
            port=9090,
            username="Bill",
            password="Bill",
            secure=False,  # Ensure secure is set to False unless your system requires it
        )
        log_event("Connected to Synnax system", writer, log_key)
    except Exception as e:
        log_event(f"Failed to connect to Synnax system: {str(e)}", writer, log_key)
        return


    try:
        # Define the control channel names
        IGNITOR_CMD = "IGNITOR_cmd"
        IGNITOR_STATE = "IGNITOR_state"

        PURGE_CMD = "SV_N2_01_cmd"
        PURGE_STATE = "SV_N2_01_state"

        ACTUATOR_CMD = "ACTUATOR_cmd"
        ACTUATOR_STATE = "ACTUATOR_state"

        STOP_CLOCK = "SET_T_CLOCK_ENABLE"
        DISARM_SEQUENCE = "ARM_AUTO"
        RUN_ABORT = "RUN_ABORT"

        if onboard_active:
            cmd.send_command("abort")
            log_event("Start command sent to Rocketside system", writer, log_key)

        with client.control.acquire(
            name="Abort Sequence",
            write_authorities=[202],
            write=[IGNITOR_CMD, PURGE_CMD, ACTUATOR_CMD, STOP_CLOCK, DISARM_SEQUENCE],
            read=[IGNITOR_STATE, PURGE_STATE, ACTUATOR_STATE, RUN_ABORT],
        ) as ctrl:
            log_event('Abort initiated', writer, log_key)

            # Mark the start of the sequence
            start = sy.TimeStamp.now()

            ctrl[STOP_CLOCK] = 0
            ctrl[DISARM_SEQUENCE] = 0

            ctrl[PURGE_CMD] = ENERGIZE

            ctrl[ACTUATOR_CMD] = DEENERGIZE
            ctrl[IGNITOR_CMD] = DEENERGIZE

            if not ctrl.wait_until_defined(
                [RUN_ABORT], timeout=60
            ):
                print(1)
            else:
                return
            
            #Mark the end of the sequence
            end = sy.TimeStamp.now()
            # Label the sequence with the end time
            client.ranges.create(
                name=f"Abort Sequence {end}",
                time_range=sy.TimeRange(start=start, end=end),
            )
            log_event(f"Abort Sequence completed: {start} to {end}", writer, log_key)
    except Exception as e:
        log_event(f"Error occurred during sequence execution: {str(e)}", writer, log_key)

def wait_for_trigger():
    #aquire synnax connection
    try:
        client = sy.Synnax(
            host="192.168.2.59",
            port=9090,
            username="Bill",
            password="Bill",
            secure=False,
        )
        
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {f"Failed to connect to Synnax system for trigger monitoring: {str(e)}"}")
        return

    # Check for channels
    arm_channel = client.channels.create(
        name="ARM_ABORT",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    abort_channel = client.channels.create(
        name="RUN_ABORT",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    shutdown_channel = client.channels.create(
        name="SEQUENCE_SHUTDOWN",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    abort_active_channel = client.channels.create(
        name="ABORT_ACTIVE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    sequence_active_channel = client.channels.create(
        name="SEQUENCE_ACTIVE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    status_channel = client.channels.create(
        name="ABORT_STATUS",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    armed_state_channel = client.channels.create(
        name="ABORT_ARMED_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    fu_redline_channel = client.channels.create(
        name="FU_UPPER_REDLINE_HIT",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    ox_redline_channel = client.channels.create(
        name="OX_UPPER_REDLINE_HIT",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    status_log_channel = client.channels.create(
        name="STATUS_LOG",
        data_type="String",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    log_channel = client.channels.create(
        name="BCLS_LOG",
        data_type="String",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    t_clock_channel = client.channels.create(
        name="T_CLOCK_MS",
        data_type="int64",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    arm_key = arm_channel.key
    abort_key = abort_channel.key
    shutdown_key = shutdown_channel.key
    status_key = status_channel.key
    armed_state_key = armed_state_channel.key
    abort_active_key = abort_active_channel.key
    sequence_active_key = sequence_active_channel.key
    fu_redline_key = fu_redline_channel.key
    ox_redline_key = ox_redline_channel.key
    log_key = log_channel.key
    t_clock_key = t_clock_channel.key
    status_log_key = status_log_channel.key

    arm_flag = False
    active_flag = True
    shutdown_flag = False

    with client.open_streamer([arm_key, abort_key,  shutdown_key, fu_redline_key, ox_redline_key, t_clock_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[armed_state_key, status_key, abort_active_key, sequence_active_key, log_key, status_log_key], enable_auto_commit=True) as writer:
        
        log_event("Connected to Synnax for trigger monitoring", writer, log_key)
        log_event("Listening for trigger signals", writer, log_key)
        writer.write({status_key: [1]})
        for frame in streamer:
            for v in frame[shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            for v in frame[arm_key]:
                if v == 1:
                    arm_flag = True
                    log_event('Abort Armed.', writer, log_key)
                elif v == 0:
                    arm_flag = False
                    log_event('Abort Disarmed.', writer, log_key)  
            for v in frame [fu_redline_key]:
                if v == 1 and arm_flag:
                    log_event("Fu upper pressure redline hit, starting abort sequence", writer, log_key)
                    writer.write({status_key: [0]})
                    writer.write({abort_active_key: [1]})
                    writer.write({sequence_active_key: [0]})
                    run_abort(writer, log_key)
                    writer.write({status_key: [1]})
                    writer.write({abort_active_key: [0]})

            for v in frame [ox_redline_key]:
                if v == 1 and arm_flag:
                    log_event("Ox upper pressure redline hit, starting abort sequence", writer, log_key)
                    writer.write({status_key: [0]})
                    writer.write({abort_active_key: [1]})
                    writer.write({sequence_active_key: [0]})
                    run_abort(writer, log_key)
                    writer.write({status_key: [1]})
                    writer.write({abort_active_key: [0]})

            for v in frame[abort_key]:
                if arm_flag and active_flag and v == 1:
                    log_event("Trigger received, starting abort sequence", writer, log_key)
                    writer.write({status_key: [0]})
                    writer.write({abort_active_key: [1]})
                    writer.write({sequence_active_key: [0]})
                    run_abort(writer, log_key)
                    writer.write({status_key: [1]})
                    writer.write({abort_active_key: [0]})
                
            writer.write({armed_state_key: [1 if arm_flag else 0]})
            writer.write({status_key: [1 if active_flag else 0]})

            if shutdown_flag:
                writer.write({status_key: [0]})
                writer.write({armed_state_key: [0]})
                log_event('Shutting down abort', writer, log_key)
                break

if __name__ == "__main__":
    wait_for_trigger()    