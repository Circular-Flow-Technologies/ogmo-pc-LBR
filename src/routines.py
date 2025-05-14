import threading
import datetime
import time
import os
import csv
import tomllib

from src.utils import get_file_path
 

class routines:
    def __init__(self, start_time, folder, parameter_file_name):

        """
        Constructor to initialize the sensor object from sensor data.
        """
        self.start_time = start_time

        # access parameter file
        self.parameter_file_path = get_file_path(folder, parameter_file_name)
        pl = self.load_parameter_list()

        # get machine_id and sampling interval for data acquisition
        self.machine_id = pl.get("machine_id", "Unknown-ID")
        self.sampling_interval = float(pl.get("dataq_sampling_interval", 60.0))

        # get initial wait time [s] (to avoid missing first cycles when intervall is rel. long. has to be longer than longest delay)
        self.initial_wait_time = float(pl.get("initial_wait_time"))

        # create shutdown event and file lock for threading 
        self.shutdown_event = threading.Event()  # Used to stop threads gracefully
        self.file_lock = threading.Lock()

        # allocate for sensor measurement data
        self.csv_file_path = None  # initialized on first loop

        # event counter (number of inflow events since programm start)
        self.nbr_events = 0

        # last event inflow and cumulative inflow volume since program start
        self.last_event_inflow = 0
        self.cumulative_inflow = 0


    # Data acquisition
    def data_acquisition(self, sensors, actuators):
        current_date = None

        while not self.shutdown_event.is_set():
            # Get current date and compare with the last used one
            new_date = datetime.datetime.now().strftime("%Y-%m-%d")
            if new_date != current_date:
                current_date = new_date
                file_name = f"{current_date}_{self.machine_id}_measurement_data.csv"
                self.csv_file_path = get_file_path("data", file_name)

                # Create file if it doesn't exist (no header needed)
                if not os.path.exists(self.csv_file_path):
                    open(self.csv_file_path, "a").close()  # create an empty file

            # Start a thread per sensor / actuator reading
            time_before_logging = time.time()
            threads = []

            # sensor read threads
            for sensor in sensors:
                thread = threading.Thread(target=self._read_and_log_sensor, args=(sensor,))
                thread.start()
                threads.append(thread)

            # actuator read threads
            for actuator in actuators:
                thread = threading.Thread(target=self._read_and_log_actuator, args=(actuator,))
                thread.start()
                threads.append(thread)

            # event thread
            thread = threading.Thread(target=self._read_and_log_event)
            thread.start()
            threads.append(thread)

            # CPU temperature thread
            thread = threading.Thread(target=self._read_and_log_CPU_temp)
            thread.start()
            threads.append(thread)

            # Wait for all sensor read threads to complete before the next loop
            for thread in threads:
                thread.join()
            
            delta_time_logging = time.time() - time_before_logging
            
            if delta_time_logging < self.sampling_interval:
                time.sleep(self.sampling_interval-delta_time_logging)
            else:
                print("\nWARNING: sampling interval for data acquisition is shorter than required time for reading sensor data (communication with hardware)")
                
        print(f"\nData logging stopped. Saved file: {self.csv_file_path}")

    def _read_and_log_sensor(self, sensor):
        # Prepare row data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        global_runtime = time.time() - self.start_time
        io_type = "Sensor"
        value = sensor.read_value()

        row = [
            timestamp,
            f"{global_runtime:.2f}",
            self.machine_id,
            io_type,
            sensor.type,
            sensor.name,
            sensor.address,
            sensor.state,
            value,
            sensor.value_aux_1,
            sensor.value_aux_2
        ]

        # Safely write to file
        with self.file_lock:
            with open(self.csv_file_path, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def _read_and_log_actuator(self, actuator):
        # Prepare row data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        global_runtime = time.time() - self.start_time
        io_type = "Actuator"

        row = [
            timestamp,
            f"{global_runtime:.2f}",
            self.machine_id,
            io_type,
            actuator.type,
            actuator.name,
            actuator.address,
            actuator.state,
            0,
            0,
            0,
            0
        ]

        # Safely write to file
        with self.file_lock:
            with open(self.csv_file_path, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def _read_and_log_event(self):
        # Prepare row data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        global_runtime = time.time() - self.start_time
        io_type = "Event"

        row = [
            timestamp,
            f"{global_runtime:.2f}",
            self.machine_id,
            io_type,
            self.nbr_events,
            self.last_event_inflow,
            self.cumulative_inflow,
            0,
            0,
            0,
            0
        ]

    def _read_and_log_CPU_temp(self):
        # Prepare row data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        global_runtime = time.time() - self.start_time
        io_type = "CPU"

        temp_str = os.popen("vcgencmd measure_temp").readline()
        temp_value = float(temp_str.replace("temp=", "").replace("'C\n", ""))

        # print(f"CPU Temperature: {temp_value}°C")

        row = [
            timestamp,
            f"{global_runtime:.2f}",
            self.machine_id,
            io_type,
            temp_value,
            0,
            0,
            0,
            0,
            0,
            0
        ]

        # Safely write to file
        with self.file_lock:
            with open(self.csv_file_path, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    # cyclic routine: evaporator feed
    def evaporator_feed(self, actuators, sensors, actuator_name_list, sensor_name_list):

        while not self.shutdown_event.is_set():

            # read up-to-date control parameters (do this here in case parameters have been changed in toml file during program run)
            pl = self.load_parameter_list()
            tau_M0102_interval  = float(pl.get("tau_M0102_interval"))
            tau_M0102_runtime   = float(pl.get("tau_M0102_runtime"))
            tau_M0102_delay     = float(pl.get("tau_M0102_delay"))
            threshold_min_B0101 = float(pl.get("threshold_min_B0101"))

            if tau_M0102_interval-tau_M0102_runtime <=1:
                print(f"WARNING: time difference between interval and runtime should be longer than 1 sec.")

            # get instance of required S&A
            act_M0102 = actuators[actuator_name_list.index("M0102")]
            sen_B0101 = sensors[sensor_name_list.index("B0101")]


            current_runtime = time.time() - (self.start_time + self.initial_wait_time)
            if int(current_runtime - tau_M0102_delay) % int(tau_M0102_interval) == 0:

                if sen_B0101.value > threshold_min_B0101:
                    # Turn actuator on
                    print(f"[Pump Control] Activating evaporator feed pump at runtime: {current_runtime:.2f}s")
                    act_M0102.set_state(True)

                    time.sleep(tau_M0102_runtime)  # Wait for the specified runtime
                    
                    # Turn actuator off
                    print(f"[Pump Control] Deactivating evaporator feed pump at runtime: {current_runtime + tau_M0102_runtime:.2f}s")
                    act_M0102.set_state(False)

            time.sleep(0.1)


    # cyclic routine: stabilizer stirrer 
    def stabilizer_stirrer(self, actuators, actuator_name_list):

        while not self.shutdown_event.is_set():
            pl_DS = self.load_parameter_list()
            tau_M0101_interval = float(pl_DS.get("tau_M0101_interval"))
            tau_M0101_runtime  = float(pl_DS.get("tau_M0101_runtime"))
            tau_M0101_delay  = float(pl_DS.get("tau_M0101_delay"))

            if tau_M0101_interval-tau_M0101_runtime <=1:
                print(f"WARNING: time difference between interval and runtime should be longer than 1 sec.")

            # get instance of required S&A
            act_M0101 = actuators[actuator_name_list.index("M0101")]
        
            current_runtime = time.time() - (self.start_time + self.initial_wait_time)
            if int(current_runtime - tau_M0101_delay) % int(tau_M0101_interval) == 0:
                # Turn actuator on
                # print(f"[Pump Control] Activating stabilizer stirrer at runtime: {current_runtime:.2f}s")
                act_M0101.set_state(True)

                time.sleep(tau_M0101_runtime)  # Wait for the specified runtime
                
                # Turn actuator off
                # print(f"[Pump Control] Deactivating stabilizer stirrer at runtime: {current_runtime + tau_M0101_runtime:.2f}s")
                act_M0101.set_state(False)

            time.sleep(0.1)


    # triggered routine: collector drain
    def collector_drain(self, actuators, sensors, actuator_name_list, sensor_name_list):
        
        while not self.shutdown_event.is_set():

            # read up-to-date control parameters (do this here in case parameters have been changed in toml file during program run)
            pl = self.load_parameter_list()
            tau_M0111_runtime   = float(pl.get("tau_M0111_runtime"))
            tau_M0111_delay     = float(pl.get("tau_M0111_delay"))
            threshold_min_B0111 = float(pl.get("threshold_min_B0111"))

            # get instance of required S&A
            act_M0111 = actuators[actuator_name_list.index("M0111")]
            sen_B0111 = sensors[sensor_name_list.index("B0111")]

            if sen_B0111.read_value() > threshold_min_B0111:

                # Wait for the specified pre-delay
                time.sleep(tau_M0111_delay)

                # get inflow volume from collector tube sensor and update inflow event data
                self.last_event_inflow = sen_B0111.read_value()
                self.update_inflow_data(self.last_event_inflow)

                current_runtime = time.time() - (self.start_time + self.initial_wait_time)
                # Turn actuator on
                print(f"[Pump Control] Activating concentrator drain pump at runtime: {current_runtime:.2f}s")
                act_M0111.set_state(True)

                # Wait for the specified runtime
                time.sleep(tau_M0111_runtime)
                
                # Turn actuator off
                print(f"[Pump Control] Deactivating concentrator drain pump at runtime: {current_runtime + tau_M0111_runtime:.2f}s")
                act_M0111.set_state(False)


            time.sleep(10)


    # triggered routine: collector flush
    def collector_flush(self, actuators, sensors, actuator_name_list, sensor_name_list):
        
        while not self.shutdown_event.is_set():

            # read up-to-date control parameters (do this here in case parameters have been changed in toml file during program run)
            pl = self.load_parameter_list()
            tau_M0112_runtime   = float(pl.get("tau_M0112_runtime"))
            tau_M0112_delay     = float(pl.get("tau_M0112_delay"))
            threshold_min_B0111 = float(pl.get("threshold_min_B0111"))

            # get instance of required S&A
            act_M0112 = actuators[actuator_name_list.index("M0112")]
            sen_B0111 = sensors[sensor_name_list.index("B0111")]

            if sen_B0111.value > threshold_min_B0111:

                # Wait for the specified pre-delay
                time.sleep(tau_M0112_delay)

                current_runtime = time.time() - (self.start_time + self.initial_wait_time)
                # Turn actuator on
                print(f"[Pump Control] Activating concentrator flush pump at runtime: {current_runtime:.2f}s")
                act_M0112.set_state(True)

                # Wait for the specified runtime
                time.sleep(tau_M0112_runtime)
                
                # Turn actuator off
                print(f"[Pump Control] Deactivating concentratro flush pump at runtime: {current_runtime + tau_M0112_runtime:.2f}s")
                act_M0112.set_state(False)


            time.sleep(10)


    # running routine: evaporation
    def evaporation(self, actuators, sensors, actuator_name_list, sensor_name_list):
        
        while not self.shutdown_event.is_set():

            # read up-to-date control parameters (do this here in case parameters have been changed in toml file during program run)
            pl = self.load_parameter_list()
            threshold_min_B0201 = float(pl.get("threshold_min_B0201"))

            # get instance of required S&A
            act_M0201 = actuators[actuator_name_list.index("M0201")]
            act_M0202 = actuators[actuator_name_list.index("M0202")]
            act_M0301 = actuators[actuator_name_list.index("M0301")]
            sen_B0201 = sensors[sensor_name_list.index("B0201")]

            current_runtime = time.time() - (self.start_time + self.initial_wait_time)
            if sen_B0201.value > threshold_min_B0201:
                # print(f"[Control] Evaporation process running at runtime: {current_runtime:.2f}s")

                # Turn actuators ON
                act_M0201.set_state(True) # disc motor
                act_M0202.set_state(True) # fans
                act_M0301.set_state(True) # dehumidifier

            else:

                # Turn actuators OFF
                act_M0201.set_state(False) # disc motor
                act_M0202.set_state(False) # fans
                act_M0301.set_state(False) # dehumidifier

            time.sleep(1)


    # cyclic routine: concentrate discharge
    def concentrate_discharge(self, actuators, sensors, actuator_name_list, sensor_name_list):

        while not self.shutdown_event.is_set():
            pl_DS = self.load_parameter_list()
            tau_M0203_interval  = float(pl_DS.get("tau_M0203_interval"))
            tau_M0203_runtime   = float(pl_DS.get("tau_M0203_runtime"))
            tau_M0203_delay     = float(pl_DS.get("tau_M0203_delay"))
            threshold_min_B0201 = float(pl_DS.get("threshold_min_B0201"))

            if tau_M0203_interval-tau_M0203_runtime <=1:
                print(f"WARNING: time difference between interval and runtime should be longer than 1 sec.")

            # get instance of required S&A
            act_M0203 = actuators[actuator_name_list.index("M0203")]
            sen_B0401 = sensors[sensor_name_list.index("B0401")]
            sen_B0201 = sensors[sensor_name_list.index("B0201")]
        
            current_runtime = time.time() - (self.start_time + self.initial_wait_time)
            if int(current_runtime - tau_M0203_delay) % int(tau_M0203_interval) == 0:

                # only discharge when concentrate tank is not full (check whether sensor is NO or NC)
                # only discharge when evaporator tank liquid level is not below minimum
                if sen_B0401.state == False and sen_B0201.value > threshold_min_B0201:
                    # Turn actuator on
                    # print(f"[Pump Control] Activating sludge pump at runtime: {current_runtime:.2f}s")
                    act_M0203.set_state(True)

                    time.sleep(tau_M0203_runtime)  # Wait for the specified runtime
                    
                    # Turn actuator off
                    # print(f"[Pump Control] Deactivating sludge pump at runtime: {current_runtime + tau_M0203_runtime:.2f}s")
                    act_M0203.set_state(False)

            time.sleep(0.1)


    # observer routine
    def observer(self, sensors, sensor_name_list):
        
        while not self.shutdown_event.is_set():

            # read up-to-date control parameters (do this here in case parameters have been changed in toml file during program run)
            pl = self.load_parameter_list()
            threshold_min_B0101 = float(pl.get("threshold_min_B0101"))
            threshold_max_B0101 = float(pl.get("threshold_max_B0101"))
            threshold_min_B0102 = float(pl.get("threshold_min_B0102"))
            threshold_min_B0202 = float(pl.get("threshold_min_B0202"))
            threshold_min_B0201 = float(pl.get("threshold_min_B0201"))
            threshold_min_B0111 = float(pl.get("threshold_min_B0111"))

            # get instance of required S&A
            sen_B0101 = sensors[sensor_name_list.index("B0101")]
            sen_B0102 = sensors[sensor_name_list.index("B0102")]
            sen_B0201 = sensors[sensor_name_list.index("B0201")]
            sen_B0202 = sensors[sensor_name_list.index("B0202")]
            sen_B0111 = sensors[sensor_name_list.index("B0111")]
            sen_B0401 = sensors[sensor_name_list.index("B0401")]

            time.sleep(10)
            current_runtime = time.time() - (self.start_time + self.initial_wait_time)

            if sen_B0102.value < threshold_min_B0102:
                print("\n[[GUI]]")
                print(f"pH in Stabilizer is too low.")

            if sen_B0202.value < threshold_min_B0202:    
                print("\n[[GUI]]")
                print(f"pH in Evaporator is too low.")
            
            if sen_B0101.value < threshold_min_B0101:
                print("\n[[GUI]]")
                print(f"Liquid level ({sen_B0101.value}) in stabilizer tank bellow minimum ({threshold_min_B0101}). No feed to evaporator.")

            if sen_B0101.value > threshold_max_B0101:
                print("\n[[GUI]]")
                print(f"Liquid level ({sen_B0101.value}) in stabilizer tank at maximum ({threshold_max_B0101}). Effluent via overflow!")

            if sen_B0111.value > threshold_min_B0111:
                print("\n[[GUI]]")
                print(f"Inflow detected: Event counter at [{self.nbr_events}]")

            if sen_B0401.state == True:
                print("\n[[GUI]]")
                print("Concentrate tank is full")

            if sen_B0201.value < threshold_min_B0201:
                print("\n[[GUI]]")
                print(f"Liquid level ({sen_B0201.value}) in evaporator at minimum ({threshold_min_B0201}). Evaporation and concentrate discharge disabled!")


    def print_sensor_values_to_prompt(self, sensors, sensor_namel_list):
            
        while not self.shutdown_event.is_set():
            
            # read up-to-date parameter list (do this here in case parameters have been changed in toml file during program run)
            pl = self.load_parameter_list()

            current_runtime = time.time() - (self.start_time + self.initial_wait_time)
            for sensor, name in zip(sensors, sensor_namel_list):

                # check if there is a corresponding flag in the parameter list
                flag_name = "print_"+name
                if flag_name in pl:

                    # get the state of the flag for printing / not printing
                    flag = pl.get(flag_name)
                    if flag == "True":
                        if sensor.type == "EZO-HUM":
                            print(f"Sensor '{name}' reads: {sensor.value} / {sensor.value_aux_1} at runtime {current_runtime} [s]")
                        else:
                            print(f"Sensor '{name}' reads: {sensor.value} at runtime {current_runtime} [s]")
                else:
                    print(f"No flag for printing / not printing of sensor {name} in parameter file.")
            
            time.sleep(2)


    
    # Clean up after keyboard interrupt
    def handle_shutdown(self, pxt):
        print("\nShutdown signal received. Cleaning up...")
        self.shutdown_event.set()

        # clean-up and close PiXtend instance
        pxt.digital_out0  = pxt.OFF
        pxt.digital_out1  = pxt.OFF
        pxt.digital_out2  = pxt.OFF
        pxt.digital_out3  = pxt.OFF
        pxt.digital_out4  = pxt.OFF
        pxt.digital_out5  = pxt.OFF
        pxt.digital_out6  = pxt.OFF
        pxt.digital_out7  = pxt.OFF
        pxt.digital_out8  = pxt.OFF
        pxt.digital_out9  = pxt.OFF
        pxt.digital_out10 = pxt.OFF
        pxt.digital_out11 = pxt.OFF
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
        print("Wait while storing measurement data...")

    # Function to load process control parameters from the TOML file
    def load_parameter_list(self):
        with open(self.parameter_file_path, "rb") as f:
            parameter_list = tomllib.load(f)
        return parameter_list

    def update_inflow_data(self, inflow_volume):

        self.nbr_events += 1
        self.cumulative_inflow += inflow_volume
