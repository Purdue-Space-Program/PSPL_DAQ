import synnax as sy
import time
import json
import os
from typing import Dict, List, Optional

# Constants for valve states - flipped for NI device
ENERGIZE = 0  # To open a normally closed valve or close a normally open valve
DEENERGIZE = 1  # To close a normally closed valve or open a normally open valve

# Valve pause time (seconds)
PAUSE_TIME = 2


class Valve:
    def __init__(self, config: Dict):
        self.name = config["name"]
        self.cmd = config["cmd"]
        self.position_indicator = config["position_indicator"]
        self.normally = config["normally"]
        self.description = config["description"]
        self.has_position_indicator = self.position_indicator is not None


def log_event(message, level="INFO"):
    """Log events with timestamps and level."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    level_str = f"[{level:^7}]"  # Center-align level in 7 characters
    print(f"[{timestamp}] {level_str} {message}")


def get_user_input(prompt="Press Enter to continue...") -> str:
    """Get user input with a custom prompt."""
    return input(f"\n> {prompt}")


def check_abort() -> bool:
    """Check if operator wants to abort the sequence."""
    response = get_user_input("Continue sequence? [y/n]: ")
    return response.lower() not in ["y", "yes"]


def load_valve_config(
    config_file: str = "valve_config.json",
) -> tuple[List[Valve], List[Valve]]:
    """Load valve configuration from JSON file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        with open(config_path, "r") as f:
            config = json.load(f)

        sv_valves = [Valve(v) for v in config["solenoid_valves"]]
        pv_valves = [Valve(v) for v in config["pneumatic_valves"]]
        return sv_valves, pv_valves
    except Exception as e:
        log_event(f"Failed to load valve configuration: {str(e)}", "ERROR")
        raise


def run_valve_check_sequence():
    """Execute the valve cycle and check sequence."""
    # Connect to Synnax cluster
    client = sy.Synnax(
        host="128.46.118.59",
        port=9090,
        username="Bill",
        password="Bill",
    )
    log_event("Starting Valve Check Sequence")

    # Load valve configurations
    sv_valves, pv_valves = load_valve_config()

    # Gather all channel names for read/write
    read_channels = []
    write_channels = []

    for valve in sv_valves + pv_valves:
        if valve.has_position_indicator:
            read_channels.append(valve.position_indicator)
        write_channels.append(valve.cmd)

    # Begin control sequence
    with client.control.acquire(
        name="Valve Check Sequence",
        read=read_channels,
        write=write_channels,
        write_authorities=[150],  # Use medium authority level to allow console override
    ) as controller:
        try:
            # First, check all SV (Solenoid Valve) operations
            log_event("BEGINNING SOLENOID VALVE CHECKS", "STATUS")

            for valve in sv_valves:
                if valve.has_position_indicator:
                    if not check_valve_with_indicator(controller, valve):
                        if check_abort():
                            raise KeyboardInterrupt(
                                "Operator requested abort after valve failure"
                            )
                else:
                    if not check_valve_without_indicator(controller, valve):
                        if check_abort():
                            raise KeyboardInterrupt(
                                "Operator requested abort after valve failure"
                            )

            # Prompt for manual confirmation before proceeding to pneumatic valves
            log_event("SOLENOID VALVE CHECKS COMPLETE", "STATUS")
            log_event("Preparing to check pneumatic valves...", "INFO")
            response = get_user_input(
                "Type 'continue' to proceed with pneumatic valve checks (or 'abort' to stop): "
            )
            if response.lower() != "continue":
                raise KeyboardInterrupt(
                    "Operator requested abort before pneumatic checks"
                )

            # Check all PV (Pneumatic Valve) operations
            log_event("BEGINNING PNEUMATIC VALVE CHECKS", "STATUS")

            for valve in pv_valves:
                if not check_valve_with_indicator(controller, valve):
                    if check_abort():
                        raise KeyboardInterrupt(
                            "Operator requested abort after valve failure"
                        )

            log_event("PNEUMATIC VALVE CHECKS COMPLETE", "STATUS")

        except KeyboardInterrupt as e:
            log_event(f"Operator initiated shutdown: {str(e)}", "WARN")
            emergency_shutdown(controller, sv_valves + pv_valves)
            return
        except Exception as e:
            log_event(f"ERROR: {str(e)}", "ERROR")
            emergency_shutdown(controller, sv_valves + pv_valves)
            raise
        finally:
            log_event("Sequence complete - all valves in safe state", "STATUS")


def check_valve_with_indicator(controller, valve: Valve) -> bool:
    """Check a valve by cycling and confirming position with indicator. Returns True if successful."""
    log_event(f"Checking {valve.name} - {valve.description}")
    log_event(f"Type: {'Normally ' + valve.normally}")

    # Get initial state
    initial_state = controller[valve.position_indicator]
    log_event(f"Initial position: {initial_state}")

    success = True
    try:
        # For normally closed valves:
        # - When deenergized (1), expect position indicator = 0 (closed)
        # - When energized (0), expect position indicator = 1 (open)
        # For normally open valves:
        # - When deenergized (1), expect position indicator = 1 (open)
        # - When energized (0), expect position indicator = 0 (closed)

        # Start with valve in deenergized state (1)
        controller[valve.cmd] = DEENERGIZE
        controller.sleep(PAUSE_TIME)
        deenergized_state = controller[valve.position_indicator]
        expected_deenergized = 0 if valve.normally == "Closed" else 1

        if deenergized_state != expected_deenergized:
            log_event(
                f"{valve.name} deenergized position incorrect: Expected {expected_deenergized}, got {deenergized_state}",
                "WARN",
            )
            success = False
        else:
            log_event(f"{valve.name} deenergized state verified", "INFO")

        # Now energize the valve (0)
        log_event(f"Energizing {valve.name}")
        controller[valve.cmd] = ENERGIZE
        controller.sleep(PAUSE_TIME)
        energized_state = controller[valve.position_indicator]
        expected_energized = 1 if valve.normally == "Closed" else 0

        if energized_state != expected_energized:
            log_event(
                f"{valve.name} energized position incorrect: Expected {expected_energized}, got {energized_state}",
                "WARN",
            )
            success = False
        else:
            log_event(f"{valve.name} energized state verified", "INFO")

        # Return to deenergized state (safe state)
        log_event(f"Returning {valve.name} to deenergized state")
        controller[valve.cmd] = DEENERGIZE
        controller.sleep(PAUSE_TIME)
        final_state = controller[valve.position_indicator]

        if final_state != expected_deenergized:
            log_event(
                f"{valve.name} final position incorrect: Expected {expected_deenergized}, got {final_state}",
                "WARN",
            )
            success = False
        else:
            log_event(f"{valve.name} returned to safe state", "INFO")

    except Exception as e:
        log_event(f"Error during {valve.name} actuation: {str(e)}", "ERROR")
        controller[valve.cmd] = DEENERGIZE  # Safe state for all valves
        success = False
        raise

    return success


def check_valve_without_indicator(controller, valve: Valve) -> bool:
    """Check a valve by cycling and using visual confirmation. Returns True if successful."""
    log_event(f"Checking {valve.name} - {valve.description}")
    log_event(f"Type: {'Normally ' + valve.normally}")
    log_event("Manual verification required for this valve", "WARN")

    try:
        # Complete cycle without intermediate confirmation
        if valve.normally == "Closed":
            log_event(f"Energizing {valve.name} to open...")
            controller[valve.cmd] = ENERGIZE
        else:
            log_event(f"Deenergizing {valve.name} to open...")
            controller[valve.cmd] = DEENERGIZE

        controller.sleep(PAUSE_TIME)

        if valve.normally == "Closed":
            log_event(f"Deenergizing {valve.name} to close...")
            controller[valve.cmd] = DEENERGIZE
        else:
            log_event(f"Energizing {valve.name} to close...")
            controller[valve.cmd] = ENERGIZE

        controller.sleep(PAUSE_TIME)

        # Single verification after complete cycle
        verification = get_user_input(
            f"Did {valve.name} cycle correctly (open then close)? [y/n]: "
        )

        if verification.lower() not in ["y", "yes"]:
            log_event(f"{valve.name} cycle verification failed", "WARN")
            return False

        log_event(f"{valve.name} cycle verified successfully", "INFO")
        return True

    except Exception as e:
        log_event(f"Error during {valve.name} actuation: {str(e)}", "ERROR")
        controller[valve.cmd] = DEENERGIZE
        return False


def emergency_shutdown(controller, valves: List[Valve]):
    """Return all valves to their safe state."""
    log_event("EMERGENCY SHUTDOWN INITIATED", "WARN")

    for valve in valves:
        try:
            log_event(f"Deenergizing {valve.name}")
            controller[valve.cmd] = DEENERGIZE
        except Exception as e:
            log_event(f"Failed to deenergize {valve.name}: {str(e)}", "ERROR")

    log_event("Emergency shutdown complete", "STATUS")


if __name__ == "__main__":
    try:
        run_valve_check_sequence()
    except KeyboardInterrupt:
        print("\nSequence aborted by operator")
    except Exception as e:
        print(f"\nSequence failed: {str(e)}")
