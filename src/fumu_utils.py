import tomllib
import time
from src.AtlasI2C_orig import AtlasI2C

class Sensor:
    def __init__(self, sensor_data, pxt):
        """
        Constructor to initialize the sensor object from sensor data.
        """
        self.name       = sensor_data["name"]
        self.descr      = sensor_data["descr"]
        self.type       = sensor_data["type"]
        self.com_prot   = sensor_data["com_prot"]
        self.address    = sensor_data["address"]
        self.value      = 0.0 
        self.gain       = float(sensor_data["gain"])  # only needed for sensors on PiXtend analog input interface (set during calibration)
        self.offset     = float(sensor_data["offset"]) # only needed for sensors on PiXtend analog input interface (set during calibration)
        self.connected  = False  # Default connection status
        self.configured = False  # Default connection status
        
        # check whether sensor is calibrated with knonw data
        if sensor_data["calibrated"] == "yes" or sensor_data["calibrated"] == "Yes":
            self.calibrated = True  # Default calibration status
        else:
            self.calibrated = False

        # PiXtend instance (same for all sensors and actuators)
        self.pxt = pxt

        # Perform sensor type-specific configuration
        self.configure_sensor()


    def configure_sensor(self):
        """
        Perform sensor type-specific configuration.
        """

        # First check whether the sensor is connected
        if "EZO" in self.type:
            devices = AtlasI2C()
            device_list = devices.list_i2c_devices()
            if int(self.address) in device_list:
                self.connected = True
            else:
                print(f"The address '{self.address}' is not listed in the I2C device list.")
        else:
            self.connected = True # all non-EZO type sensors get a pass for this check

        # configure all connected sensors
        if self.connected:
            if self.type == "EZO-RTD":
                print(f"Configuring EZO-RTD'{self.name}'.")
                device = AtlasI2C(int(self.address))
                res = device.query('S,c') # set temperature scale to Celcius
                self.configured = True

            elif self.type == "EZO-pH":
                print(f"Configuring EZO-pH '{self.name}'.")
                device = AtlasI2C(int(self.address))
                res = device.query('T,20') # temperature compensation for 20°C
                self.configured = True

            elif self.type == "EZO-EC":
                print(f"Configuring EZO-EC '{self.name}'.")
                device = AtlasI2C(int(self.address))
                res = device.query(',K,1.0') # set probe type
                res = device.query('O,EC,1')  # set EC as output parameter
                res = device.query('O,TDS,0') # disable TDS as output parameter
                res = device.query('O,S,0')   # disable S as output parameter
                res = device.query('O,SG,0')  # disable SG as output parameter
                self.configured = True

            elif "EZO-HUM" in  self.type:
                print(f"Configuring EZO-HUM '{self.name}'.")
                device = AtlasI2C(int(self.address))
                res = device.query('O,HUM,1')  # set rel. humidity as output parameter
                res = device.query('O,T,1')    # set temperature as output parameter
                res = device.query('O,Dew,0')   # disable S as output parameter
                self.configured = True

            elif "PX" in self.type:
                print(f"Configuring analog / digital input '{self.name}' on PiXtend.")
                # Check if SPI communication is running and the received data is correct
                if self.pxt.crc_header_in_error is False and self.pxt.crc_data_in_error is False:
                    self.configured = True
                else:
                    print(f"SPI communication does not appear to be running. Sensor on PiXtend not conifigured.")

            else:
                print(f"Unknown sensor type '{self.type}'. No specific configuration applied.")

        else:
            print(f"Sensor '{self.name}' could not be configured, because it appears not to be connected")



    def calibrate(self):
        """
        Perform sensor type-dependent calibration routine.
        """
        if self.type == "EZO-RTD":
            print(f"Calibrating temperature sensor type EZO-RTD, name '{self.name}'. ---1-point calibration---")
            device = AtlasI2C(int(self.address))
            uinp = input("Put the temperature probe in a reference medium and enter the reference temperature: ")
            calibration_command = "Cal,"+uinp
            device.query(calibration_command)
            uinp = input("1-point calibration successfully terminated.")
            self.calibrated = True
            
            return

        elif self.type == "EZO-pH":
            print(f"Calibrating pH sensor type EZO-pH, name '{self.name}'. ---3-point calibration---")
            device = AtlasI2C(int(self.address))

            # calibration at medium pH
            uinp = input("Put the pH probe in the medium pH reference medium and enter the corresponding pH value (e.g 7.00): ")
            calibration_command = "Cal,mid,"+uinp
            device.query(calibration_command)

            # calibration at low pH
            uinp = input("Put the pH probe in the low pH reference medium and enter the corresponding pH value (e.g. 4.00): ")
            calibration_command = "Cal,low,"+uinp
            device.query(calibration_command)

            # calibration at high pH
            uinp = input("Put the pH probe in the high pH reference medium and enter the corresponding pH value (e.g. 9.00): ")
            calibration_command = "Cal,high,"+uinp
            device.query(calibration_command)

            uinp = input("3-point calibration successfully terminated.")
            self.calibrated = True

            return

        elif self.type == "EZO-EC":
            print(f"Calibrating EC sensor type EZO-EC, name '{self.name}'. ---2-point calibration---")
            device = AtlasI2C(int(self.address))

            # calibration at medium pH
            uinp = input("Dry calibration: Is the probe tip dry / not immersed in a liquid? (enter y/n): ")
            if uinp == "y" or uinp == "Y" or uinp == "yes" or uinp == "Yes":
                calibration_command = "Cal,dry,"
                device.query(calibration_command)

                # calibration at low pH
                uinp = input("Put the EC probe in the low EC reference medium and enter the corresponding EC value (e.g. 12880): ")
                calibration_command = "Cal,low,"+uinp
                device.query(calibration_command)

                # calibration at high pH
                uinp = input("Put the EC probe in the high EC reference medium and enter the corresponding EC value (e.g. 150000): ")
                calibration_command = "Cal,high,"+uinp
                device.query(calibration_command)

                uinp = input("2-point calibration successfully terminated.")
                self.calibrated = True

                return

            else:
                print(f"EC probe requires to be dry in first calibation step. Start again.")

        elif self.type == "PX-AI":
            if self.calibrated:
                uinp = input("Sensor is already calibrated. Do you want to overwrite the current calibration? (enter y/n): ")
                if uinp == "y" or uinp == "Y" or uinp == "yes" or uinp == "Yes":
                    self.gain = 1
                    self.offset = 0
                else:
                    return
                
            print(f"Calibrating ultrasonic sensor for tank volume measurement (PiXtend analog input inteface), name '{self.name}'.")

            V_low  = float(input("Fill in the initial amount of water such that the senor is 150 - 300 mm above liquid surface, and enter the volume of the inital amount of Water (in L): "))
            U_low  = self.read_value()
            dV     = float(input("Add an additional amount of water such that the liquid surface rises to a level 50 - 150 mm below the sensor, and enter the volume of the ADDED amount of water (in L): "))
            U_high = self.read_value()

            self.gain   = -(dV)/(U_low - U_high)
            self.offset = V_low + dV - self.gain*U_high

            self.calibrated = True
            print(f"Calibration successfully terminated.")
            print(f"Enter 'gain' = {self.gain} and 'offset' {self.offset} for Sensor '{self.name}' in 'io_list.toml'.")

            return 
        
        else:
            print(f"No calibration routine available for sensor type '{self.type}'.")
            self.calibrated = False

            return


    def read_value(self):
        """
        Acquire and return the measured value.
        """
        if self.configured:

            if "EZO" in self.type:
                device = AtlasI2C(int(self.address))

                if self.type == "EZO-HUM-RH":
                    val = float(device.query('R').split(':')[1].split('\x00')[0].split(',')[0])
                    self.value = val

                elif self.type == "EZO-HUM-T":
                    val = float(device.query('R').split(':')[1].split('\x00')[0].split(',')[1])
                    self.value = val

                else:
                    val = float(device.query('R').split(':')[1].split('\x00')[0])
                    self.value = val
            elif "PX" in self.type:
                if self.address == "analog_in0":
                    self.value = self.pxt.analog_in0*self.gain + self.offset

                elif self.address == "analog_in1":
                    self.value = self.pxt.analog_in1*self.gain + self.offset

                elif self.address == "digital_in0":
                    self.value = self.pxt.digital_in0

                elif self.address == "digital_in1":
                    self.value = self.pxt.digital_in1

                elif self.address == "digital_in2":
                    self.value = self.pxt.digital_in2

                elif self.address == "digital_in3":
                    self.value = self.pxt.digital_in3

                else:
                    print(f"Sensor address '{self.address}' is either unknown or has not yet been implemented.")

            else:
                print(f"Unknown sensor type '{self.name}'. Cannot read measurement value.")            

            return self.value
        
        else:
            print(f"Sensor '{self.name}' is not configured.")
            return None
        


class Actuator:
    def __init__(self, actuator_data, pxt):
        """
        Constructor to initialize the actuator object from actuator data.
        """
        self.name = actuator_data["name"]
        self.descr = actuator_data["descr"]
        self.type = actuator_data["type"]
        self.address = actuator_data["address"]
        self.com_prot = actuator_data["com_prot"]
        self.configured = False  # Default status
        self.state = False  # Default state

        # PiXtend instance (same for all sensors and actuators)
        self.pxt = pxt

        # configure actuators
        self.configure()

    
    def configure(self):
    
        if "PX" in self.type:
            print(f"Configuring analog / digital output '{self.name}' on PiXtend.")
            # Check if SPI communication is running and the received data is correct
            if self.pxt.crc_header_in_error is False and self.pxt.crc_data_in_error is False:
                self.configured = True
            else:
                print(f"SPI communication does not appear to be running. Actuator on PiXtend not conifigured.")

        else:
            print(f"Unknown actuator type '{self.type}'. No specific configuration applied.")


    def set_state(self, state):
        """
        Activate or disactivate actuator
        """
        if self.configured:

            if self.address == "relay0":
                if state == True:
                    self.pxt.relay0 = self.pxt.ON
                else:
                    self.pxt.relay0 = self.pxt.OFF

            elif self.address == "relay1":
                if state == True:
                    self.pxt.relay1 = self.pxt.ON
                else:
                    self.pxt.relay1 = self.pxt.OFF

            elif self.address == "relay2":
                if state == True:
                    self.pxt.relay2 = self.pxt.ON
                else:
                    self.pxt.relay2 = self.pxt.OFF

            elif self.address == "relay3":
                if state == True:
                    self.pxt.relay3 = self.pxt.ON
                else:
                    self.pxt.relay3 = self.pxt.OFF

            elif self.address == "digital_out0":
                if state == True:
                    self.pxt.digital_out0 = self.pxt.ON
                else:
                    self.pxt.digital_out0 = self.pxt.OFF

            elif self.address == "digital_out1":
                if state == True:
                    self.pxt.digital_out1 = self.pxt.ON
                else:
                    self.pxt.digital_out1 = self.pxt.OFF

            elif self.address == "digital_out2":
                if state == True:
                    self.pxt.digital_out2 = self.pxt.ON
                else:
                    self.pxt.digital_out2 = self.pxt.OFF

            elif self.address == "digital_out3":
                if state == True:
                    self.pxt.digital_out3 = self.pxt.ON
                else:
                    self.pxt.digital_out3 = self.pxt.OFF
            else:
                print(f"Actuator address '{self.address}' is unknown.")
        else:
            print(f"Actuator '{self.name}' is not configured. State cannot be set.")

    


def load_sensors_from_toml(file_path, pxt):
    """
    Load sensor data from a TOML file and initialize Sensor objects.
    """
    with open(file_path, "rb") as f:
        io_list = tomllib.load(f)
    
    sensors = []
    for sensor_data in io_list["sensor"]:
        sensor = Sensor(sensor_data, pxt)
        sensors.append(sensor)
    
    return sensors

def load_actuators_from_toml(file_path, pxt):
    """
    Load actuator data from a TOML file and initialize Actuator objects.
    """
    with open(file_path, "rb") as f:
        io_list = tomllib.load(f)
    
    actuators = []
    for actuator_data in io_list["actuator"]:
        actuator = Actuator(actuator_data, pxt)
        actuators.append(actuator)
    
    return actuators
