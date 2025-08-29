import synnax as sy # type: ignore
from datetime import datetime

ENERGIZE = 0
DEENERGIZE = 1

onboard_active = False

def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"Pump Auto: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})

# Main autosequence
def run_sequence(writer, log_key, test_duration_setpoint, pump_outlet_setpoint, run_regulate_key, close_regulate_key, eth_inlet_cmd_key, eth_outlet_cmd_key):
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
            name="Pump Test Autosequence",
            write_authorities=[200],
            write=[INLET_CMD, OUTLET_CMD],
            read=[INLET_STATE, OUTLET_STATE],
        ) as ctrl:
            with client.open_writer(start=sy.TimeStamp.now(), channels=[run_regulate_key, close_regulate_key, eth_inlet_cmd_key, eth_outlet_cmd_key], enable_auto_commit=True) as writer2:
                log_event('Autosequence initiated', writer, log_key)

                # Mark the start of the sequence
                start = sy.TimeStamp.now()

                #activate regulator
                writer2.write({run_regulate_key: [1]})
                ctrl.sleep(2)

                #prime pump
                writer2.write({eth_inlet_cmd_key: [1]})
                log_event("Inlet opened sucessfully.", writer, log_key)
            
                '''
                ctrl[INLET_CMD] = ENERGIZE

                # Wait until the Inlet is opened
                if ctrl.wait_until(
                    lambda c: c[INLET_STATE] == ENERGIZE,
                    timeout= 1 * sy.TimeSpan.SECOND, 
                ):
                    log_event("Inlet opened sucessfully.", writer, log_key)
                else:
                    log_event("Failed to open inlet.", writer, log_key)
                    break
                '''

                log_event("Priming pump.", writer, log_key)

                #wait for pump to prime
                ctrl.sleep(5)
                log_event("Pump is primed, proceeding with test.", writer, log_key)

                #start pump
                #add command to start pump with [pump_outlet_setpoint]

                #open run line
                writer2.write({eth_outlet_cmd_key: [1]})
                log_event("Outlet opened sucessfully.", writer, log_key)
                '''
                ctrl[OUTLET_CMD] = ENERGIZE

                # Wait until the run line is open
                if ctrl.wait_until(
                    lambda c: c[OUTLET_STATE] == ENERGIZE,
                    timeout= 1 * sy.TimeSpan.SECOND, 
                ):
                    log_event("Outlet opened sucessfully.", writer, log_key)
                else:
                    log_event("Failed to open outlet.", writer, log_key)
                    break
                '''

                #wait for test to run
                ctrl.sleep(float(test_duration_setpoint))

                #stop pump
                #add command to shut down pump

                #close reg
                writer2.write({close_regulate_key: [1]})

                #Shutoff inlet
                writer2.write({eth_inlet_cmd_key: [0]})
                log_event("Inlet closed sucessfully.", writer, log_key)
                '''
                ctrl[INLET_CMD] = DEENERGIZE

                # Wait until the Inlet is shutoff
                if ctrl.wait_until(
                    lambda c: c[INLET_STATE] == DEENERGIZE,
                    timeout= 1 * sy.TimeSpan.SECOND, 
                ):
                    log_event("Inlet closed sucessfully.", writer, log_key)
                else:
                    log_event("Failed to close inlet.", writer, log_key)
                    break
                '''

                #Shutoff Outlet
                writer2.write({eth_outlet_cmd_key: [0]})
                log_event("Outlet closed sucessfully.", writer, log_key)
                '''
                ctrl[OUTLET_CMD] = DEENERGIZE

                # Wait until the Inlet is shutoff
                if ctrl.wait_until(
                    lambda c: c[OUTLET_STATE] == DEENERGIZE,
                    timeout= 1 * sy.TimeSpan.SECOND, 
                ):
                    log_event("Outlet closed sucessfully.", writer, log_key)
                else:
                    log_event("Failed to close outlet.", writer, log_key)
                    break
                '''
                # Mark the end of the sequence
                end = sy.TimeStamp.now()

                # Label the sequence with the end time
                client.ranges.create(
                    name=f"Abort Sequence {end}",
                    time_range=sy.TimeRange(start=start, end=end),
                )

                log_event(f"Pump Test Autosequence completed: {start} to {end}", writer, log_key)
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
        name="HBR_ARM_AUTOSEQUENCE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    run_channel = client.channels.create(
        name="HBR_RUN_AUTOSEQUENCE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    reset_channel = client.channels.create(
        name="HBR_RESET_AUTOSEQUENCE",
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
        name="HBR_AUTOSEQUENCE_SHUTDOWN",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    status_channel = client.channels.create(
        name="HBR_AUTOSEQUENCE_STATUS",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    armed_state_channel = client.channels.create(
        name="HBR_AUTOSEQUENCE_ARMED_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    arm_abort_channel = client.channels.create(
        name="HBR_ARM_ABORT",
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

    pump_parameters_state_channel = client.channels.create(
        name="HBR_PUMP_PARAMETERS_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    log_channel = client.channels.create(
        name="HBR_LOG",
        data_type="String",
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

    pump_outlet_setpoint_channel = client.channels.create(
        name="HBR_PUMP_OUTLET_SETPOINT",
        data_type="Float32",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    test_duration_setpoint_channel = client.channels.create(
        name="HBR_TEST_DURATION_SETPOINT",
        data_type="Float32",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    run_regulate_channel = client.channels.create(
        name="HBR_RUN_REGULATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    close_regulate_channel = client.channels.create(
        name="HBR_CLOSE_REGULATOR",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    eth_outlet_cmd_channel = client.channels.create(
        name="PV-ETH-OUTLET_cmd",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    eth_inlet_cmd_channel = client.channels.create(
        name="PV-ETH-INLET_cmd",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    arm_key = arm_channel.key
    run_key = run_channel.key
    reset_key = reset_channel.key
    total_shutdown_key = total_shutdown_channel.key
    single_shutdown_key = single_shutdown_channel.key
    status_key = status_channel.key
    armed_state_key = armed_state_channel.key
    arm_abort_key = arm_abort_channel.key
    sequence_active_key = sequence_active_channel.key
    pump_parameters_state_key = pump_parameters_state_channel.key
    log_key = log_channel.key
    seal_pressure_redline_key = seal_pressure_redline_channel.key
    motor_thermal_redline_key = motor_thermal_redline_channel.key
    pump_outlet_setpoint_key = pump_outlet_setpoint_channel.key
    test_duration_setpoint_key = test_duration_setpoint_channel.key
    run_regulate_key = run_regulate_channel.key
    close_regulate_key = close_regulate_channel.key
    eth_outlet_cmd_key = eth_outlet_cmd_channel.key
    eth_inlet_cmd_key = eth_inlet_cmd_channel.key

    arm_flag = False
    arm_abort_flag = False
    active_flag = True
    shutdown_flag = False
    pump_parameter_flag = False
    seal_pressure_redline = 0
    motor_thermal_redline = 0
    pump_outlet_setpoint = 0
    test_duration_setpoint = 0

    with client.open_streamer([arm_key, run_key, reset_key, total_shutdown_key, single_shutdown_key, arm_abort_key, seal_pressure_redline_key, motor_thermal_redline_key, pump_outlet_setpoint_key, test_duration_setpoint_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[armed_state_key, status_key, sequence_active_key, pump_parameters_state_key, log_key], enable_auto_commit=True) as writer:
        
        log_event("Connected to Synnax for trigger monitoring", writer, log_key)
        log_event("Listening for trigger signals", writer, log_key)
        writer.write({status_key: [1]})
        for frame in streamer:
            for v in frame[reset_key]:
                if v == 1:
                    active_flag = True
                    log_event('Autosequence reset', writer, log_key)
            for v in frame[total_shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            for v in frame[single_shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            for v in frame[arm_key]:
                if v == 1 and pump_parameter_flag and active_flag:
                    arm_flag = True
                    log_event('Autosequence armed', writer, log_key)
                elif v == 0 and pump_parameter_flag and active_flag:
                    arm_flag = False
                    log_event('Autosequence disarmed', writer, log_key) 
            for v in frame[arm_abort_key]:
                if v == 1:
                    arm_abort_flag = True
                elif v == 0:
                    arm_abort_flag = False
            for v in frame[seal_pressure_redline_key]:
                if v != 0:
                    seal_pressure_redline = v
            for v in frame[motor_thermal_redline_key]:
                if v != 0:
                    motor_thermal_redline = v
            for v in frame[pump_outlet_setpoint_key]:
                if v != 0:
                    pump_outlet_setpoint = v
                    log_event(f"Pump outlet setpoint set to {pump_outlet_setpoint} psi", writer, log_key)
            for v in frame[test_duration_setpoint_key]:
                if v != 0:
                    test_duration_setpoint = v
                    log_event(f"Test duration setpoint set to {test_duration_setpoint} seconds", writer, log_key)  
            for v in frame[run_key]:
                if arm_flag and active_flag and arm_abort_flag and v == 1:
                    print(test_duration_setpoint)
                    log_event("Trigger received, starting Autosequence", writer, log_key)
                    writer.write({armed_state_key: [0]})
                    writer.write({status_key: [0]})
                    writer.write({sequence_active_key: [1]})
                    active_flag = False 
                    arm_flag = False
                    run_sequence(writer, log_key, test_duration_setpoint, pump_outlet_setpoint, run_regulate_key, close_regulate_key, eth_inlet_cmd_key, eth_outlet_cmd_key)
                    writer.write({sequence_active_key: [0]})

            if seal_pressure_redline != 0 and motor_thermal_redline != 0 and pump_outlet_setpoint != 0 and test_duration_setpoint != 0:
                pump_parameter_flag = True
            else:
                pump_parameter_flag = False

            writer.write({armed_state_key: [1 if arm_flag else 0]})
            writer.write({status_key: [1 if active_flag else 0]})
            writer.write({pump_parameters_state_key: [1 if pump_parameter_flag else 0]})

            if shutdown_flag:
                writer.write({status_key: [0]})
                writer.write({armed_state_key: [0]})
                writer.write({pump_parameters_state_key: [0]})
                log_event('Shutting down autosequence', writer, log_key)
                break

if __name__ == "__main__":
    wait_for_trigger()    