from flask import Flask, jsonify, render_template, request, redirect, url_for
from shared_state import sensors, actuators
import subprocess
import threading
import os
import signal

app = Flask(__name__)

# Path configuration
MAIN_SCRIPT = os.path.abspath("../main.py")
CALIBRATE_SCRIPT = os.path.abspath("../scripts/calibrate_sensor.py")

# Global state
process_thread = None
process_obj = None
is_running = False
prompt_messages = []

# Example routine names (update as needed)
routines = [
    "data_acquisition", "stabilizer_stirrer", "evaporator_feed",
    "collector_flush", "collector_drain", "evaporation",
    "concentrate_discharge", "observer", "print_to_prompt"
]
active_routines = set(routines)  # Initially all active


def run_main():
    global process_obj, is_running
    is_running = True
    process_obj = subprocess.Popen(["python3", MAIN_SCRIPT], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process_obj.stdout:
        prompt_messages.append(line.strip())
        if len(prompt_messages) > 50:
            prompt_messages.pop(0)


@app.route("/api/status")
def get_status():
    sensor_data = {s.name: s.value for s in sensors}
    actuator_data = {a.name: a.state for a in actuators}
    return jsonify({"sensors": sensor_data, "actuators": actuator_data})


@app.route("/", methods=["GET", "POST"])
def index():
    global is_running

    if request.method == "POST":
        if "start" in request.form and not is_running:
            # Start control process in a thread
            global process_thread
            process_thread = threading.Thread(target=run_main)
            process_thread.start()
        elif "stop" in request.form and is_running:
            # Graceful shutdown (sends SIGINT like Ctrl+C)
            if process_obj:
                process_obj.send_signal(signal.SIGINT)
                process_thread.join()
                is_running = False
        elif "calibrate" in request.form and not is_running:
            subprocess.run(["python3", CALIBRATE_SCRIPT])
        else:
            # Handle routine toggle
            for routine in routines:
                if routine in request.form:
                    active_routines.add(routine)
                else:
                    active_routines.discard(routine)

    # Dummy sensor/actuator state (replace with real reads)
    sensors = {f"Sensor {i}": f"{round(i*1.23, 2)}" for i in range(5)}
    actuators = {f"Actuator {i}": "ON" if i % 2 == 0 else "OFF" for i in range(3)}

    return render_template("index.html",
                           is_running=is_running,
                           sensors=sensors,
                           actuators=actuators,
                           routines=routines,
                           active_routines=active_routines,
                           prompt_messages=prompt_messages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
