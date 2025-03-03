import synnax as sy
import time
from socket import socket, AF_INET, SOCK_STREAM
from struct import pack


def send_start_command():
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect(("192.168.1.103", 1234))

        START_COMMAND = 14
        packet = pack("B", START_COMMAND)
        s.send(packet)
        val = s.recv(1)
        print(f"Sent start command, received: {val}")


# Main autosequence
client = sy.Synnax(
    host="128.46.118.59",
    port=9090,
    username="Bill",
    password="Bill",
)

with client.control.acquire(
    name="TC Auto Sequence Test",
    read=["TC", "ACTUATOR_state", "IGNITER_state"],
    write=["ACTUATOR_cmd", "IGNITER_cmd"],
) as controller:
    start = sy.TimeStamp.now()

    # Send the start command at the beginning of the sequence
    send_start_command()

    controller["IGNITER_cmd"] = True  # Turn on the igniter
    # controller.wait_until(lambda c: c["TC"] > 100) # Wait until the TC reads above 100
    controller["ACTUATOR_cmd"] = True
    time.sleep(5)

    # Turn off the igniter and actuator
    controller["ACTUATOR_cmd"] = False
    controller["IGNITER_cmd"] = False

    end = sy.TimeStamp.now()
    client.ranges.create(
        name=f"TC Auto Sequence Test {end}",
        time_range=sy.TimeRange(start=start, end=end),
    )
