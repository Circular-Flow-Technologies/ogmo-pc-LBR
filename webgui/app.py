from flask import Flask, render_template, request, redirect
from webgui import shared_state
import subprocess

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        # Handle Start
        if "start" in request.form:
            shared_state.is_running = True  # This will signal main to launch threads (already running)
        
        # Handle Stop
        elif "stop" in request.form:
            shared_state.is_running = False
            if shared_state.routines_instance:
                shared_state.routines_instance.shutdown_event.set()
                shared_state.routines_instance.handle_shutdown(None)

        # Handle Calibrate
        elif "calibrate" in request.form and not shared_state.is_running:
            subprocess.Popen(["python3", "../scripts/calibrate_sensor.py"])

        # Handle routine toggles
        new_active = set()
        for key in request.form.keys():
            if key in shared_state.active_routines:
                new_active.add(key)
        shared_state.active_routines = new_active

        return redirect("/")

    # Render page
    sensor_data = {s.name: s.value for s in shared_state.sensors}
    actuator_data = {a.name: a.state for a in shared_state.actuators}

    return render_template(
        "index.html",
        sensors=sensor_data,
        actuators=actuator_data,
        is_running=shared_state.is_running,
        routines=list(shared_state.active_routines),
        active_routines=shared_state.active_routines,
        prompt_messages=shared_state.prompt_messages
    )

# if __name__ == "__main__":
#     app.run(debug=False, port=5050, host="0.0.0.0")
