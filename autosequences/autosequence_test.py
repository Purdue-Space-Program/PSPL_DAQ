import time
import synnax as sy

client = sy.Synnax(
    host = "128.46.118.59",
    port = 9090,
    username = "Bill",
    password = "Bill",
)

with client.control.acquire(
    name="Test",
    read=["REED-N2-02", "SV-N2-02_state"],
    write=["SV-N2-02_cmd"],
    write_authorities=[sy.Authority.ABSOLUTE]
) as controller:
    for i in range(10):
        controller["SV-N2-02_cmd"] = 1
        time.sleep(0.3)
        controller["SV-N2-02_cmd"] = 0
        time.sleep(0.3)
