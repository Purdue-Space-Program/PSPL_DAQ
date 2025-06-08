import synnax as sy # type: ignore
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'PSPL_CMS_AVIONICS_COTS_FSW', 'tools')))
import command as cmd  # type: ignore

ENERGIZE = 0
DEENERGIZE = 1

onboard_active = False


def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"Auto: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})


# Main autosequence
def run_sequence(writer, log_key):
    """Execute the Hot Fire Auto Sequence with control logic."""
    # Connect to the Synnax system
    try:
        client = sy.Synnax(
            host="128.46.118.59",
            port=9090,
            username="Bill",
            password="Bill",
            secure=False,  # Ensure secure is set to False unless your system requires it
        )
        log_event("Connected to Synnax system", writer, log_key)
    except Exception as e:
        log_event(f"Failed to connect to Synnax system: {str(e)}", writer, log_key)
        return

    # Define the control channel names
    IGNITOR_CMD = "IGNITOR_cmd"
    IGNITOR_STATE = "IGNITOR_state"

    DELUGE_CMD = "DELUGE_cmd"
    DELUGE_STATE = "DELUGE_state"

    PURGE_CMD = "SV-N2-02_cmd"
    PURGE_STATE = "SV-N2-02_state"

    ACTUATOR_CMD = "ACTUATOR_cmd"
    ACTUATOR_STATE = "ACTUATOR_state"

    log_event("Starting Hot Fire Auto Sequence", writer, log_key)
    if onboard_active:
        cmd.send_command("start")
        log_event("Start command sent to Rocketside system", writer, log_key)

    try:
        # Open a control sequence under a context manager, so control is released when done
        with client.control.acquire(
            name="Hot Fire Auto Sequence",
            write=[IGNITOR_CMD, DELUGE_CMD, PURGE_CMD, ACTUATOR_CMD],
            read=[IGNITOR_STATE, DELUGE_STATE, PURGE_STATE, ACTUATOR_STATE],
            write_authorities=[200],  # Set high authority to prevent interference
        ) as ctrl:
            log_event("Control sequence acquired", writer, log_key)

            # Mark the start of the sequence
            start = sy.TimeStamp.now()

            # Start the N2 purge at T-5
            log_event("Activating N2-Purge", writer, log_key)
            ctrl[PURGE_CMD] = ENERGIZE

            # Wait until the N2 Purge activates
            if ctrl.wait_until(
                lambda c: c[PURGE_STATE] == ENERGIZE,
                timeout = 5 * sy.TimeSpan.SECOND,
            ):
                log_event("N2 Purge Sucessfully Activated", writer, log_key)
            else:
                # Shutdown and abort autosequence if purge fails to open
                ctrl[PURGE_CMD] = DEENERGIZE
                log_event('N2 Purge failed to start, Autosequence aborted', writer, log_key)
                return

            # Activate the Water Deluge at T-3
            ctrl.sleep(2)
            log_event("Activating Water Deluge", writer, log_key)
            ctrl[DELUGE_CMD]= ENERGIZE

            # Wait until the Water Deluge activates
            if ctrl.wait_until(
                lambda c: c[DELUGE_STATE] == ENERGIZE,
                timeout = 5 * sy.TimeSpan.SECOND,
            ):
                log_event("Water Deluge Sucessfully Activated", writer, log_key)
            else:
                # Shutdown and abort autosequence if Deluge fails to open
                ctrl[DELUGE_CMD] = DEENERGIZE
                ctrl[PURGE_CMD] = DEENERGIZE
                log_event('Water Deluge failed to start, Autosequence aborted', writer, log_key)
                return
            
            # Fire the Ignitor at T-0
            ctrl.sleep(3)
            log_event("Firing Ignitor Pyro", writer, log_key)
            ctrl[IGNITOR_CMD] = ENERGIZE

            # Check for ignition
            if ctrl.wait_until(
                lambda c: c[IGNITOR_STATE] == ENERGIZE,
                timeout = 2 * sy.TimeSpan.SECOND,
            ):
                log_event("Ignitor Pyro Fired", writer, log_key)
            else:
                # Shutdown and abort autosequence if ignitor does not fire
                ctrl[IGNITOR_CMD] = DEENERGIZE
                log_event("Ignitor Ignition Failed, aborting Autosequence", writer, log_key)
                ctrl.sleep(3)
                ctrl[DELUGE_CMD] = DEENERGIZE
                ctrl[PURGE_CMD] = DEENERGIZE
                log_event('Autosequence Aborted', writer, log_key)
                return

            # Fire the Actuator pyro at T+3
            ctrl.sleep(3)
            log_event("Firing Actuator Pyro", writer, log_key)
            ctrl[ACTUATOR_CMD] = ENERGIZE

            # Check for Actuator firing
            if ctrl.wait_until(
                lambda c: c[ACTUATOR_STATE] == ENERGIZE,
                timeout = 2 * sy.TimeSpan.SECOND,
            ):
                log_event("Actuator Fired", writer, log_key)
            else:
                # Shutdown and abort autosequence if Actuator fails
                ctrl[ACTUATOR_CMD] = DEENERGIZE
                ctrl[IGNITOR_CMD] = DEENERGIZE
                log_event("Actuator failed to fire, aborting Autosequence", writer, log_key)
                ctrl.sleep(3)
                ctrl[DELUGE_CMD] = DEENERGIZE
                ctrl[PURGE_CMD] = DEENERGIZE
                log_event('Autosequence Aborted', writer, log_key)
                return

            ctrl.sleep(15)

            # deenergize system
            # deenergize actuator
            ctrl[ACTUATOR_CMD] = DEENERGIZE

            # Wait until the actuator is deactivated 
            if ctrl.wait_until(
                lambda c: c[ACTUATOR_STATE] == DEENERGIZE,
                timeout=10 * sy.TimeSpan.SECOND, 
            ):
                log_event("Actuator deactivated successfully", writer, log_key)
            else:
                log_event("Failed to deactivate Actuator within timeout", writer, log_key)

            # deenergize ignitor
            ctrl[IGNITOR_CMD] = DEENERGIZE

            # Wait until the ignitor is deactivated 
            if ctrl.wait_until(
                lambda c: c[IGNITOR_STATE] == DEENERGIZE,
                timeout=10 * sy.TimeSpan.SECOND, 
            ):
                log_event("Igniter deactivated successfully", writer, log_key)
            else:
                log_event("Failed to deactivate igniter within timeout", writer, log_key)
            
            # pause before deluge shutoff
            ctrl.sleep(3)
            ctrl[DELUGE_CMD] = DEENERGIZE

            # Wait until the deluge is shutoff
            if ctrl.wait_until(
                lambda c: c[DELUGE_STATE] == DEENERGIZE,
                timeout=10 * sy.TimeSpan.SECOND, 
            ):
                log_event("Deluge shutoff sucessfull", writer, log_key)
            else:
                log_event("Failed to shutoff deugle within timeout", writer, log_key)

            # pause before N2 purge shutoff
            ctrl.sleep(3)
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
                name=f"Hot Fire Auto Sequence {end}",
                time_range=sy.TimeRange(start=start, end=end),
            )

            log_event(f"Hot Fire Auto Sequence completed: {start} to {end}", writer, log_key)

    except Exception as e:
        log_event(f"Error occurred during sequence execution: {str(e)}", writer, log_key)


def wait_for_trigger():
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

    # Check for channels
    arm_channel = client.channels.create(
        name="ARM_AUTO",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    run_channel = client.channels.create(
        name="RUN_AUTO",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    reset_channel = client.channels.create(
        name="RESET_AUTO",
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

    status_channel = client.channels.create(
        name="AUTOSEQUENCE_STATUS",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    armed_state_channel = client.channels.create(
        name="AUTOSEQUENCE_ARMED_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    arm_abort_channel = client.channels.create(
        name="ARM_ABORT",
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

    log_channel = client.channels.create(
        name="BCLS_LOG",
        data_type="String",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    arm_key = arm_channel.key
    run_key = run_channel.key
    reset_key = reset_channel.key
    shutdown_key = shutdown_channel.key
    status_key = status_channel.key
    armed_state_key = armed_state_channel.key
    arm_abort_key = arm_abort_channel.key
    sequence_active_key = sequence_active_channel.key
    log_key = log_channel.key

    arm_flag = False
    arm_abort_flag = False
    active_flag = True
    shutdown_flag = False

    with client.open_streamer([arm_key, run_key, reset_key, shutdown_key, arm_abort_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[armed_state_key, status_key, sequence_active_key, log_key], enable_auto_commit=True) as writer:
        
        log_event("Connected to Synnax for trigger monitoring", writer, log_key)
        log_event("Listening for trigger signals", writer, log_key)
        writer.write({status_key: [1]})
        for frame in streamer:
            for v in frame[reset_key]:
                if v == 1:
                    active_flag = True
                    log_event('Autosequence reset', writer, log_key)
            for v in frame[shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            for v in frame[arm_key]:
                if v == 1:
                    arm_flag = True
                    log_event('Autosequence armed', writer, log_key)
                elif v == 0:
                    arm_flag = False
                    log_event('Autosequence disarmed', writer, log_key) 
            for v in frame[arm_abort_key]:
                if v == 1:
                    arm_abort_flag = True
                elif v == 0:
                    arm_abort_flag = False  
            for v in frame[run_key]:
                if arm_flag and active_flag and arm_abort_flag and v == 1:
                    log_event("Trigger received, starting Autosequence", writer, log_key)
                    writer.write({armed_state_key: [0]})
                    writer.write({status_key: [0]})
                    writer.write({sequence_active_key: [1]})
                    active_flag = False 
                    arm_flag = False
                    run_sequence(writer, log_key)
                    writer.write({sequence_active_key: [0]})
                     
            writer.write({armed_state_key: [1 if arm_flag else 0]})
            writer.write({status_key: [1 if active_flag else 0]})

            if shutdown_flag:
                writer.write({status_key: [0]})
                writer.write({armed_state_key: [0]})
                log_event('Shutting down autosequence', writer, log_key)
                break

if __name__ == "__main__":
    wait_for_trigger()    
