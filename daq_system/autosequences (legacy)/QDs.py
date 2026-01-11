import synnax as sy # type: ignore
from datetime import datetime

ENERGIZE = 0
DEENERGIZE = 1

pop_timing = 1.5 #time valves are active for is seconds

#event logging function
def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"QDs: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})

# Helium QD popper
def pop_helium(writer, log_key):
    """Pop the helium QD"""
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

    # Define the control channel names
    QD_CMD = "SV-QD-03_cmd"
    QD_STATE = "SV-QD-03_state"

    log_event("Popping Helium QD", writer, log_key)
    
    try:
        # Open a control sequence under a context manager, so control is released when done
        with client.control.acquire(
            name="Helium QD",
            write=[QD_CMD],
            read=[QD_STATE],
            write_authorities=[200],  # Set high authority to prevent interference
        ) as ctrl:
            #Open the valve
            ctrl[QD_CMD] = ENERGIZE

            # Wait until the valve opens
            if ctrl.wait_until(
                lambda c: c[QD_STATE] == ENERGIZE,
                timeout = 2 * sy.TimeSpan.SECOND,
            ):
                log_event('Helium QD valve opened', writer, log_key)
            else:
                # Send message if valve fails to open
                ctrl[QD_CMD] = DEENERGIZE
                log_event('Helium QD valve failed to open.', writer, log_key)
                return

            #Wait for QD to pop
            ctrl.sleep(pop_timing)

            #Close the valve
            ctrl[QD_CMD] = DEENERGIZE

            # Wait until the valve closes
            if ctrl.wait_until(
                lambda c: c[QD_STATE] == DEENERGIZE,
                timeout = 2 * sy.TimeSpan.SECOND,
            ):
                log_event('Helium QD valve closed.', writer, log_key)
                log_event('Helium QD popped.', writer, log_key)
            else:
                # Send message if valve fails to open
                ctrl[QD_CMD] = DEENERGIZE
                log_event('Helium QD valve failed to close.', writer, log_key)
                return

    except Exception as e:
        log_event(f"Error occurred during script execution: {str(e)}", writer, log_key)

# Vent QD popper
def pop_vents(writer, log_key):
    """Pop the vent QDs"""
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

    # Define the control channel names
    QD_CMD = "SV-QD-01_cmd"
    QD_STATE = "SV-QD-01_state"

    log_event("Popping Vent QDs", writer, log_key)
    
    try:
        # Open a control sequence under a context manager, so control is released when done
        with client.control.acquire(
            name="Vent QDs",
            write=[QD_CMD],
            read=[QD_STATE],
            write_authorities=[200],  # Set high authority to prevent interference
        ) as ctrl:
            #Open the valve
            ctrl[QD_CMD] = ENERGIZE

            # Wait until the valve opens
            if ctrl.wait_until(
                lambda c: c[QD_STATE] == ENERGIZE,
                timeout = 2 * sy.TimeSpan.SECOND,
            ):
                log_event('Vent QD valve opened', writer, log_key)
            else:
                # Send message if valve fails to open
                ctrl[QD_CMD] = DEENERGIZE
                log_event('Vent QD valve failed to open.', writer, log_key)
                return

            #Wait for QD to pop
            ctrl.sleep(pop_timing)

            #Close the valve
            ctrl[QD_CMD] = DEENERGIZE

            # Wait until the valve closes
            if ctrl.wait_until(
                lambda c: c[QD_STATE] == DEENERGIZE,
                timeout = 2 * sy.TimeSpan.SECOND,
            ):
                log_event('Vent QD valve closed.', writer, log_key)
                log_event('Vent QDs popped.', writer, log_key)
            else:
                # Send message if valve fails to open
                ctrl[QD_CMD] = DEENERGIZE
                log_event('Vent QD valve failed to close.', writer, log_key)
                return

    except Exception as e:
        log_event(f"Error occurred during script execution: {str(e)}", writer, log_key)

# Fill QD popper
def pop_fill(writer, log_key):
    """Pop the fill QDs"""
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

    # Define the control channel names
    QD_CMD = "SV-QD-02_cmd"
    QD_STATE = "SV-QD-02_state"

    log_event("Popping fill QDs", writer, log_key)
    
    try:
        # Open a control sequence under a context manager, so control is released when done
        with client.control.acquire(
            name="Fill QDs",
            write=[QD_CMD],
            read=[QD_STATE],
            write_authorities=[200],  # Set high authority to prevent interference
        ) as ctrl:
            #Open the valve
            ctrl[QD_CMD] = ENERGIZE

            # Wait until the valve opens
            if ctrl.wait_until(
                lambda c: c[QD_STATE] == ENERGIZE,
                timeout = 2 * sy.TimeSpan.SECOND,
            ):
                log_event('Fill QD valve opened', writer, log_key)
            else:
                # Send message if valve fails to open
                ctrl[QD_CMD] = DEENERGIZE
                log_event('Fill QD valve failed to open.', writer, log_key)
                return

            #Wait for QD to pop
            ctrl.sleep(pop_timing)

            #Close the valve
            ctrl[QD_CMD] = DEENERGIZE

            # Wait until the valve closes
            if ctrl.wait_until(
                lambda c: c[QD_STATE] == DEENERGIZE,
                timeout = 2 * sy.TimeSpan.SECOND,
            ):
                log_event('Fill QD valve closed.', writer, log_key)
                log_event('Fill QDs popped.', writer, log_key)
            else:
                # Send message if valve fails to open
                ctrl[QD_CMD] = DEENERGIZE
                log_event('Fill QD valve failed to close.', writer, log_key)
                return

    except Exception as e:
        log_event(f"Error occurred during script execution: {str(e)}", writer, log_key)

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
    shutdown_channel = client.channels.create(
        name="QD_SHUTDOWN",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    status_channel = client.channels.create(
        name="QD_STATUS",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    helium_channel = client.channels.create(
        name="POP_HELIUM_QD",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    vent_channel = client.channels.create(
        name="POP_VENT_QD",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    fill_channel = client.channels.create(
        name="POP_Fill_QD",
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

    shutdown_key = shutdown_channel.key
    status_key = status_channel.key
    log_key = log_channel.key
    helium_key = helium_channel.key
    vent_key = vent_channel.key
    fill_key = fill_channel.key

    shutdown_flag = False

    with client.open_streamer([shutdown_key, helium_key, vent_key, fill_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[status_key, log_key], enable_auto_commit=True) as writer:
        
        log_event("Connected to Synnax for trigger monitoring", writer, log_key)
        log_event("Listening for trigger signals", writer, log_key)
        writer.write({status_key: [1]})

        for frame in streamer:
            for v in frame[shutdown_key]:
                if v == 1:
                    shutdown_flag = True
                else:
                    shutdown_flag = False
            for v in frame[helium_key]:
                if v == 1:
                    pop_helium(writer, log_key)
            for v in frame[vent_key]:
                if v == 1:
                    pop_vents(writer, log_key)
            for v in frame[fill_key]:
                if v == 1:
                    pop_fill(writer, log_key)

            if shutdown_flag:
                writer.write({status_key: [0]})
                log_event('Shutting down autosequence', writer, log_key)
                break

if __name__ == "__main__":
    wait_for_trigger()    
