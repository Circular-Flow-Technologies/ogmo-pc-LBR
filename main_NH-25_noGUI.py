import threading
import time

from pixtendv2l import PiXtendV2L
from src.utils import load_sensors_from_toml, load_actuators_from_toml
from src.routines import routines
from webgui import shared_state


def main():

    # create a PiXtend instance
    pxt = PiXtendV2L()

    # create sensor and actuator instances
    folder = "read"
    file_name = "io_list.toml"

    sensors = load_sensors_from_toml(folder, file_name, pxt)
    sensor_name_list = []
    for sensor in sensors:
        sensor_name_list.append(sensor.name)
    print(sensor_name_list)

    actuators = load_actuators_from_toml(folder, file_name, pxt)
    actuator_name_list = []
    for actuator in actuators:
        actuator_name_list.append(actuator.name)

    # pass sensors and actuators instances to shared_state for accessing in flask app (for GUI)
    shared_state.sensors = sensors
    shared_state.actuators = actuators

    shared_state.sensor_map = {s.name: s for s in sensors}
    shared_state.actuator_map = {a.name: a for a in actuators}

    # Initialize routines
    start_time = time.time()
    file_name = "parameters.toml"
    routines_ = routines(start_time, folder, file_name)

    # Create threads for all parallel tasks
    threads = []
    threads.append(threading.Thread(target=routines_.data_acquisition, args=(sensors, actuators,)))
    threads.append(threading.Thread(target=routines_.stabilizer_stirrer, args=(actuators, actuator_name_list,)))
    threads.append(threading.Thread(target=routines_.evaporator_feed, args=(actuators, sensors, actuator_name_list, sensor_name_list,)))
    threads.append(threading.Thread(target=routines_.collector_flush, args=(actuators, sensors, actuator_name_list, sensor_name_list,)))
    threads.append(threading.Thread(target=routines_.collector_drain, args=(actuators, sensors, actuator_name_list, sensor_name_list,)))
    threads.append(threading.Thread(target=routines_.evaporation, args=(actuators, sensors, actuator_name_list, sensor_name_list,)))
    threads.append(threading.Thread(target=routines_.concentrate_discharge, args=(actuators, sensors, actuator_name_list, sensor_name_list,)))
    threads.append(threading.Thread(target=routines_.observer, args=(sensors, sensor_name_list,)))
    threads.append(threading.Thread(target=routines_.print_sensor_values_to_prompt, args=(sensors, sensor_name_list,)))

    # Start threads
    for thread in threads:
        thread.start()

    # Set up signal handler for graceful shutdown on Ctrl+C
    try:
        while not routines_.shutdown_event.is_set():
            time.sleep(1)  # Main thread is waiting, keeping the program running
    except KeyboardInterrupt:
        routines_.handle_shutdown(pxt)
    
    # Wait for threads to finish
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()