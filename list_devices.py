import synnax as sy
import json


def main():
    try:
        # Connect to Synnax
        print("Connecting to Synnax...")
        client = sy.Synnax(
            host="128.46.118.59",
            port=9090,
            username="Bill",
            password="Bill",
        )

        print("\nRetrieving devices...")
        print("\nListing all hardware devices:")
        print("-" * 50)

        # Print information about hardware devices
        print("NI Devices:")
        try:
            # Retrieve devices by specific locations
            device_5 = client.hardware.devices.retrieve(location="Dev5")
            device_6 = client.hardware.devices.retrieve(location="Dev6")

            # Function to print device information
            def print_device_info(device, device_num):
                if not device:
                    print(f"\nDevice {device_num} not found.")
                    return

                print(f"\nDevice {device_num}:")
                print("-" * 50)
                print(f"Device Name: {device.name}")
                print(f"Location: {device.location}")
                print(f"Model: {device.model}")
                print(f"Make: {device.make}")
                print(f"Key: {device.key}")
                print(f"Rack: {device.rack}")

                # Parse and print properties if they exist
                if hasattr(device, "properties"):
                    try:
                        props = json.loads(device.properties)
                        print("\nProperties:")
                        for key, value in props.items():
                            print(f"  {key}: {value}")
                    except json.JSONDecodeError:
                        print(f"Raw properties: {device.properties}")
                print("-" * 50)

            # Print information for both devices
            print_device_info(device_5, "5")
            print_device_info(device_6, "6")

        except Exception as e:
            print(f"Error retrieving devices: {e}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
