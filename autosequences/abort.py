import synnax as sy # type: ignore
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'PSPL_CMS_AVIONICS_COTS_FSW', 'tools')))

import command as cmd # type: ignore

ENERGIZE = 0
DEENERGIZE = 1

onboard_active = False


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
            host="10.165.89.106",
            port=2701,
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

        DELUGE_CMD = "DELUGE_cmd"
        DELUGE_STATE = "DELUGE_state"

        PURGE_CMD = "SV-N2-02_cmd"
        PURGE_STATE = "SV-N2-02_state"

        ACTUATOR_CMD = "ACTUATOR_cmd"
        ACTUATOR_STATE = "ACTUATOR_state"

        if onboard_active:
            cmd.send_command("abort")
            log_event("Start command sent to Rocketside system", writer, log_key)

        with client.control.acquire(
            name="Abort Sequence",
            write_authorities=[230],
            write=[IGNITOR_CMD, DELUGE_CMD, PURGE_CMD, ACTUATOR_CMD],
            read=[IGNITOR_STATE, DELUGE_STATE, PURGE_STATE, ACTUATOR_STATE],
        ) as ctrl:
            log_event('Abort initiated', writer, log_key)

            # Mark the start of the sequence
            start = sy.TimeStamp.now()

            ctrl[DELUGE_CMD] = ENERGIZE
            ctrl[PURGE_CMD] = ENERGIZE

            ctrl[ACTUATOR_CMD] = DEENERGIZE
            ctrl[IGNITOR_CMD] = DEENERGIZE

            #close bbs

            ctrl.sleep(15)

            ctrl[DELUGE_CMD] = DEENERGIZE

                # Wait until the deluge is shutoff
            if ctrl.wait_until(
                lambda c: c[DELUGE_STATE] == DEENERGIZE,
                timeout=10 * sy.TimeSpan.SECOND, 
            ):
                log_event("Deluge shutoff sucessfull", writer, log_key)
            else:
                log_event("Failed to shutoff deugle within timeout", writer, log_key)
            
            ctrl[PURGE_CMD] = DEENERGIZE

            # Wait until the N2 purge is shotoff
            if ctrl.wait_until(
                lambda c: c[PURGE_STATE] == DEENERGIZE,
                timeout=10 * sy.TimeSpan.SECOND, 
            ):
                log_event("N2 Purge shutoff sucessfull", writer, log_key)
            else:
                log_event("Failed to shutoff N2 Purge within timeout", writer, log_key)

            # Mark the end of the sequence
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
            host="10.165.89.106",
            port=2701,
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

    log_channel = client.channels.create(
        name="BCLS_LOG",
        data_type="String",
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
    log_key = log_channel.key

    arm_flag = False
    active_flag = True
    shutdown_flag = False

    with client.open_streamer([arm_key, abort_key,  shutdown_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[armed_state_key, status_key, abort_active_key, sequence_active_key, log_key], enable_auto_commit=True) as writer:
        
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