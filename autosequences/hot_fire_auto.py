import synnax as sy
from datetime import datetime

ENERGIZE = 0
DEENERGIZE = 1


def log_event(message):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


# Main autosequence
def run_sequence():
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
        log_event("Connected to Synnax system")
    except Exception as e:
        log_event(f"Failed to connect to Synnax system: {str(e)}")
        return

    # Define the control channel names
    IGNITOR_CMD = "IGNITOR_cmd"
    IGNITOR_STATE = "IGNITOR_state"

    DELUGE_CMD = "DELUGE_cmd"
    DELUGE_STATE = "DELUGE_state"

    PURGE_CMD = "SV-N2-02_cmd"
    PURGE_STATE = "SV-N2-02_state"

    log_event("Starting Hot Fire Auto Sequence")

    try:
        # Open a control sequence under a context manager, so control is released when done
        with client.control.acquire(
            name="Hot Fire Auto Sequence",
            write=[IGNITOR_CMD, DELUGE_CMD, PURGE_CMD],
            read=[IGNITOR_STATE, DELUGE_STATE, PURGE_STATE],
            write_authorities=[200],  # Set high authority to prevent interference
        ) as ctrl:
            log_event("Control sequence acquired")

            # Mark the start of the sequence
            start = sy.TimeStamp.now()

            # Set initial conditions (like energizing the igniter)
            log_event("Activating igniter")
            ctrl[IGNITOR_CMD] = ENERGIZE
            ctrl[DELUGE_CMD] = ENERGIZE
            ctrl[PURGE_CMD] = ENERGIZE

            # Wait until the ignitor state is activated (assuming it goes high)
            if ctrl.wait_until(
                lambda c: c[IGNITOR_STATE] == ENERGIZE,
                timeout=30
                * sy.TimeSpan.SECOND,  # Wait up to 30 seconds for the igniter to activate
            ):
                log_event("Igniter activated successfully")
            else:
                log_event("Failed to activate igniter within timeout")
                # Emergency shutdown in case of failure
                ctrl[IGNITOR_CMD] = DEENERGIZE
                log_event("Emergency shutdown completed")
                return

            # Run the actuator for a specified amount of time (simulated run time)
            ctrl.sleep(20)  # Simulating 5 seconds of operation

            # De-energize the igniter (shutdown)
            log_event("De-energizing igniter")
            ctrl[IGNITOR_CMD] = DEENERGIZE
            ctrl[DELUGE_CMD] = DEENERGIZE

            # Wait until the igniter is deactivated (assuming the state goes low)
            if ctrl.wait_until(
                lambda c: c[IGNITOR_STATE] == DEENERGIZE,
                timeout=10
                * sy.TimeSpan.SECOND,  # Wait up to 10 seconds for deactivation
            ):
                log_event("Igniter deactivated successfully")
            else:
                log_event("Failed to deactivate igniter within timeout")

            # Mark the end of the sequence
            end = sy.TimeStamp.now()

            # Label the sequence with the end time
            client.ranges.create(
                name=f"Cold Flow Auto Sequence {end}",
                time_range=sy.TimeRange(start=start, end=end),
            )

            log_event(f"Cold Flow Auto Sequence completed: {start} to {end}")

    except Exception as e:
        log_event(f"Error occurred during sequence execution: {str(e)}")


if __name__ == "__main__":
    run_sequence()
