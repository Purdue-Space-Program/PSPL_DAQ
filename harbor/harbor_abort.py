import synnax as sy # type: ignore
from datetime import datetime

ENERGIZE = 0
DEENERGIZE = 1

def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"Abort: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})

# Abort sequence
def run_abort(writer, log_key, close_regulate_key):
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
    try:
        # Define the control channel names
        INLET_STATE = "PV-ETH-INLET_state"
        INLET_CMD = "PV-ETH-INLET_cmd"

        OUTLET_STATE = "PV-ETH-OUTLET_state"
        OUTLET_CMD = "PV-ETH-OUTLET_cmd"

        with client.control.acquire(
            name="Abort Sequence",
            write_authorities=[230],
            write=[INLET_CMD, OUTLET_CMD],
            read=[INLET_STATE, OUTLET_STATE],
        ) as ctrl:
            log_event('Abort initiated', writer, log_key)

            # Mark the start of the sequence
            start = sy.TimeStamp.now()

            #close regulator
            writer.write({close_regulate_key: [1]})

            #Add commands to shutdown pump and cut power
            #
            #

            #Shutoff inlet
            ctrl[INLET_CMD] = DEENERGIZE

            # Wait until the Inlet is shutoff
            if ctrl.wait_until(
                lambda c: c[INLET_STATE] == DEENERGIZE,
                timeout= 1 * sy.TimeSpan.SECOND, 
            ):
                log_event("Inlet closed sucessfully.", writer, log_key)
            else:
                log_event("Failed to close inlet.", writer, log_key)
            
            #Shutoff Outlet
            ctrl[OUTLET_CMD] = DEENERGIZE

            # Wait until the Inlet is shutoff
            if ctrl.wait_until(
                lambda c: c[OUTLET_STATE] == DEENERGIZE,
                timeout= 1 * sy.TimeSpan.SECOND, 
            ):
                log_event("Outlet closed sucessfully.", writer, log_key)
            else:
                log_event("Failed to close outlet.", writer, log_key)

            ctrl.sleep(5)

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
        name="HBR_ARM_ABORT",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    abort_channel = client.channels.create(
        name="HBR_RUN_ABORT",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    total_shutdown_channel = client.channels.create(
        name="HBR_ALL_SHUTDOWN",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    single_shutdown_channel = client.channels.create(
        name="HBR_ABORT_SHUTDOWN",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    abort_active_channel = client.channels.create(
        name="HBR_ABORT_ACTIVE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    sequence_active_channel = client.channels.create(
        name="HBR_AUTOSEQUENCE_ACTIVE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    status_channel = client.channels.create(
        name="HBR_ABORT_STATUS",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    armed_state_channel = client.channels.create(
        name="HBR_ABORT_ARMED_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    seal_pressure_redline_channel = client.channels.create(
        name="HBR_SEAL_PRESSURE_REDLINE",
        data_type="Float32",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    motor_thermal_redline_channel = client.channels.create(
        name="HBR_MOTOR_THERMAL_REDLINE",
        data_type="Float32",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    log_channel = client.channels.create(
        name="HBR_LOG",
        data_type="String",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    pt_eth_seal_channel = client.channels.create(
        name="PT-ETH-SEAL",
        data_type="Float32",
        virtual=False,
        retrieve_if_name_exists=True,
    )

    tc_pump_motor_channel = client.channels.create(
        name="TC-PUMP-MOTOR",
        data_type="Float32",
        virtual=False,
        retrieve_if_name_exists=True,
    )

    close_regulate_channel = client.channels.create(
        name="HBR_CLOSE_REGULATOR",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    arm_key = arm_channel.key
    abort_key = abort_channel.key
    single_shutdown_key = single_shutdown_channel.key
    total_shutdown_key = total_shutdown_channel.key
    status_key = status_channel.key
    armed_state_key = armed_state_channel.key
    abort_active_key = abort_active_channel.key
    sequence_active_key = sequence_active_channel.key
    seal_pressure_redline_key = seal_pressure_redline_channel.key
    motor_thermal_redline_key = motor_thermal_redline_channel.key
    log_key = log_channel.key
    pt_eth_seal_key = pt_eth_seal_channel.key
    tc_pump_motor_key = tc_pump_motor_channel.key
    close_regulate_key = close_regulate_channel.key

    arm_flag = False
    active_flag = True
    shutdown_flag = False
    seal_pressure_redline = 0
    motor_thermal_redline = 0

    with client.open_streamer([arm_key, abort_key,  single_shutdown_key, total_shutdown_key, seal_pressure_redline_key, motor_thermal_redline_key, pt_eth_seal_key, tc_pump_motor_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[armed_state_key, status_key, abort_active_key, sequence_active_key, log_key, close_regulate_key], enable_auto_commit=True) as writer:
        
        log_event("Connected to Synnax for trigger monitoring", writer, log_key)
        log_event("Listening for trigger signals", writer, log_key)
        writer.write({status_key: [1]})
        for frame in streamer:
            for v in frame[total_shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            for v in frame[single_shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            for v in frame[arm_key]:
                if v == 1:
                    arm_flag = True
                    log_event('Abort Armed.', writer, log_key)
                elif v == 0:
                    arm_flag = False
                    log_event('Abort Disarmed.', writer, log_key)  
            for v in frame[seal_pressure_redline_key]:
                if v != 0:
                    seal_pressure_redline = v
                    log_event(f"Seal pressure redline set to {seal_pressure_redline} psi", writer, log_key)
            for v in frame[motor_thermal_redline_key]:
                if v != 0:
                    motor_thermal_redline = v
                    log_event(f"Motor thermal redline set to {motor_thermal_redline} f", writer, log_key)
            for v in frame[pt_eth_seal_key]:
                if v > seal_pressure_redline:
                    if arm_flag and active_flag:
                        log_event("Seal pressure redline exceded, aborting test.", writer, log_key)
                        writer.write({status_key: [0]})
                        writer.write({abort_active_key: [1]})
                        writer.write({sequence_active_key: [0]})
                        run_abort(writer, log_key, close_regulate_key)
                        writer.write({status_key: [1]})
                        writer.write({abort_active_key: [0]})
            for v in frame[tc_pump_motor_key]:
                if v > motor_thermal_redline:
                    if arm_flag and active_flag:
                        log_event("Motor temperature exceded, aborting test.", writer, log_key)
                        writer.write({status_key: [0]})
                        writer.write({abort_active_key: [1]})
                        writer.write({sequence_active_key: [0]})
                        run_abort(writer, log_key, close_regulate_key)
                        writer.write({status_key: [1]})
                        writer.write({abort_active_key: [0]})
            for v in frame[abort_key]:
                if arm_flag and active_flag and v == 1:
                    log_event("Trigger received, starting abort sequence", writer, log_key)
                    writer.write({status_key: [0]})
                    writer.write({abort_active_key: [1]})
                    writer.write({sequence_active_key: [0]})
                    run_abort(writer, log_key, close_regulate_key)
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