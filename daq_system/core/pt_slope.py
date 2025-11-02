import synnax as sy
from synnax import DataType
import os

# --- 1. CONFIGURATION (User-Provided) ---
HOST = "10.165.89.106" 
PORT = 2701
USERNAME = "Bill" 
PASSWORD = "Bill" 

# Define the base channel whose slope we want to calculate
BASE_PRESSURE_CHANNEL_NAME = "PT-FU-04" 

# --- 2. LUA EXPRESSION FOR 5-SECOND SLOPE ---
# Note: The Lua expression *must* still use the channel name (e.g., 'PT-FU-04')
# because that's how Synnax's Lua environment references channels.

LUA_SLOPE_EXPRESSION = f"""
-- Time window is 5 seconds in nanoseconds (5 * 10^9)
local window_size_ns = 5000000000 
local pressure_channel = channels["{BASE_PRESSURE_CHANNEL_NAME}"]

-- Get all samples in the last 5 seconds
local pressure_window = pressure_channel:window(
    window_size_ns, 
    time - window_size_ns, 
    time
)

local oldest_sample = pressure_window:first()
local newest_sample = pressure_window:last()

if oldest_sample == nil or newest_sample == nil then
    return nil
end

local delta_pressure = newest_sample.value - oldest_sample.value

local delta_time_ns = newest_sample.time - oldest_sample.time
local delta_time_s = delta_time_ns / 1000000000 

if delta_time_s == 0 then
    return nil
end

local slope = delta_pressure / delta_time_s

return slope
"""

# --- 3. CHANNEL CREATION SCRIPT (FIXED FOR INTEGER KEY REQUIREMENT) ---

def create_slope_calculated_channel():
    """
    Connects to Synnax, retrieves the key for the base channel, and creates 
    the 5-second slope calculated channel using the key.
    """
    try:
        # Initialize the Synnax client
        client = sy.Synnax(
            host=HOST,
            port=PORT,
            username=USERNAME,
            password=PASSWORD,
        )

        # 🎯 FIX STEP 1: RETRIEVE THE CHANNEL KEY (ID)
        print(f"Retrieving key for base channel: {BASE_PRESSURE_CHANNEL_NAME}...")
        
        # Use .retrieve() to get the existing Channel object
        base_channel = client.channels.retrieve(BASE_PRESSURE_CHANNEL_NAME)
        
        # Extract the integer key
        base_channel_key = base_channel.key 
        print(f"Found channel key: {base_channel_key}")


        # 🎯 FIX STEP 2: USE THE INTEGER KEY IN THE 'requires' LIST
        channel_data = {
            "name": f"{BASE_PRESSURE_CHANNEL_NAME}_SLOPE_5S",
            "data_type": DataType.FLOAT64,
            "expression": LUA_SLOPE_EXPRESSION,
            # PASS THE INTEGER KEY, NOT THE STRING NAME, to satisfy the ValidationError
            "requires": [base_channel_key], 
        }

        # Initialize a basic Channel object using the data dictionary.
        calculated_channel = sy.Channel(**channel_data)

        # Create the channel on the Synnax cluster
        created_channel = client.channels.create(calculated_channel)
        
        print("\n✅ Successfully created Calculated Channel:")
        print(f"   Name: {created_channel.name}")
        print(f"   Key: {created_channel.key}")
        print(f"   Status: Active and calculating slope for {BASE_PRESSURE_CHANNEL_NAME}.")

    # Catch specific exceptions for better debugging
    except sy.exceptions.SynnaxError as e:
        print(f"❌ Synnax API Error: {e}")
    except Exception as e:
        # This will now catch the ValidationError from the failed 'requires' check, 
        # or any other connection/runtime errors.
        print(f"❌ An error occurred during channel creation. Check Synnax server status or permissions.")
        print(f"   Error Details: {type(e).__name__}: {e}")

if __name__ == '__main__':
    create_slope_calculated_channel()