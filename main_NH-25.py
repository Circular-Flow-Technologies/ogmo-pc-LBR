import threading
import time
import sys
from pixtendv2l import PiXtendV2L
from webgui import shared_state

# Redirect stdout globally
# Warning: This is global. All print() output from any thread is redirected.
# sys.stdout = shared_state.PromptLogger()
# sys.stderr = shared_state.PromptLogger()

from src.utils import load_sensors_from_toml, load_actuators_from_toml
from src.routines import routines

def start_flask():
    try:
        print("[Flask] Starting Flask server...")
        from webgui.app import app
        app.run(debug=False, port=5050, host="0.0.0.0")
    except Exception as e:
        print(f"[Flask] Failed to start Flask: {e}")

def main():
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    time.sleep(2)  # Give Flask time to initialize
 
    # Initialize PiXtend and IO
    pxt = PiXtendV2L()
    folder = "read"
    file_name = "io_list.toml"
    sensors = load_sensors_from_toml(folder, file_name, pxt)
    actuators = load_actuators_from_toml(folder, file_name, pxt)

    sensor_name_list = [s.name for s in sensors]
    actuator_name_list = [a.name for a in actuators]

    # Share state
    shared_state.sensors = sensors
    shared_state.actuators = actuators
    shared_state.sensor_map = {s.name: s for s in sensors}
    shared_state.actuator_map = {a.name: a for a in actuators}

    while True:
        if shared_state.is_running:
            start_time = time.time()
            routines_ = routines(start_time, "parameters.toml", "log_file.csv")
            shared_state.routines_instance = routines_

            threads = []

            def maybe_add(name, target, args):
                if name in shared_state.active_routines:
                    threads.append(threading.Thread(target=target, args=args))

            maybe_add("data_acquisition", routines_.data_acquisition, (sensors, actuators))
            maybe_add("stabilizer_stirrer", routines_.stabilizer_stirrer, (actuators, sensors, actuator_name_list, sensor_name_list))
            maybe_add("evaporator_feed", routines_.evaporator_feed, (actuators, sensors, actuator_name_list, sensor_name_list))
            maybe_add("collector_flush", routines_.collector_flush, (actuators, sensors, actuator_name_list, sensor_name_list))
            maybe_add("collector_drain", routines_.collector_drain, (actuators, sensors, actuator_name_list, sensor_name_list))
            maybe_add("evaporation", routines_.evaporation, (actuators, sensors, actuator_name_list, sensor_name_list))
            maybe_add("concentrate_discharge", routines_.concentrate_discharge, (actuators, sensors, actuator_name_list, sensor_name_list))
            maybe_add("observer", routines_.observer, (sensors, sensor_name_list))
            maybe_add("print_sensor_values_to_prompt", routines_.print_sensor_values_to_prompt, (sensors, sensor_name_list))
            maybe_add("print_sensor_values_to_prompt", routines_.CaOH2_refill, args=(actuators, actuator_name_list))

            for t in threads:
                t.start()

            try:
                while not routines_.shutdown_event.is_set():
                    time.sleep(1)
            except KeyboardInterrupt:
                routines_.handle_shutdown(pxt)

            for t in threads:
                t.join()
            shared_state.is_running = False

        else:
            time.sleep(1)  # Polling for Start command

if __name__ == "__main__":
    main()
