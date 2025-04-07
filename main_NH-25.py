import threading
import datetime
import numpy as np
import sys
import time
import os
import tomllib

from pixtendv2s import PiXtendV2S
from src.AtlasI2C_orig import AtlasI2C
from src.fumu_utils import load_sensors_from_toml, load_actuators_from_toml

# Global runtime tracking
start_time = time.time()
shutdown_event = threading.Event()  # Used to stop threads gracefully
sensor_data = []

# initial wait time [s] (to avoid missing first cycles when intervall is rel. long. has to be longer than longest delay)
initial_wait_time = 10

# parameter file open and read in async routines for dynamic updating
parameter_file_path = "src/fumu_DS_parameters.toml"

# Function to load tau values from the TOML file
def load_parameter_list():
    with open(parameter_file_path, "rb") as f:
        parameter_list = tomllib.load(f)
    return parameter_list

# Task 1: Data acquisition
def data_acquisition(sensors):
    global sensor_data
    while not shutdown_event.is_set():
        # Generate the current timestamp and runtime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        global_runtime = time.time() - start_time
        row = [timestamp, global_runtime]
        
        # Read sensor values
        for sensor in sensors:
            value = sensor.read_value()
            row.append(value)
        
        # Append the new row to sensor data
        sensor_data.append(row)
        time.sleep(1)  # Simulate reading every 1 second

    # Get the current date for the file name
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    file_name = f"data/{current_date}_FuMu-DS_sensor_data.npy"

    # Check if the file exists
    if os.path.exists(file_name):
        # If the file exists, load existing data
        existing_data = np.load(file_name, allow_pickle=True).tolist()
        # Merge new data with existing data
        existing_data.extend(sensor_data)
        # Save the merged data back to the file
        np.save(file_name, np.array(existing_data))
    else:
        # If the file doesn't exist, save the new data to the file
        np.save(file_name, np.array(sensor_data))
    
    print(f"Data saved to {file_name}")

# Task 2: stabilizer feed control
def stabi_feed_pump_control(actuators, actuator_name_list):

    # select actuators
    act_M1101 = actuators[actuator_name_list.index("M1101")]
    
    while not shutdown_event.is_set():
        pl_DS = load_parameter_list()
        tau_M1101_interval = float(pl_DS.get("tau_M1101_interval"))
        tau_M1101_runtime  = float(pl_DS.get("tau_M1101_runtime"))
        tau_M1101_delay    = float(pl_DS.get("tau_M1101_delay"))

        current_runtime = time.time() - (start_time + initial_wait_time)
        if tau_M1101_interval-tau_M1101_runtime <=1:
            print(f"WARNING: time difference between interval and runtime should be longer than 1 sec.")

        if int(current_runtime - tau_M1101_delay) % int(tau_M1101_interval) == 0:
            # Turn actuator on
            print(f"[Pump Control] Activating recirculation pump and valve at runtime: {current_runtime:.2f}s")
            act_M1101.set_state(True)

            time.sleep(tau_M1101_runtime)  # Wait for the specified runtime
            
            # Turn actuator off
            print(f"[Pump Control] Deactivating recirculation pump and valve at runtime: {current_runtime + tau_M1101_runtime:.2f}s")
            act_M1101.set_state(False)

        time.sleep(1)


# Task 3: stirrer control
def stirrer_control(actuators, actuator_name_list):

    # select actuators
    act_M1201 = actuators[actuator_name_list.index("M1201")]
    
    while not shutdown_event.is_set():
        pl_DS = load_parameter_list()
        tau_M1201_interval = float(pl_DS.get("tau_M1201_interval"))
        tau_M1201_runtime  = float(pl_DS.get("tau_M1201_runtime"))
        tau_M1201_delay  = float(pl_DS.get("tau_M1201_delay"))

        current_runtime = time.time() - (start_time + initial_wait_time)
        if tau_M1201_interval-tau_M1201_runtime <=1:
            print(f"WARNING: time difference between interval and runtime should be longer than 1 sec.")

        if int(current_runtime - tau_M1201_delay) % int(tau_M1201_interval) == 0:
            # Turn actuator on
            print(f"[Pump Control] Activating recirculation pump and valve at runtime: {current_runtime:.2f}s")
            act_M1201.set_state(True)

            time.sleep(tau_M1201_runtime)  # Wait for the specified runtime
            
            # Turn actuator off
            print(f"[Pump Control] Deactivating recirculation pump and valve at runtime: {current_runtime + tau_M1201_runtime:.2f}s")
            act_M1201.set_state(False)

        time.sleep(1)


# Task 4: evaporator feed control
def evi_feed_pump_control(actuators, actuator_name_list):

    # select actuators
    act_M1202 = actuators[actuator_name_list.index("M1202")]
    
    while not shutdown_event.is_set():
        pl_FD = load_parameter_list()
        tau_M1202_interval = float(pl_FD.get("tau_M1202_interval"))
        tau_M1202_delay    = float(pl_FD.get("tau_M1202_delay"))
        tau_M1202_runtime  = float(pl_FD.get("tau_M1202_runtime"))

        current_runtime = time.time() - (start_time + initial_wait_time)
        if tau_M1202_interval-tau_M1202_runtime <=1:
            print(f"WARNING: time difference between interval and runtime should be longer than 1 sec.")

        if int(current_runtime - tau_M1202_delay) % int(tau_M1202_interval) == 0:
            # Turn actuator on
            print(f"[Pump Control] Activating feed pump and valve at runtime: {current_runtime:.2f}s")
            act_M1202.set_state(True)

            time.sleep(tau_M1202_runtime)
            # Turn actuator off
            print(f"[Pump Control] Deactivating feed pump and valve at runtime: {current_runtime + tau_M1202_runtime:.2f}s")
            act_M1202.set_state(False)

        time.sleep(1)

# Clean up after keyboard interrupt
def handle_shutdown(pxt):
    print("\nShutdown signal received. Cleaning up...")
    shutdown_event.set()

    # clean-up and close PiXtend instance
    pxt.digital_out0 = pxt.OFF
    pxt.digital_out1 = pxt.OFF
    pxt.digital_out2 = pxt.OFF
    pxt.digital_out3 = pxt.OFF
    pxt.relay0 = pxt.OFF
    pxt.relay1 = pxt.OFF
    pxt.relay2 = pxt.OFF
    pxt.relay3 = pxt.OFF
    time.sleep(0.25)
    pxt.close()
    time.sleep(0.25)
    del pxt
    pxt = None
    print("\nPiXtend instance closed and deleted")


def main():

    # create a PiXtend instance
    pxt = PiXtendV2S()

    # sensor and actuator instances
    io_file = "src/io_list.toml"
    sensors = load_sensors_from_toml(io_file, pxt)
    sensor_name_list = []
    for sensor in sensors:
        sensor_name_list.append(sensor.name)

    io_file = "src/io_list.toml"
    actuators = load_actuators_from_toml(io_file, pxt)
    actuator_name_list = []
    for actuator in actuators:
        actuator_name_list.append(actuator.name)

    # Create threads for both tasks
    data_thread = threading.Thread(target=data_acquisition, args=(sensors,))
    stirrer_thread = threading.Thread(target=stirrer_control, args=(actuators, actuator_name_list,))
    evi_feed_pump_thread = threading.Thread(target=evi_feed_pump_control, args=(actuators, actuator_name_list,))
    stabi_feed_pump_thread = threading.Thread(target=stabi_feed_pump_control, args=(actuators, actuator_name_list,))


    # Start both threads
    data_thread.start()
    stirrer_thread.start()
    evi_feed_pump_thread.start()
    stabi_feed_pump_thread.start()

    # Set up signal handler for graceful shutdown on Ctrl+C
    try:
        while not shutdown_event.is_set():
            time.sleep(1)  # Main thread is waiting, keeping the program running
    except KeyboardInterrupt:
        handle_shutdown(pxt)
    
    # Wait for threads to finish
    data_thread.join()
    stirrer_thread.join()
    evi_feed_pump_thread.join()
    stabi_feed_pump_thread.join()

if __name__ == "__main__":
    main()