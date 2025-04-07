from AtlasI2C import (AtlasI2C)
import time

def i2c_address_swop(current_address, new_address):
    device = AtlasI2C()
    device.set_i2c_address(current_address)
    
    print(f"Changing address from {current_address} to {new_address}")
    device.write(f"i2c,{new_address}")
    device.write("i2csave")
    time.sleep(1)
    print(f"Address successfully changed and saved to {new_address}")

devices = AtlasI2C()
print("Device list before changes: ", devices.list_i2c_devices())

# Example usage for EZO-pH circuits
#i2c_address_swop(102, 101)  # Change i2C address
#time.sleep(1)
#i2c_address_swop(99, 90)  # Change i2C address
#time.sleep(1)
#i2c_address_swop(100, 92)  # Change i2C address
#time.sleep(1)
i2c_address_swop(111, 110)  # Change i2C address
time.sleep(1)

devices = AtlasI2C()
print("Device list after changes: ", devices.list_i2c_devices())

