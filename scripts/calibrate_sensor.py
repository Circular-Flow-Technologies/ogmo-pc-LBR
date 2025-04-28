import time
from pixtendv2l import PiXtendV2L
from src.AtlasI2C_orig import AtlasI2C
from src.utils import load_sensors_from_toml


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

# user input to select sensor for calibration
selected_sensor = str(input("Enter name of sensor to be calibrated (e.g. B_0101): "))

sensor = sensors[sensor_name_list.index(selected_sensor)]

if sensor.type == "PX-AI":
    target_ID = int(input("Enter target ID for analog sensor: '1' for current sensor, '2' for linear level measurement, '3' for quadratic level measurement: "))
    sensor.calibrate(target_ID)
else:
    sensor.calibrate()

# close PiXtend instance
pxt.close()
time.sleep(0.5)
del pxt
pxt = None
