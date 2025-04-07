import time
import numpy as np
from atlas_i2c import AtlasI2C
from datetime import datetime

# Assign I2C addresses for each sensor
SENSOR_ADDRESSES = {
    "ph_1": 0x62,
    "ph_2": 0x63,
    "ec_1": 0x64,
    "ec_2": 0x65,
    "rtd_1": 0x66,
    "rtd_2": 0x67,
}

# Initialize sensors
sensors = {name: AtlasI2C(address) for name, address in SENSOR_ADDRESSES.items()}

# Data storage
data = []

print("Starting data acquisition. Press Ctrl+C to stop.")

try:
    while True:
        # Capture timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Read sensor data
        readings = []
        for name, sensor in sensors.items():
            try:
                value = float(sensor.query("R"))  # Send "R" command to read sensor value
                readings.append(value)
            except Exception as e:
                print(f"Error reading {name}: {e}")
                readings.append(np.nan)  # Append NaN for missing data

        # Combine timestamp and readings
        row = [timestamp] + readings
        print(row)

        # Append to data list
        data.append(row)

        # Wait for 1 second
        time.sleep(1)

except KeyboardInterrupt:
    print("\nMeasurement stopped by user.")

# Save data to a .npy file
print("Saving data to sensor_data.npy...")
header = ["Timestamp"] + list(SENSOR_ADDRESSES.keys())
np.save("sensor_data", np.array(data, dtype=object))

print("Data saved successfully.")
