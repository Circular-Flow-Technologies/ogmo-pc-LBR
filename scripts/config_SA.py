import asyncio
import datetime
import numpy as np
import signal
import sys
import time
import tomllib

from pixtendv2s import PiXtendV2S
from src.AtlasI2C_orig import AtlasI2C
from src.fumu_utils import load_sensors_from_toml, load_actuators_from_toml




# --- Global Variables ---
start_time = time.time()    # Global runtime variable

# parameter file open and read in async routines for dynamic updating
parameter_file_path = "src/fumu_parameters.toml"

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
