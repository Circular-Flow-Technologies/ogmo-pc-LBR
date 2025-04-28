import threading
import datetime
import time

from pixtendv2l import PiXtendV2s
from src.fumu_utils import load_sensors_from_toml

# Global runtime tracking
start_time = time.time()
shutdown_event = threading.Event()  # Used to stop threads gracefully


# Data acquisitioncd
def sensor_data_print(sensor):
    while not shutdown_event.is_set():
        # Generate the current timestamp and runtime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        global_runtime = time.time() - start_time
        row = [timestamp, global_runtime]
        
        # Read sensor values
        value = sensor.read_value()
        row.append(value)
        
        # print sensor data
        print(row)
        time.sleep(1)  # Simulate reading every 1 second


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

    sensor = sensors[sensor_name_list.index("B0104")]

    # Calibrate sensor
    #sensor.calibrate()

    # Create thread for sensor data print
    print_thread = threading.Thread(target=sensor_data_print, args=(sensor,))

    # Start both threads
    print_thread.start()

    # Set up signal handler for graceful shutdown on Ctrl+C
    try:
        while not shutdown_event.is_set():
            time.sleep(1)  # Main thread is waiting, keeping the program running
    except KeyboardInterrupt:
        handle_shutdown(pxt)
    

if __name__ == "__main__":
    main()