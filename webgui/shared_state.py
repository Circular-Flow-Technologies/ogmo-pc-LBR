import sys
import threading


# allows flasl GUI app and main from process control to access the same variables

sensors = []
actuators = []

# Optional: dictionary lookup for names
sensor_map = {}
actuator_map = {}

# Flag to check if the system is running
is_running = False

# Selected routines (e.g. toggle boxes)
active_routines = set([
    "data_acquisition",
    "stabilizer_stirrer",
    "evaporator_feed",
    "collector_flush",
    "collector_drain",
    "evaporation",
    "concentrate_discharge",
    "observer",
    "print_to_prompt"
])


# For shutdown from the Flask GUI
routines_instance = None

# Prompt message buffer
prompt_messages = []
prompt_lock = threading.Lock()

class PromptLogger:
    def write(self, message):
        # Avoid blank lines
        if message.strip():
            with prompt_lock:
                prompt_messages.append(message.strip())
                if len(prompt_messages) > 100:
                    prompt_messages.pop(0)

    def flush(self):
        pass  # Required for Python's file-like API



