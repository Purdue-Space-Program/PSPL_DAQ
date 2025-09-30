import synnax as sy # type: ignore
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'PSPL_CMS_AVIONICS_COTS_FSW', 'tools')))
import command as cmd  # type: ignore

ENERGIZE = 0
DEENERGIZE = 1

def log_event(message, writer, log_key):
    """Log events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    fullMessage = f"[{timestamp}] {"Auto: "}{message}"
    print(fullMessage)
    writer.write({log_key: [fullMessage]})

def wait_for_timestamps():
    #aquire synnax connection
    
    #HARDCODED VARIABLES
    #T-TIMES in milliseconds
    main_hold_time = -25000 #Main hold while waiting for prop fill to complete
    activate_purge_time = -24000 #activate purge at t-24s
    pop_qd_time = -24000 #pop QDs at t-24s
    qd_wait_time = -20000 #start post pop wait at t-20s
    pre_press_time = -15000 #start prepress at t-15s
    pre_press_wait_time = 3000 #wait for 3s before checking prepress sucess condition
    activate_deluge_time = -8000
    fire_igniter_time = -3000 #fire igniter at t-3s
    fire_actuator_time = 0 #fire actuator at t-0s

    pop_vent_qds_time = pop_qd_time 
    pop_helium_qd_time = pop_qd_time + 2000

    prepress_margin = 5 # += margin in psi for prepress validation

    
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

    # Define the control channel names
    IGNITOR_CMD = "IGNITOR_cmd"
    IGNITOR_STATE = "IGNITOR_state"

    DELUGE_CMD = "DELUGE_cmd"
    DELUGE_STATE = "DELUGE_state"

    PURGE_CMD = "SV-N2-02_cmd"
    PURGE_STATE = "SV-N2-02_state"

    ACTUATOR_CMD = "ACTUATOR_cmd"
    ACTUATOR_STATE = "ACTUATOR_state"

    VENT_QD_CMD = "SV-QD-01_cmd"
    VENT_QD_STATE = "SV-QD-01_state"

    HELIUM_QD_CMD = "SV-QD-03_cmd"
    HELIUM_QD_STATE = "SV-QD-03_state"

    OX_TANK_PRESSURE = "PT-OX-201"
    FU_TANK_PRESSURE = "PT-FU-201"

    FU_UPPER = "FU_UPPER_SETP"
    FU_LOWER = "FU_LOWER_SETP"

    OX_UPPER = "OX_UPPER_SETP"
    OX_LOWER = "OX_LOWER_SETP"

    T_CLOCK = "SET_T_CLOCK_ENABLE"

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

    #BB setpoints
    fu_lower = client.read_latest(FU_LOWER) - prepress_margin
    fu_upper = client.read_latest(FU_UPPER) + prepress_margin
    ox_lower = client.read_latest(OX_LOWER) - prepress_margin
    ox_upper = client.read_latest(OX_UPPER) + prepress_margin

    #command channel flags
    arm_flag = False
    arm_abort_flag = False
    active_flag = True
    shutdown_flag = False

    #control channel flags
    purge_activated_flag = False
    deluge_activated_flag = False
    vent_qds_popped_flag = False
    helium_qd_popped_flag = False
    marottas_regulated_flag = False
    prepress_hold_cleared_flag = False
    igniter_fired_flag = False
    actuator_fired_flag = False

    with client.control.acquire(
            name="Automatic Control System",
            write=[IGNITOR_CMD, DELUGE_CMD, PURGE_CMD, ACTUATOR_CMD, VENT_QD_CMD, HELIUM_QD_CMD, T_CLOCK],
            read=[IGNITOR_STATE, DELUGE_STATE, PURGE_STATE, ACTUATOR_STATE, VENT_QD_STATE, HELIUM_QD_STATE, FU_TANK_PRESSURE, OX_TANK_PRESSURE],
            write_authorities=[200],  # Set high authority to prevent interference
        ) as ctrl:
            with client.open_streamer([arm_key, shutdown_key, arm_abort_key, clock_key]) as streamer, \
                client.open_writer(start=sy.TimeStamp.now(), channels=[armed_state_key, status_key, sequence_active_key, log_key, start_clock_key, stop_clock_key], enable_auto_commit=True) as writer:
                
                log_event("Connected to Synnax for trigger monitoring", writer, log_key)
                log_event("Listening for trigger signals", writer, log_key)
                log_event(fu_lower, writer, log_key)
                log_event(fu_upper, writer, log_key)
                log_event(ox_lower, writer, log_key)
                log_event(ox_upper, writer, log_key)

                writer.write({status_key: [1]})

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
                    for v in frame[clock_key]:
                        current_t_time = v 
                    writer.write({armed_state_key: [1 if arm_flag else 0]})

                    if shutdown_flag:
                        writer.write({status_key: [0]})
                        writer.write({armed_state_key: [0]})
                        writer.write({sequence_active_key: [0]})
                        log_event('Shutting down autosequence', writer, log_key)
                        break

                    #check to see if we should be scanning for autosequence timings
                    if current_t_time > main_hold_time and arm_flag == True and arm_abort_flag == True:
                        writer.write({sequence_active_key: [1]})

                        #check current t-time to set what items have already passed in the countdown
                        if current_t_time <= activate_purge_time:
                            purge_activated_flag = False
                        if current_t_time <= pop_vent_qds_time: 
                            vent_qds_popped_flag = False
                        if current_t_time <= pop_helium_qd_time: 
                            hemium_qd_popped_flag = False
                        if current_t_time <= pre_press_time:
                            marottas_regulated_flag = False
                        if current_t_time <= pre_press_time + pre_press_wait_time:
                            prepress_hold_cleared_flag = False
                        if current_t_time <= activate_deluge_time:
                            deluge_activated_flag = False
                        if current_t_time <= fire_igniter_time:
                            igniter_fired_flag = False
                        if current_t_time <= fire_actuator_time:
                            actuator_fired_flag = False

                        #scan for events that need to be activated
                        if current_t_time > activate_purge_time and purge_activated_flag == False:
                            ctrl[PURGE_CMD] = ENERGIZE
                            purge_activated_flag = True
                            log_event("Activating N2-Purge", writer, log_key)

                        if current_t_time > pop_vent_qds_time and vent_qds_popped_flag == False:
                            log_event("Popping Vent QDs", writer, log_key)
                            ctrl[VENT_QD_CMD] = ENERGIZE
                            vent_qds_popped_flag = True
                            cmd.sleep(0.5)
                            ctrl[VENT_QD_CMD] = DEENERGIZE

                        if current_t_time > pop_helium_qd_time and helium_qd_popped_flag == False:
                            log_event("Popping Helium QD", writer, log_key)
                            ctrl[HELIUM_QD_CMD] = ENERGIZE
                            helium_qd_popped_flag = True
                            cmd.sleep(0.5)
                            ctrl[HELIUM_QD_CMD] = DEENERGIZE

                        if current_t_time > pre_press_time and marottas_regulated_flag == False:
                            cmd.send_command("SET_OX_STATE_REGULATE")
                            cmd.send_command("SET_FU_STATE_REGULATE")
                            marottas_regulated_flag = True
                            log_event("Starting Prepress", writer, log_key)


                        
                        
                        if current_t_time > pre_press_time + pre_press_wait_time and prepress_hold_cleared_flag == False:
                            if  ctrl[FU_TANK_PRESSURE] > fu_lower  and  ctrl[FU_TANK_PRESSURE] < fu_upper and  ctrl[OX_TANK_PRESSURE] > ox_lower and ctrl[OX_TANK_PRESSURE] < ox_upper:
                                prepress_hold_cleared_flag = True
                                log_event("Prepress Validation completed", writer, log_key)
                            else:
                                ctrl[T_CLOCK] = 0
                                if ctrl.wait_until(
                                    lambda c: c[FU_TANK_PRESSURE] > fu_lower and c[FU_TANK_PRESSURE] < fu_upper and c[OX_TANK_PRESSURE] > ox_lower and c[OX_TANK_PRESSURE] < ox_upper,
                                    timeout=10 * sy.TimeSpan.SECOND, 
                                ):
                                    log_event("Prepress Validation completed", writer, log_key)
                                    ctrl[T_CLOCK] = 1
                                else:
                                    log_event("Failed to sucessfully prepress", writer, log_key)
                        

                        if current_t_time > activate_deluge_time and deluge_activated_flag == False and prepress_hold_cleared_flag == True:
                            ctrl[DELUGE_CMD] = ENERGIZE
                            deluge_activated_flag = True
                            log_event("Activating Deluge", writer, log_key)

                        if current_t_time > fire_igniter_time and igniter_fired_flag == False and prepress_hold_cleared_flag == True:
                            ctrl[IGNITOR_CMD] = ENERGIZE
                            igniter_fired_flag = True
                            log_event("Firing Ignitor", writer, log_key)

                        if current_t_time > fire_actuator_time and actuator_fired_flag == False and prepress_hold_cleared_flag == True:
                            ctrl[ACTUATOR_CMD] = ENERGIZE
                            actuator_fired_flag = True
                            log_event("Firing Actuator", writer, log_key)

                    else:
                        writer.write({sequence_active_key: [0]})

if __name__ == "__main__":
    wait_for_timestamps()    
