import synnax as sy
import time
from socket import socket, AF_INET, SOCK_STREAM
from struct import pack
from datetime import datetime

ENERGIZE = 0
DEENERGIZE = 1


def send_tcp_command(command_code):
    """Send a TCP command to the specified address and port.

    Args:
        command_code (int): Command code to send

    Returns:
        bytes: Response received from the server
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect(("192.168.1.103", 1234))
        packet = pack("B", command_code)
        s.send(packet)
        response = s.recv(1)
        return response


def log_event(message):
    """Log events with timestamps.

    Args:
        message (str): Message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


# Command codes
START_COMMAND = 14
ABORT_COMMAND = 15

# Sequence parameters
TC_THRESHOLD = 100  # Temperature threshold
IGNITION_WAIT_TIME = 10  # Seconds to wait between igniter and actuator
ACTUATOR_RUN_TIME = 5.0  # Seconds to run actuator


# Main autosequence
def run_tc_sequence():
    """Execute the TC auto sequence with abort logic."""
    client = sy.Synnax(
        host="128.46.118.59",
        port=9090,
        username="Bill",
        password="Bill",
    )

    log_event("Starting TC Auto Sequence")

    with client.control.acquire(
        name="TC Auto Sequence",
        read=["TC", "ACTUATOR_state", "IGNITOR_state"],
        write=["ACTUATOR_cmd", "IGNITOR_cmd"],
        write_authorities=[200],  # Set high authority to prevent interference
    ) as controller:
        # Capture sequence start time
        start = sy.TimeStamp.now()
        sequence_status = "ABORTED"  # Default status

        try:
            # Send start command
            # response = send_tcp_command(START_COMMAND)
            # log_event(f"Sent start command, received: {response}")

            # Activate igniter
            controller["IGNITOR_cmd"] = ENERGIZE
            # log_event("Igniter activated")

            # Wait for TC to exceed threshold while respecting timeout
            # log_event(
            #     f"Waiting up to {IGNITION_WAIT_TIME} seconds for TC > {TC_THRESHOLD}"
            # )

            # Using controller.wait_until with a timeout for precise timing
            tc_threshold_reached = controller.wait_until(
                lambda c: c["TC"] > TC_THRESHOLD,
                timeout=IGNITION_WAIT_TIME * sy.TimeSpan.SECOND,
            )

            # Check if temperature threshold was reached
            if tc_threshold_reached:
                # log_event(f"TC threshold reached: {controller['TC']}")

                # Activate actuator ONLY if temperature threshold was reached
                controller["ACTUATOR_cmd"] = ENERGIZE
                # log_event("Actuator activated")

                # Run actuator for specified time
                controller.sleep(ACTUATOR_RUN_TIME)

                # Deactivate systems in reverse order
                controller["ACTUATOR_cmd"] = DEENERGIZE
                # log_event("Actuator deactivated")

                controller["IGNITOR_cmd"] = DEENERGIZE
                # log_event("Igniter deactivated")

                sequence_status = "SUCCESS"
                log_event("Sequence completed successfully")
            else:
                controller["IGNITOR_cmd"] = DEENERGIZE
                # Abort sequence if TC didn't reach threshold

                # Send abort command
                # response = send_tcp_command(ABORT_COMMAND)
                # log_event(f"Sent abort command, received: {response}")

                log_event(
                    f"ABORTING: TC only reached {controller['TC']}, below threshold of {TC_THRESHOLD}"
                )

                # Deactivate igniter without ever activating actuator
                log_event("Ignitor deactivated")

        except Exception as e:
            # Safety shutdown
            controller["ACTUATOR_cmd"] = DEENERGIZE
            controller["IGNITOR_cmd"] = DEENERGIZE

            # Handle unexpected errors
            log_event(f"ERROR: {str(e)}")
            log_event("Emergency shutdown completed")

        finally:
            # Ensure we always create a range to document the test
            end = sy.TimeStamp.now()

            # Create range with descriptive name
            client.ranges.create(
                name=f"TC Auto Sequence {sequence_status} {end}",
                time_range=sy.TimeRange(start=start, end=end),
            )
            log_event(f"Test data saved as 'TC Auto Sequence {sequence_status} {end}'")


if __name__ == "__main__":
    run_tc_sequence()
