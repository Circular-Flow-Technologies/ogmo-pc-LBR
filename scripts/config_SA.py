from pixtendv2l import PiXtendV2L
from src.AtlasI2C_orig import AtlasI2C
from src.utils import load_sensors_from_toml, load_actuators_from_toml


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

