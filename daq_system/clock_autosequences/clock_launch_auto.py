import synnax as sy # type: ignore
from datetime import datetime
import sys
import os
import command as cmd # type: ignore

#MAKE SURE SET TO TRUE BEFORE REAL TESTING
######################
onboard_active = True
######################

ENERGIZE = 0
DEENERGIZE = 1

default_authority = 10 #control autohrity when not running an action
action_authority = 201 #control authority for running an action

log_list = []

#HARDCODED VARIABLES
#T-TIMES in milliseconds

global test_name
test_name = "Launch"

main_hold_time = -20000 #Main hold while waiting for prop fill to complete
pop_qd_time = -19000 #pop QDs at t-24s
qd_wait_time = -16000 #start post pop wait at t-16s
activate_purge_time = -15000 #activate purge at t-15s
pre_press_time = -12000 #start prepress at t-12s
pre_press_wait_time = 3000 #wait for 3s before checking prepress sucess condition
fire_igniter_time = -3000 #fire igniter at t-3s
fire_actuator_time = 0 #fire actuator at t-0s
deenergize_pyros_time = 1000 #deenergize pyros 1s after ignition


pop_fill_qds_time = pop_qd_time
pop_vent_qds_time = pop_qd_time + 1000
pop_helium_qd_time = pop_qd_time + 2000
qd_pop_duration = 1 #flow n2 through the pushers for 1 second

prepress_margin = 15 # negative margin in psi for prepress validation
copv_lower_redline = 4500 #minimum copv pressure [psi]

def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    if onboard_active:
        fullMessage = f"[{timestamp}] {"Auto: "}{message}"
    else:
        fullMessage = f"[{timestamp}] |WARNING ONBOARD OFF| {"Auto: "}{message}"
    print(fullMessage)
    log_list.append(fullMessage)
    writer.write({log_key: [fullMessage]})

def run_event(ctrl, command, state):
    ctrl.set_authority(action_authority)
    ctrl[command] = state
    ctrl.set_authority(default_authority)

def wait_for_timestamps():
    try:
        client = sy.Synnax(
            host="192.168.2.59",
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

    clear_prepress_channel = client.channels.create(
        name="CLEAR_PREPRESS_HOLD",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    clear_main_hold_channel = client.channels.create(
        name="CLEAR_MAIN_HOLD",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    clear_main_hold_state_channel = client.channels.create(
        name="CLEAR_MAIN_HOLD_STATE",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    pull_BB_setpoints_channel = client.channels.create(
        name="PULL_BB_SETPOINTS",
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

    clock_channel = client.channels.create(
        name="T_CLOCK_MS",
        data_type="int64",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    start_clock_channel = client.channels.create(
        name="START_T_CLOCK",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    stop_clock_channel = client.channels.create(
        name="STOP_T_CLOCK",
        data_type="uint8",
        virtual=True,
        retrieve_if_name_exists=True,
    )

    t_clock_add_sec_channel = client.channels.create(
        name='T_CLOCK_ADD_SEC',
        data_type='int64',
        virtual=True,
        retrieve_if_name_exists=True,
    )

    record_data_channel = client.channels.create(
        name='RECORD_DATA',
        data_type='uint8',
        virtual=True,
        retrieve_if_name_exists=True,
    )

    copv_override_channel = client.channels.create(
        name='COPV_OVERRIDE',
        data_type='uint8',
        virtual=True,
        retrieve_if_name_exists=True,
    )

    copv_override_state_channel = client.channels.create(
        name='COPV_OVERRIDE_STATE',
        data_type='uint8',
        virtual=True,
        retrieve_if_name_exists=True,
    )

    copv_fill_light_channel = client.channels.create(
        name='COPV_FILL_LIGHT',
        data_type='uint8',
        virtual=True,
        retrieve_if_name_exists=True,
    )
    # Define the control channel names
    IGNITOR_CMD = "IGNITOR_cmd"
    IGNITOR_STATE = "IGNITOR_state"

    PURGE_CMD = "SV_N2_01_cmd"
    PURGE_STATE = "SV_N2_01_state"

    ACTUATOR_CMD = "ACTUATOR_cmd"
    ACTUATOR_STATE = "ACTUATOR_state"

    VENT_QD_CMD = "SV_QD_01_cmd"
    VENT_QD_STATE = "SV_QD_01_state"

    HELIUM_QD_CMD = "SV_QD_03_cmd"
    HELIUM_QD_STATE = "SV_QD_03_state"

    FILL_QD_CMD = "SV_QD_02_cmd"
    FILL_QD_STATE = "SV_QD_02_state"
    
    if onboard_active:
        COPV_PRESSURE = "PT_HE_201"
        OX_TANK_PRESSURE = "PT_OX_201"
        FU_TANK_PRESSURE = "PT_FU_201"
    else:
        COPV_PRESSURE = "PT_HE_01"  
        OX_TANK_PRESSURE = "PT_OX_02"
        FU_TANK_PRESSURE = "PT_FU_02"
    
    FU_UPPER = "FU_UPPER_SETP"
    FU_LOWER = "FU_LOWER_SETP"
    FU_REDLINE = "FU_UPPER_REDLINE"

    OX_UPPER = "OX_UPPER_SETP"
    OX_LOWER = "OX_LOWER_SETP"
    OX_REDLINE = "OX_UPPER_REDLINE"

    T_CLOCK_ENABLE = "SET_T_CLOCK_ENABLE"
    T_CLOCK_STATE = "T_CLOCK_ENABLE"

    CLEAR_PREPRESS = clear_prepress_channel.key

    COPV_LIGHT = "COPV_FILL_LIGHT"

    arm_key = arm_channel.key
    shutdown_key = shutdown_channel.key
    status_key = status_channel.key
    armed_state_key = armed_state_channel.key
    arm_abort_key = arm_abort_channel.key
    sequence_active_key = sequence_active_channel.key
    log_key = log_channel.key
    clock_key = clock_channel.key
    start_clock_key = start_clock_channel.key
    stop_clock_key = stop_clock_channel.key
    pull_BB_setpoints_key = pull_BB_setpoints_channel.key
    clear_main_hold_key = clear_main_hold_channel.key
    clear_main_hold_state_key = clear_main_hold_state_channel.key
    t_clock_add_sec_key = t_clock_add_sec_channel.key
    record_data_key = record_data_channel.key
    copv_override_key = copv_override_channel.key
    copv_override_state_key = copv_override_state_channel.key
    copv_fill_light_key = copv_fill_light_channel.key

    #command channel flags
    arm_flag = False
    arm_abort_flag = False
    active_flag = True
    shutdown_flag = False

    #control channel flags
    purge_activated_flag = False
    vent_qds_popped_flag = False
    fill_qds_popped_flag = False
    helium_qd_popped_flag = False
    marottas_regulated_flag = False
    prepress_hold_cleared_flag = False
    main_hold_cleared_flag = False
    igniter_fired_flag = False
    actuator_fired_flag = False
    sequence_started_flag = False
    copv_full_flag = False
    recording_data_flag = False
    pyros_deenergized_flag = False

    #input and output keys for streamer
    input_keys = [
        arm_key, 
        shutdown_key, 
        arm_abort_key, 
        clock_key,
        pull_BB_setpoints_key,
        clear_main_hold_key,
        record_data_key,
        copv_override_key,
    ]

    output_keys = [
        armed_state_key, 
        status_key, 
        sequence_active_key, 
        log_key, 
        start_clock_key, 
        stop_clock_key, 
        clear_main_hold_state_key,
        copv_override_state_key,
        copv_fill_light_key,
    ]

    #input and output channels for control sequence
    input_authorities = [
        IGNITOR_STATE, 
        PURGE_STATE, 
        ACTUATOR_STATE, 
        VENT_QD_STATE, 
        FILL_QD_STATE,
        HELIUM_QD_STATE, 
        FU_TANK_PRESSURE, 
        OX_TANK_PRESSURE,
        COPV_PRESSURE,
        CLEAR_PREPRESS,
        T_CLOCK_STATE,
    ]

    output_authorities = [
        IGNITOR_CMD,  
        PURGE_CMD, 
        ACTUATOR_CMD, 
        VENT_QD_CMD,
        FILL_QD_CMD,
        HELIUM_QD_CMD, 
        T_CLOCK_ENABLE,
        COPV_LIGHT,
    ]

    with client.control.acquire(
            name="Automatic Control System",
            write= output_authorities,
            read= input_authorities,
            write_authorities=[10],  # Set low authority to prevent interference
        ) as ctrl:
            with client.open_streamer(input_keys) as streamer, \
                client.open_writer(start=sy.TimeStamp.now(), channels= output_keys, enable_auto_commit=True) as writer:

                #if broken remove float() and :.2f
                log_event("Connected to Synnax for trigger monitoring", writer, log_key)
                log_event("Listening for trigger signals", writer, log_key)
                fu_lower_setpoint = float(client.read_latest(FU_LOWER))
                fu_upper_setpoint = float(client.read_latest(FU_UPPER))
                fu_redline_setpoint = float(client.read_latest(FU_REDLINE))
                ox_lower_setpoint = float(client.read_latest(OX_LOWER))
                ox_upper_setpoint = float(client.read_latest(OX_UPPER))
                ox_redline_setpoint = float(client.read_latest(OX_REDLINE))

                fu_lower = fu_lower_setpoint - prepress_margin
                fu_upper = fu_redline_setpoint - prepress_margin
                ox_lower = ox_lower_setpoint - prepress_margin
                ox_upper = ox_redline_setpoint - prepress_margin

                log_event(f"FU Lower BB Setpoint: {fu_lower_setpoint:.2f}psi", writer, log_key)
                log_event(f"FU Upper BB Setpoint: {fu_upper_setpoint:.2f}psi", writer, log_key)
                log_event(f"FU Redline Setpoint: {fu_redline_setpoint:.2f}psi", writer, log_key)
                log_event(f"OX Lower BB Setpoint: {ox_lower_setpoint:.2f}psi", writer, log_key)
                log_event(f"OX Upper BB Setpoint: {ox_upper_setpoint:.2f}psi", writer, log_key)
                log_event(f"OX Redline Setpoint: {ox_redline_setpoint:.2f}psi", writer, log_key)

                log_event(f"FU Lower Validation Setpoint: {fu_lower:.2f}psi", writer, log_key)
                log_event(f"FU Upper Validation Setpoint: {fu_upper:.2f}psi", writer, log_key)
                log_event(f"OX Lower Validation Setpoint: {ox_lower:.2f}psi", writer, log_key)
                log_event(f"OX Upper Validation Setpoint: {ox_upper:.2f}psi", writer, log_key)
                writer.write({status_key: [1]})

                refrence_time = sy.TimeStamp.now()
                fill_start_time = refrence_time
                shutdown_time = refrence_time
                test_start_time = refrence_time
                test_end_time = refrence_time

                for frame in streamer:
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
                    for v in frame[clear_main_hold_key]:
                        if v == 1:
                            main_hold_cleared_flag = True
                        elif main_hold_cleared_flag == True:
                            main_hold_cleared_flag = False 
                    for v in frame[clock_key]:
                        current_t_time = v 
                    for v in frame[pull_BB_setpoints_key]:
                        if v == 1:
                            fu_lower_setpoint = float(client.read_latest(FU_LOWER))
                            fu_upper_setpoint = float(client.read_latest(FU_UPPER))
                            fu_redline_setpoint = float(client.read_latest(FU_REDLINE))
                            ox_lower_setpoint = float(client.read_latest(OX_LOWER))
                            ox_upper_setpoint = float(client.read_latest(OX_UPPER))
                            ox_redline_setpoint = float(client.read_latest(OX_REDLINE))

                            fu_lower = fu_lower_setpoint - prepress_margin
                            fu_upper = fu_redline_setpoint - prepress_margin
                            ox_lower = ox_lower_setpoint - prepress_margin
                            ox_upper = ox_redline_setpoint - prepress_margin

                            log_event(f"FU Lower BB Setpoint: {fu_lower_setpoint:.2f}psi", writer, log_key)
                            log_event(f"FU Upper BB Setpoint: {fu_upper_setpoint:.2f}psi", writer, log_key)
                            log_event(f"FU Redline Setpoint: {fu_redline_setpoint:.2f}psi", writer, log_key)
                            log_event(f"OX Lower BB Setpoint: {ox_lower_setpoint:.2f}psi", writer, log_key)
                            log_event(f"OX Upper BB Setpoint: {ox_upper_setpoint:.2f}psi", writer, log_key)
                            log_event(f"OX Redline Setpoint: {ox_redline_setpoint:.2f}psi", writer, log_key)

                            log_event(f"FU Lower Validation Setpoint: {fu_lower:.2f}psi", writer, log_key)
                            log_event(f"FU Upper Validation Setpoint: {fu_upper:.2f}psi", writer, log_key)
                            log_event(f"OX Lower Validation Setpoint: {ox_lower:.2f}psi", writer, log_key)
                            log_event(f"OX Upper Validation Setpoint: {ox_upper:.2f}psi", writer, log_key)
                    for v in frame[record_data_key]:
                        if v == 1:
                            if recording_data_flag == False:
                                recording_data_flag = True
                                fill_start_time = sy.TimeStamp.now()
                                log_event('Starting data recording', writer, log_key)
                        elif v == 0:
                            if recording_data_flag == True:
                                recording_data_flag = False
                                shutdown_time = sy.TimeStamp.now()
                                log_event('Stopping data recording', writer, log_key)
                    for v in frame[copv_override_key]:
                        writer.write({copv_override_state_key: [1 if v  == 1 else 0]})
                        if v == 1 or ctrl[COPV_PRESSURE] >= copv_lower_redline:
                            copv_full_flag = True
                        else:
                            copv_full_flag = False
                            
                    writer.write({armed_state_key: [1 if arm_flag else 0]})
                    writer.write({clear_main_hold_state_key: [1 if main_hold_cleared_flag else 0]})

                    if shutdown_flag:
                        writer.write({armed_state_key: [0]})
                        writer.write({sequence_active_key: [0]})
                        writer.write({copv_override_state_key: [0]})
                        writer.write({copv_fill_light_key: [0]})

                        log_event(f'Full Range Name: "{test_name}_full_dataset"', writer, log_key)
                        log_event(f'Fill start Timestamp: {fill_start_time}', writer, log_key)
                        log_event(f'Shutdown Timestamp: {shutdown_time}', writer, log_key)
                        log_event(f'Test Range Name: "{test_name}_test_data"', writer, log_key)
                        log_event(f'Test start Timestamp: {test_start_time}', writer, log_key)
                        log_event(f'Test End Timestamp: {test_end_time}', writer, log_key)

                        log_event('Logging log events to the log event log.', writer, log_key)
                        log_event('Shutting down autosequence', writer, log_key)
                        output_log_file = open(rf"daq_system/utils/{test_name}_log", 'w')
                        for v in log_list:
                            output_log_file.write(v + "\n")
                        writer.write({status_key: [0]})
                        break

                    
                    #check to see if we should be scanning for autosequence timings
                    writer.write({copv_fill_light_key: [1 if ctrl[COPV_PRESSURE] >= copv_lower_redline else 0]})
                    if ctrl[COPV_PRESSURE] >= copv_lower_redline:
                        copv_full_flag = True

                    if current_t_time >= main_hold_time and current_t_time <= 2000:
                        if main_hold_cleared_flag == True and arm_flag == True and arm_abort_flag == True and copv_full_flag == True and sequence_started_flag == False:
                            if ctrl[T_CLOCK_STATE] == 0:
                                run_event(ctrl, T_CLOCK_ENABLE, 1)
                                log_event('Main hold cleared, starting sequence', writer, log_key)
                                sequence_started_flag = True
                                test_start_time = sy.TimeStamp.now() - 30 * sy.TimeSpan.SECOND
                            writer.write({sequence_active_key: [1]})
                        elif main_hold_cleared_flag == True and arm_flag == True and arm_abort_flag == True and sequence_started_flag == True:
                            if ctrl[T_CLOCK_STATE] == 0:
                                run_event(ctrl, T_CLOCK_ENABLE, 1)
                            #check current t-time to set what items have already passed in the countdown
                            if current_t_time < main_hold_time and main_hold_cleared_flag == True:
                                main_hold_cleared_flag = False
                            if current_t_time < main_hold_time and sequence_started_flag == True:
                                sequence_started_flag = False
                            if current_t_time <= activate_purge_time and purge_activated_flag == True:
                                purge_activated_flag = False
                            if current_t_time <= pop_vent_qds_time and vent_qds_popped_flag == True: 
                                vent_qds_popped_flag = False
                            if current_t_time <= pop_fill_qds_time and fill_qds_popped_flag == True: 
                                fill_qds_popped_flag = False
                            if current_t_time <= pop_helium_qd_time and helium_qd_popped_flag == True: 
                                helium_qd_popped_flag = False
                            if current_t_time <= pre_press_time and marottas_regulated_flag == True:
                                marottas_regulated_flag = False
                            if current_t_time <= (pre_press_time + pre_press_wait_time) and prepress_hold_cleared_flag == True:
                                prepress_hold_cleared_flag = False
                            if current_t_time <= fire_igniter_time and igniter_fired_flag == True:
                                igniter_fired_flag = False
                            if current_t_time <= fire_actuator_time and actuator_fired_flag == True:
                                actuator_fired_flag = False
                            if current_t_time <= deenergize_pyros_time and pyros_deenergized_flag == True:
                                pyros_deenergized_flag = False

                            #scan for events that need to be activated
                            if current_t_time > activate_purge_time and purge_activated_flag == False:
                                run_event(ctrl, PURGE_CMD, ENERGIZE)
                                purge_activated_flag = True
                                log_event("Activating N2-Purge", writer, log_key)

                            if current_t_time > pop_vent_qds_time and vent_qds_popped_flag == False:
                                log_event("Popping Vent QDs", writer, log_key)
                                run_event(ctrl, VENT_QD_CMD, ENERGIZE)
                                vent_qds_popped_flag = True
                                ctrl.sleep(qd_pop_duration)
                                run_event(ctrl, VENT_QD_CMD, DEENERGIZE)
                                log_event("Vent QDs popped", writer, log_key)

                            if current_t_time > pop_fill_qds_time and fill_qds_popped_flag == False:
                                log_event("Popping Fill QDs", writer, log_key)
                                run_event(ctrl, FILL_QD_CMD, ENERGIZE)
                                fill_qds_popped_flag = True
                                ctrl.sleep(qd_pop_duration)
                                run_event(ctrl, FILL_QD_CMD, DEENERGIZE)
                                log_event("Fill QDs popped", writer, log_key)

                            if current_t_time > pop_helium_qd_time and helium_qd_popped_flag == False:
                                log_event("Popping Helium QD", writer, log_key)
                                run_event(ctrl, HELIUM_QD_CMD, ENERGIZE)
                                helium_qd_popped_flag = True
                                ctrl.sleep(qd_pop_duration)
                                run_event(ctrl, HELIUM_QD_CMD, DEENERGIZE)
                                log_event("Helium QD popped", writer, log_key)

                            if current_t_time > pre_press_time and marottas_regulated_flag == False:
                                if onboard_active:
                                    cmd.send_command("SET_OX_STATE_REGULATE")
                                    cmd.send_command("SET_FU_STATE_REGULATE")
                                    print("0")
                                else:
                                    log_event("FAILED TO REGULATE, ONBOARD INACTIVE", writer, log_key)
                                marottas_regulated_flag = True
                                log_event("Starting Prepress", writer, log_key)
                                
                            if current_t_time > pre_press_time + pre_press_wait_time and prepress_hold_cleared_flag == False:
                                if  ctrl[FU_TANK_PRESSURE] > fu_lower  and  ctrl[FU_TANK_PRESSURE] < fu_upper and  ctrl[OX_TANK_PRESSURE] > ox_lower and ctrl[OX_TANK_PRESSURE] < ox_upper:
                                    prepress_hold_cleared_flag = True
                                    log_event("Prepress Validation completed", writer, log_key)
                                else:
                                    run_event(ctrl, T_CLOCK_ENABLE, 0)
                                    if ctrl.wait_until(
                                        lambda c: (c[FU_TANK_PRESSURE] > fu_lower and c[FU_TANK_PRESSURE] < fu_upper and c[OX_TANK_PRESSURE] > ox_lower and c[OX_TANK_PRESSURE] < ox_upper) or c.get(CLEAR_PREPRESS, 0) == 1,
                                        timeout=10 * sy.TimeSpan.SECOND, 
                                    ):
                                        log_event('Prepress override engaged', writer, log_key)
                                        log_event("Prepress Validation completed", writer, log_key)
                                        run_event(ctrl, T_CLOCK_ENABLE, 1)
                                        prepress_hold_cleared_flag = True
                                    else:
                                        log_event("Failed to sucessfully prepress", writer, log_key)
                                        main_hold_cleared_flag = False

                            if current_t_time > fire_igniter_time and igniter_fired_flag == False and prepress_hold_cleared_flag == True:
                                run_event(ctrl, IGNITOR_CMD, ENERGIZE)
                                igniter_fired_flag = True
                                log_event("Firing Ignitor", writer, log_key)
                            
                            if current_t_time > fire_actuator_time and actuator_fired_flag == False and prepress_hold_cleared_flag == True:
                                run_event(ctrl, ACTUATOR_CMD, ENERGIZE)
                                actuator_fired_flag = True
                                log_event("Firing Actuator", writer, log_key)
                                test_end_time = sy.TimeStamp.now() + 30 * sy.TimeSpan.SECOND

                            if current_t_time > deenergize_pyros_time and pyros_deenergized_flag == False and prepress_hold_cleared_flag == True:
                                run_event(ctrl, ACTUATOR_CMD, DEENERGIZE)
                                run_event(ctrl, IGNITOR_CMD, DEENERGIZE)
                                log_event("Pyros Deenergized", writer, log_key)
                                pyros_deenergized_flag = True

                        else:
                            if ctrl[T_CLOCK_STATE] == 1:
                                run_event(ctrl, T_CLOCK_ENABLE, 0)
                                
                    else:
                        writer.write({sequence_active_key: [0]})
                        writer.write({clear_main_hold_state_key: [0]})
                        main_hold_cleared_flag = False
        
if __name__ == "__main__":
    wait_for_timestamps()    