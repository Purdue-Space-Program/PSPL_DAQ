import synnax as sy # type: ignore
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'PSPL_CMS_AVIONICS_COTS_FSW', 'tools')))
import command as cmd  # type: ignore

ENERGIZE = 0
DEENERGIZE = 1


def run_event(ctrl, command, state):
    ctrl.set_authority(200)
    ctrl[command] = state
    ctrl.set_authority(10)

def wait_for_timestamps():
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

    # Define the control channel names
   

    HS_CAMERA_STATE = "HS_CAMERA_state"
    HS_CAMERA_CMD = "HS_CAMERA_cmd"

    #input and output channels for control sequence
    input_authorities = [
        HS_CAMERA_STATE,
    ]

    output_authorities = [ 
        HS_CAMERA_CMD,
    ]

    with client.control.acquire(
            name="Automatic Control System",
            write= output_authorities,
            read= input_authorities,
            write_authorities=[10],  # Set low authority to prevent interference
        ) as ctrl:
           
            ctrl.sleep(1)
            run_event(ctrl, HS_CAMERA_CMD, ENERGIZE)
            ctrl.sleep(.010)
            run_event(ctrl, HS_CAMERA_CMD, DEENERGIZE)

if __name__ == "__main__":
    wait_for_timestamps()    