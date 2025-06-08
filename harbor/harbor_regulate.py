import synnax as sy # type: ignore
from datetime import datetime

ENERGIZE = 0
DEENERGIZE = 1

def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"Regulate: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})

def close_regulator(writer, log_key):
    try:
        #add command to close reg
        log_event("Regulator closed.", writer, log_key)
    except Exception as e:
        log_event(f"Regulator failed to close:  {str(e)}", writer, log_key)

def open_regulator(writer, log_key):
    try:
        #add command to open reg
        log_event("Regulator Opened.", writer, log_key)
    except Exception as e:
        log_event(f"Regulator failed to open:  {str(e)}", writer, log_key)

def regulate(writer, log_key, pressure_setpoint):
    try:
        #add command to start regulation at {pressure_setpoint}
        log_event(f"Regulator activated, regulating at {str(pressure_setpoint)} psi.", writer, log_key)
    except Exception as e:
        log_event(f"Regulator failed to activate:  {str(e)}", writer, log_key)

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
        name="HBR_ARM_REGULATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    run_regulate_channel = client.channels.create(
        name="HBR_RUN_REGULATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    single_shutdown_channel = client.channels.create(
        name="HBR_REGULATE_SHUTDOWN",
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

    status_channel = client.channels.create(
        name="HBR_REGULATE_STATUS",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    armed_state_channel = client.channels.create(
        name="HBR_REGULATE_ARMED_STATE",
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

    regulate_setpoint_channel = client.channels.create(
        name="HBR_REGULATE_SETPOINT",
        data_type="float32",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    log_channel = client.channels.create(
        name="HBR_LOG",
        data_type="String",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    close_regulate_channel = client.channels.create(
        name="HBR_CLOSE_REGULATOR",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    open_regulate_channel = client.channels.create(
        name="HBR_OPEN_REGULATOR",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    open_state_channel = client.channels.create(
        name="HBR_REGULATE_OPEN_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    closed_state_channel = client.channels.create(
        name="HBR_REGULATE_CLOSED_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    regulate_state_channel = client.channels.create(
        name="HBR_REGULATE_REGULATING_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    parameter_state_channel = client.channels.create(
        name="HBR_REGULATE_PARAMETERS_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    arm_key = arm_channel.key
    run_regulate_key = run_regulate_channel.key
    single_shutdown_key = single_shutdown_channel.key
    total_shutdown_key = total_shutdown_channel.key
    status_key = status_channel.key
    armed_state_key = armed_state_channel.key
    arm_abort_key = arm_abort_channel.key
    regulate_setpoint_key = regulate_setpoint_channel.key
    log_key = log_channel.key
    close_regulate_key = close_regulate_channel.key
    open_regulate_key = open_regulate_channel.key
    open_state_key = open_state_channel.key
    closed_state_key = closed_state_channel.key
    regulate_state_key = regulate_state_channel.key
    parameter_state_key = parameter_state_channel.key

    arm_flag = False
    arm_abort_flag = False
    active_flag = True
    shutdown_flag = False
    open_flag = False
    closed_flag = True
    regulating_flag = False
    parameter_flag = False
    regulate_setpoint = 0

    with client.open_streamer([arm_key, run_regulate_key, single_shutdown_key, total_shutdown_key, arm_abort_key, regulate_setpoint_key, close_regulate_key, open_regulate_key]) as streamer, \
        client.open_writer(start=sy.TimeStamp.now(), channels=[status_key, armed_state_key, log_key, open_state_key, closed_state_key, regulate_state_key, parameter_state_key], enable_auto_commit=True) as writer:
        
        log_event("Connected to Synnax for trigger monitoring", writer, log_key)
        log_event("Listening for trigger signals", writer, log_key)
        writer.write({status_key: [1]})
        writer.write({closed_state_key: [1]})
        for frame in streamer:
            for v in frame[single_shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            for v in frame[total_shutdown_key]:
                if v == 1:
                    shutdown_flag = True
            for v in frame[arm_key]:
                if v == 1:
                    arm_flag = True
                    log_event('Regulate armed', writer, log_key)
                elif v == 0:
                    arm_flag = False
                    log_event('Regulate disarmed', writer, log_key) 
            for v in frame[arm_abort_key]:
                if v == 1:
                    arm_abort_flag = True
                else:
                    arm_abort_flag = False
            for v in frame[regulate_setpoint_key]:
                if v != 0:
                    regulate_setpoint = v
                    parameter_flag = True
                    log_event(f"Regulate setpoint set to {regulate_setpoint} psi", writer, log_key)
            for v in frame[run_regulate_key]:
                if arm_abort_flag:
                    if arm_flag:
                        if parameter_flag:
                            try:
                                log_event('Activating Regulator.', writer, log_key)
                                regulate(writer, log_key, regulate_setpoint)
                                closed_flag = False
                                regulating_flag = True
                                open_flag = False
                            except Exception as e:
                                log_event(f"Regulator failed to activate:  {str(e)}", writer, log_key)
            for v in frame[open_regulate_key]:
                if not open_flag:
                        try:
                            log_event('Opening Regulator.', writer, log_key)
                            open_regulator(writer, log_key)
                            closed_flag = False
                            regulating_flag = False
                            open_flag = True
                        except Exception as e:
                            log_event(f"Regulator failed to open:  {str(e)}", writer, log_key)
            for v in frame[close_regulate_key]:  
                if not closed_flag:
                    try:
                        log_event('Closing Regulator.', writer, log_key)
                        close_regulator(writer, log_key)
                        closed_flag = True
                        regulating_flag = False
                        open_flag = False
                    except Exception as e:
                        log_event(f"Regulator failed to close:  {str(e)}", writer, log_key)

            writer.write({armed_state_key: [1 if arm_flag else 0]})
            writer.write({status_key: [1 if active_flag else 0]})
            writer.write({parameter_state_key: [1 if parameter_flag else 0]})
            writer.write({open_state_key: [1 if open_flag else 0]})
            writer.write({closed_state_key: [1 if closed_flag else 0]})
            writer.write({regulate_state_key: [1 if regulating_flag else 0]})

            if shutdown_flag:
                writer.write({status_key: [0]})
                writer.write({armed_state_key: [0]})
                if not closed_flag:
                    log_event('Closing Regulator.', writer, log_key)
                    close_regulator(writer, log_key)
                    writer.write({open_state_key: [0]})
                    writer.write({regulate_state_key: [0]})
                writer.write({closed_state_key: [0]})
                writer.write({parameter_state_key: [0]})
                log_event('Shutting down regulator', writer, log_key)
                break

if __name__ == "__main__":
    wait_for_trigger()    