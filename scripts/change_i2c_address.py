from src.AtlasI2C_orig import AtlasI2C
import time

def i2c_address_swop(current_address, new_address):
    device = AtlasI2C(current_address)
    
    print(f"Changing address from '{current_address}' to '{new_address}' ")
    device.write(f"I2C,{new_address}")
    time.sleep(2)
    devices = AtlasI2C()
    print(f"The device list now reads...")
    print(devices.list_i2c_devices())

# main
devices = AtlasI2C()
print("Device list before changes: ", devices.list_i2c_devices())

# get user input for address change
current_address = int(input("Enter the address to be changed: "))
new_address     = int(input("Enter the new address (1-127, be sure not to choose an address which is already in use): "))

i2c_address_swop(current_address, new_address)  # Change i2C address
time.sleep(1)


