import time
import synnax as sy

client = sy.Synnax(
    host="128.46.118.59",
    port=9090,
    username="Bill",
    password="Bill",
)


with client.control.acquire(
    name="Test",
    read=["REED-N2-02", "SV-N2-02_state"],
    write=["SV-N2-02_cmd"],
) as controller:

    start = sy.TimeStamp.now()

    for i in range(10):
        controller["SV-N2-02_cmd"] = True
        time.sleep(0.3)
        controller["SV-N2-02_cmd"] = False
        time.sleep(0.3)

    end = sy.TimeStamp.now()

    client.ranges.create(
        name=f"Test {end}",
        time_range=sy.TimeRange(start=start, end=end),
    )
