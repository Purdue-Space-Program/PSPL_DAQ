import synnax as sy
from datetime import datetime
from collections import deque

# Command constants
ENERGIZE = 0
DEENERGIZE = 1

# Pressure and slope setpoints (in PSI and PSI/sec)
SLOPE_THRESHOLD = 50.0  # PSI/sec
GOAL_PRESSURE_FINAL = 3500
REDLINE_PRESSURE = 3600
MOVING_AVERAGE_WINDOW = 5 # Number of data points for the filter

# Channel names
LOG_KEY = "BCLS_LOG"
STATUS_KEY = "AUTOSEQUENCE_STATUS"
PT_HE_01_STATE = "PT-HE-01"
PV_HE_01_CMD = "PV-HE-01_cmd"
PV_HE_01_STATE = "PV-HE-01_state"
SV_BP_01_CMD = "SV-BP-01_cmd"
SV_BP_01_STATE = "SV-BP-01_state"


def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {{'Auto-Press': '{message}'}}"
    print(fullMessage)
    if writer and log_key:
        writer.write({log_key: [fullMessage]})


def run_pressurization_sequence_with_slope(writer, log_key):
    """Execute the COPV pressurization sequence with slope-based control."""

    # Establish connection to Synnax system
    try:
        client = sy.Synnax(
            host="10.165.89.106",
            port=2701,
            username="Bill",
            password="Bill",
            secure=False,
        )
        log_event("Connected to Synnax system", writer, log_key)
    except Exception as e:
        log_event(f"Failed to connect to Synnax: {str(e)}", writer, log_key)
        return

    try:
        # Acquire control of the necessary channels with high authority
        with client.control.acquire(
            name="COPV Pressurization",
            write=[PV_HE_01_CMD, SV_BP_01_CMD],
            read=[PT_HE_01_STATE, PV_HE_01_STATE, SV_BP_01_STATE],
            write_authorities=[240], # High authority to prevent interference
        ) as ctrl:
            log_event("Control sequence acquired for COPV pressurization", writer, log_key)
            start = sy.TimeStamp.now()

            # Step 1: Initial Pressurization
            log_event("Initiating main pressurization valve (PV-HE-01)", writer, log_key)
            ctrl[PV_HE_01_CMD] = ENERGIZE
            
            # Initialize moving average and time tracking
            pressure_readings = deque(maxlen=MOVING_AVERAGE_WINDOW)
            last_smoothed_pressure = None
            last_time = sy.TimeStamp.now()

            # Wait and monitor pressure to determine when to engage boost pump
            log_event("Monitoring pressure slope for boost pump activation...", writer, log_key)
            while True:
                # Check for redline condition at every loop iteration
                if ctrl[PT_HE_01_STATE] >= REDLINE_PRESSURE:
                    log_event("Redline pressure exceeded. Aborting sequence.", writer, log_key)
                    # De-energize all valves on failure
                    ctrl[PV_HE_01_CMD] = DEENERGIZE
                    ctrl[SV_BP_01_CMD] = DEENERGIZE
                    return

                # Add the new pressure reading to the deque
                pressure_readings.append(ctrl[PT_HE_01_STATE])
                current_time = sy.TimeStamp.now()
                
                # Wait until we have enough data points for the filter
                if len(pressure_readings) < MOVING_AVERAGE_WINDOW:
                    ctrl.sleep(0.5)
                    continue

                # Calculate the smoothed pressure and elapsed time
                smoothed_pressure = sum(pressure_readings) / len(pressure_readings)
                delta_time = (current_time - last_time).as_seconds()

                if last_smoothed_pressure is not None and delta_time > 0:
                    delta_pressure = smoothed_pressure - last_smoothed_pressure
                    slope = delta_pressure / delta_time
                    log_event(f"Smoothed pressure: {smoothed_pressure:.2f} PSI, Slope: {slope:.2f} PSI/sec", writer, log_key)
                
                    # Check if slope has dropped below the threshold
                    if slope <= SLOPE_THRESHOLD:
                        log_event(f"Slope dropped below threshold ({SLOPE_THRESHOLD} PSI/sec). Activating boost pump.", writer, log_key)
                        break

                # Update for next iteration
                last_smoothed_pressure = smoothed_pressure
                last_time = current_time
                ctrl.sleep(0.5) # Poll every half second to get a good rate

            # Step 2: Boost Pressurization
            log_event("Activating boost pump valve (SV-BP-01) for final pressure.", writer, log_key)
            ctrl[SV_BP_01_CMD] = ENERGIZE

            # Wait until final goal pressure is reached
            if not ctrl.wait_until(
                lambda c: c[PT_HE_01_STATE] >= GOAL_PRESSURE_FINAL,
                timeout=60 * sy.TimeSpan.SECOND,
            ):
                log_event("Failed to reach final goal pressure. Aborting.", writer, log_key)
                # De-energize all valves on failure
                ctrl[PV_HE_01_CMD] = DEENERGIZE
                ctrl[SV_BP_01_CMD] = DEENERGIZE
                return
            
            log_event(f"Final pressure of {GOAL_PRESSURE_FINAL} PSI reached.", writer, log_key)
            
            # Step 3: Final de-energization
            log_event("De-energizing all valves", writer, log_key)
            ctrl[SV_BP_01_CMD] = DEENERGIZE
            ctrl[PV_HE_01_CMD] = DEENERGIZE

            # Wait for valves to close
            ctrl.wait_until(
                lambda c: c[SV_BP_01_STATE] == DEENERGIZE and c[PV_HE_01_STATE] == DEENERGIZE,
                timeout=10 * sy.TimeSpan.SECOND,
            )
            log_event("Pressurization sequence complete. All valves closed.", writer, log_key)

            end = sy.TimeStamp.now()
            client.ranges.create(
                name=f"COPV Pressurization {end}",
                time_range=sy.TimeRange(start=start, end=end),
            )

    except Exception as e:
        log_event(f"Error occurred: {str(e)}", writer, log_key)


def wait_for_trigger():
    # This function remains the same as in the original script
    try:
        client = sy.Synnax(
            host="10.165.89.106",
            port=2701,
            username="Bill",
            password="Bill",
            secure=False,
        )
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] Failed to connect to Synnax for trigger monitoring: {str(e)}")
        return

    # Create channels for monitoring and control
    run_channel = client.channels.create(
        name="RUN_PRESSURIZATION",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )
    log_channel = client.channels.create(
        name=LOG_KEY,
        data_type="String",
        virtual=True,
        retrieve_if_name_exists=True,
    )
    status_channel = client.channels.create(
        name=STATUS_KEY,
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    run_key = run_channel.key
    log_key = log_channel.key
    status_key = status_channel.key
    
    with client.open_streamer([run_key]) as streamer, \
         client.open_writer(start=sy.TimeStamp.now(), channels=[log_key, status_key], enable_auto_commit=True) as writer:
        
        log_event("Listening for pressurization trigger signal...", writer, log_key)
        writer.write({status_key: [1]}) # Indicate ready state

        for frame in streamer:
            for v in frame[run_key]:
                if v == 1:
                    log_event("Pressurization trigger received!", writer, log_key)
                    writer.write({status_key: [0]}) # Indicate running state
                    run_pressurization_sequence_with_slope(writer, log_key)
                    writer.write({status_key: [1]}) # Indicate ready state again
                    
if __name__ == "__main__":
    wait_for_trigger()