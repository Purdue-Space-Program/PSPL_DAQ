import synnax as sy
import time

# Constants for valve states - flipped for NI device
ENERGIZE = 0  # To open a normally closed valve or close a normally open valve
DEENERGIZE = 1  # To close a normally closed valve or open a normally open valve

# Valve pause time (seconds)
PAUSE_TIME = 2


def log_event(message):
    """Log events with timestamps."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def get_user_input(prompt="Press Enter to continue..."):
    """Get user input with a custom prompt."""
    return input(prompt)


def run_valve_check_sequence():
    """
    Execute the valve cycle and check sequence to validate
    proper operation of solenoid and pneumatic valves.
    """
    # Connect to Synnax cluster
    client = sy.Synnax(
        host="128.46.118.59",
        port=9090,
        username="Bill",
        password="Bill",
    )
    log_event("Starting Valve Check Sequence")

    # Define SV (Solenoid Valve) test channels
    # Note: sv_has_reed=False for valves without reed switches
    sv_valves = [
        {
            "name": "SV-HE-01",
            "cmd": "SV-HE-01_cmd",
            "reed": None,
            "normally": "Closed",
            "has_reed": False,
        },
        {
            "name": "SV-BP-01",
            "cmd": "SV-BP-01_cmd",
            "reed": "REED-BP-01",
            "normally": "Closed",
            "has_reed": True,
        },
        {
            "name": "SV-N2-02",
            "cmd": "SV-N2-02_cmd",
            "reed": "REED-N2-02",
            "normally": "Closed",
            "has_reed": True,
        },
        {
            "name": "SV-QD-02",
            "cmd": "SV-QD-02_cmd",
            "reed": None,
            "normally": "Closed",
            "has_reed": False,
        },
        {
            "name": "SV-QD-03",
            "cmd": "SV-QD-03_cmd",
            "reed": None,
            "normally": "Closed",
            "has_reed": False,
        },
    ]

    # Define PV (Pneumatic Valve) test channels
    pv_valves = [
        {
            "name": "PV-HE-01",
            "cmd": "PV-HE-01_cmd",
            "reed": "PI-HE-01",
            "normally": "Closed",
            "has_reed": True,
        },
        {
            "name": "PV-FU-02",
            "cmd": "PV-FU-02_cmd",
            "reed": "PI-FU-02",
            "normally": "Closed",
            "has_reed": True,
        },
        {
            "name": "PV-OX-02",
            "cmd": "PV-OX-02_cmd",
            "reed": "PI-OX-02",
            "normally": "Closed",
            "has_reed": True,
        },
        {
            "name": "PV-FU-03",
            "cmd": "PV-FU-03_cmd",
            "reed": "PI-FU-03",
            "normally": "Open",
            "has_reed": True,
        },
        {
            "name": "PV-OX-03",
            "cmd": "PV-OX-03_cmd",
            "reed": "PI-OX-03",
            "normally": "Open",
            "has_reed": True,
        },
    ]

    # Gather all channel names for read/write
    read_channels = []
    write_channels = []

    for valve in sv_valves + pv_valves:
        if valve["has_reed"] and valve["reed"]:
            read_channels.append(valve["reed"])
        write_channels.append(valve["cmd"])

    # Begin control sequence
    with client.control.acquire(
        name="Valve Check Sequence",
        read=read_channels,
        write=write_channels,
        write_authorities=[150],  # Use medium authority level to allow console override
    ) as controller:
        try:
            # First, check all SV (Solenoid Valve) operations
            log_event("===== BEGINNING SOLENOID VALVE CHECKS =====")

            for valve in sv_valves:
                if valve["has_reed"]:
                    check_valve_with_reed(controller, valve)
                else:
                    check_valve_without_reed(controller, valve)

            # Prompt for manual confirmation before proceeding to pneumatic valves
            log_event("===== SOLENOID VALVE CHECKS COMPLETE =====")
            log_event("Preparing to check pneumatic valves...")
            get_user_input(
                "Type 'continue' and press Enter to proceed with pneumatic valve checks: "
            )

            # Check all PV (Pneumatic Valve) operations
            log_event("===== BEGINNING PNEUMATIC VALVE CHECKS =====")

            for valve in pv_valves:
                check_valve_with_reed(controller, valve)

            log_event("===== PNEUMATIC VALVE CHECKS COMPLETE =====")

        except Exception as e:
            # Safety shutdown - place all valves in safe state
            log_event(f"ERROR: {str(e)}")
            emergency_shutdown(controller, sv_valves + pv_valves)
            log_event("Emergency shutdown completed")


def check_valve_with_reed(controller, valve):
    """Check a valve by cycling and confirming position with reed switch."""
    valve_name = valve["name"]
    cmd_channel = valve["cmd"]
    reed_channel = valve["reed"]
    normally = valve["normally"]

    log_event(
        f"Checking {valve_name} (Normally {normally}) with reed switch validation"
    )

    # Get initial state
    initial_reed_state = controller[reed_channel]

    # For normally closed valves:
    # - When deenergized (1), the reed switch should read 0 (closed)
    # - When energized (0), the reed switch should read 1 (open)
    # For normally open valves:
    # - When deenergized (1), the reed switch should read 1 (open)
    # - When energized (0), the reed switch should read 0 (closed)
    expected_closed_state = 0 if normally == "Closed" else 1
    expected_open_state = 1 if normally == "Closed" else 0

    log_event(f"{valve_name} initial position indication: {initial_reed_state}")

    # Actuate the valve to open position
    if normally == "Closed":
        log_event(f"Energizing {valve_name} to open...")
        controller[cmd_channel] = ENERGIZE  # 0 to energize and open NC valve
    else:  # Normally Open
        log_event(f"Deenergizing {valve_name} to open...")
        controller[cmd_channel] = DEENERGIZE  # 1 to deenergize and open NO valve

    # Pause to allow valve to actuate
    controller.sleep(PAUSE_TIME)

    # Verify open position
    open_reed_state = controller[reed_channel]
    log_event(f"{valve_name} position indication after actuation: {open_reed_state}")

    if open_reed_state != expected_open_state:
        log_event(
            f"WARNING: {valve_name} position indication incorrect! Expected {expected_open_state}, got {open_reed_state}"
        )
    else:
        log_event(f"{valve_name} successfully actuated and verified open")

    # Actuate the valve to closed position
    if normally == "Closed":
        log_event(f"Deenergizing {valve_name} to close...")
        controller[cmd_channel] = DEENERGIZE  # 1 to deenergize and close NC valve
    else:  # Normally Open
        log_event(f"Energizing {valve_name} to close...")
        controller[cmd_channel] = ENERGIZE  # 0 to energize and close NO valve

    # Pause to allow valve to actuate
    controller.sleep(PAUSE_TIME)

    # Verify closed position
    closed_reed_state = controller[reed_channel]
    log_event(f"{valve_name} position indication after actuation: {closed_reed_state}")

    if closed_reed_state != expected_closed_state:
        log_event(
            f"WARNING: {valve_name} position indication incorrect! Expected {expected_closed_state}, got {closed_reed_state}"
        )
    else:
        log_event(f"{valve_name} successfully actuated and verified closed")

    # Ask user to confirm before proceeding to next valve
    get_user_input(
        f"{valve_name} check complete. Press Enter to continue to next valve..."
    )


def check_valve_without_reed(controller, valve):
    """Check a valve by cycling and using visual/manual confirmation."""
    valve_name = valve["name"]
    cmd_channel = valve["cmd"]
    normally = valve["normally"]

    log_event(f"Checking {valve_name} (Normally {normally}) - NO REED SWITCH")
    log_event(f"This valve requires visual/manual verification")

    # Actuate the valve to open position
    if normally == "Closed":
        log_event(f"Energizing {valve_name} to open...")
        controller[cmd_channel] = ENERGIZE  # 0 to energize and open NC valve
    else:  # Normally Open
        log_event(f"Deenergizing {valve_name} to open...")
        controller[cmd_channel] = DEENERGIZE  # 1 to deenergize and open NO valve

    # Pause to allow valve to actuate
    controller.sleep(PAUSE_TIME)

    # Prompt for manual verification
    verification = get_user_input(
        f"Please visually verify {valve_name} is OPEN. Type 'yes' if correct, or 'no' if incorrect: "
    )

    if verification.lower() != "yes":
        log_event(
            f"WARNING: {valve_name} did not open correctly according to visual verification"
        )
    else:
        log_event(
            f"{valve_name} successfully actuated to open position (verified visually)"
        )

    # Actuate the valve to closed position
    if normally == "Closed":
        log_event(f"Deenergizing {valve_name} to close...")
        controller[cmd_channel] = DEENERGIZE  # 1 to deenergize and close NC valve
    else:  # Normally Open
        log_event(f"Energizing {valve_name} to close...")
        controller[cmd_channel] = ENERGIZE  # 0 to energize and close NO valve

    # Pause to allow valve to actuate
    controller.sleep(PAUSE_TIME)

    # Prompt for manual verification
    verification = get_user_input(
        f"Please visually verify {valve_name} is CLOSED. Type 'yes' if correct, or 'no' if incorrect: "
    )

    if verification.lower() != "yes":
        log_event(
            f"WARNING: {valve_name} did not close correctly according to visual verification"
        )
    else:
        log_event(
            f"{valve_name} successfully actuated to closed position (verified visually)"
        )

    # Ask user to confirm before proceeding to next valve
    get_user_input(
        f"{valve_name} check complete. Press Enter to continue to next valve..."
    )


def emergency_shutdown(controller, valves):
    """Return all valves to their safe state."""
    log_event("EMERGENCY SHUTDOWN: Returning all valves to safe state")

    for valve in valves:
        if valve["normally"] == "Closed":
            # For normally closed valves, deenergize (1) to close
            log_event(f"Deenergizing {valve['name']} (Normally Closed)")
            controller[valve["cmd"]] = DEENERGIZE
        else:  # Normally Open
            # For normally open valves, deenergize (1) to open
            log_event(f"Deenergizing {valve['name']} (Normally Open)")
            controller[valve["cmd"]] = DEENERGIZE


if __name__ == "__main__":
    run_valve_check_sequence()
