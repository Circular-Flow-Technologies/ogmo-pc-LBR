import threading
import datetime
import time
import os
import csv
import tomllib
import numpy as np

from src.utils import get_file_path
 

class routines:
    def __init__(self, start_time, parameter_file_name, log_file_name):

        """
        Constructor to initialize the sensor object from sensor data.
        """
        self.start_time = start_time

        # access parameter file
        self.parameter_file_path = get_file_path("read", parameter_file_name)
        pl = self.load_parameter_list()

        # load log-file
        self.log_file_path = get_file_path("data", log_file_name)

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
        self.event_nbr = self.read_latest_from_log_file('event_number')

        # last event inflow and cumulative inflow volume since program start
        self.last_event_inflow = 0
        self.cumulative_inflow = self.read_latest_from_log_file('cumulative_inflow')

        # routine status flags
        self.collector_drain_running       = False
        self.evaporator_feed_running       = False
        self.evaporation_running           = False
        self.concentrate_discharge_running = False

        # timer for evaporation duty cycle
        self.evaporation_start_time = start_time

        # state tracker for observer
        self.observer_states = {}


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
                time.sleep(0.2)
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
            0,
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
            0,
            0,
            0,
            0,
            self.event_nbr,
            self.last_event_inflow,
            self.cumulative_inflow,
        ]
        
        # Safely write to file
        with self.file_lock:
            with open(self.csv_file_path, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def _read_and_log_CPU_temp(self):
        # Prepare row data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        global_runtime = time.time() - self.start_time
        io_type = "CPU"
        name = "CPU-Temp"

        temp_str = os.popen("vcgencmd measure_temp").readline()
        temp_value = float(temp_str.replace("temp=", "").replace("'C\n", ""))

        row = [
            timestamp,
            f"{global_runtime:.2f}",
            self.machine_id,
            io_type,
            0,
            name,
            0,
            0,
            temp_value,
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
                    # print(f"[Pump Control] Activating evaporator feed pump at runtime: {current_runtime:.2f}s")
                    act_M0102.set_state(True)

                    time.sleep(tau_M0102_runtime)  # Wait for the specified runtime
                    
                    # Turn actuator off
                    # print(f"[Pump Control] Deactivating evaporator feed pump at runtime: {current_runtime + tau_M0102_runtime:.2f}s")
                    act_M0102.set_state(False)

            time.sleep(0.1)


    # cyclic routine: stabilizer stirrer 
    def stabilizer_stirrer(self, actuators, sensors, actuator_name_list, sensor_name_list):

        while not self.shutdown_event.is_set():
            pl = self.load_parameter_list()
            tau_M0101_interval = float(pl.get("tau_M0101_interval"))
            tau_M0101_runtime  = float(pl.get("tau_M0101_runtime"))
            tau_M0101_delay  = float(pl.get("tau_M0101_delay"))
            refill_flag = str(pl.get("CaOH2_refill"))

            if tau_M0101_interval-tau_M0101_runtime <=1:
                print(f"WARNING: time difference between interval and runtime should be longer than 1 sec.")

            # get instance of required S&A
            act_M0101 = actuators[actuator_name_list.index("M0101")]
            sen_BM101 = sensors[sensor_name_list.index("BM101")]
        
            current_runtime = time.time() - (self.start_time + self.initial_wait_time)
            if int(current_runtime - tau_M0101_delay) % int(tau_M0101_interval) == 0 and refill_flag == "False":
                # Turn actuator on
                # print(f"[Pump Control] Activating stabilizer stirrer at runtime: {current_runtime:.2f}s")
                
                # Turn actuators ON (depending on over-current management settings)
                if sen_BM101.value == False:
                    act_M0101.set_state(True) # disc motor
                else:
                    time.sleep(12) # give observer some time to detect
                    act_M0101.set_state(False)
                    self.relaunch_motor(act_M0101) # relaunch depends on flag in parameters file


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

                current_runtime = time.time() - (self.start_time + self.initial_wait_time)
                # Turn actuator on
                print(f"[Pump Control] Activating collector tube drain pump at runtime: {current_runtime:.2f}s")
                act_M0111.set_state(True)
                self.collector_drain_running = True

                # Wait for the specified runtime
                time.sleep(tau_M0111_runtime)
                
                # Turn actuator off
                print(f"[Pump Control] Deactivating collector tube drain pump at runtime: {current_runtime + tau_M0111_runtime:.2f}s")
                act_M0111.set_state(False)
                self.collector_drain_running = False


            time.sleep(1)


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

            if sen_B0111.value > threshold_min_B0111 and not(self.collector_drain_running):

                # Wait for the specified pre-delay
                time.sleep(tau_M0112_delay)

                # get inflow volume from collector tube sensor and update inflow event data
                self.last_event_inflow = sen_B0111.read_value()
                self.update_inflow_data(self.last_event_inflow)

                current_runtime = time.time() - (self.start_time + self.initial_wait_time)
                # Turn actuator on
                print(f"[Pump Control] Activating collector tube flush pump at runtime: {current_runtime:.2f}s")
                act_M0112.set_state(True)

                # Wait for the specified runtime
                time.sleep(tau_M0112_runtime)
                
                # Turn actuator off
                print(f"[Pump Control] Deactivating collector tube flush pump at runtime: {current_runtime + tau_M0112_runtime:.2f}s")
                act_M0112.set_state(False)


            time.sleep(1)


    # running routine: evaporation
    def evaporation(self, actuators, sensors, actuator_name_list, sensor_name_list):
        
        while not self.shutdown_event.is_set():

            # read up-to-date control parameters (do this here in case parameters have been changed in toml file during program run)
            pl = self.load_parameter_list()
            threshold_min_B0201 = float(pl.get("threshold_min_B0201"))
            tau_M0201_runtime   = float(pl.get("tau_M0201_runtime"))
            tau_M0201_interval = float(pl.get("tau_M0201_interval"))

            # get instance of required S&A
            act_M0201 = actuators[actuator_name_list.index("M0201")]
            act_M0204 = actuators[actuator_name_list.index("M0204")]
            act_M0205 = actuators[actuator_name_list.index("M0205")]
            act_M0301 = actuators[actuator_name_list.index("M0301")]
            sen_B0201 = sensors[sensor_name_list.index("B0201")]
            sen_BM201 = sensors[sensor_name_list.index("BM201")]

            current_runtime = time.time() - self.evaporation_start_time
            evap_duty_cycle = int(current_runtime/tau_M0201_runtime) % int(tau_M0201_interval/tau_M0201_runtime) == 0
            if sen_B0201.value > threshold_min_B0201 and not(self.evaporation_running) and evap_duty_cycle:

                # start timer for evaporation duty cycle
                self.evaporation_start_time = time.time()

                # Turn actuators ON (depending on over-current management settings)
                if sen_BM201.value == False:
                    act_M0201.set_state(True) # disc motor
                else:
                    time.sleep(12) # give observer some time to detect
                    act_M0201.set_state(False)
                    self.relaunch_motor(act_M0201) # relaunch depends on flag in parameters file

                #act_M0204.set_state(True) # fans out                 
                #act_M0205.set_state(True) # fans in           
                #act_M0301.set_state(True) # dehumidifier

                # turn ON routine status flag
                self.evaporation_running = True
                self.add_log_file_entry("evaporation_run", 1)
                print("Evaporation process started")

            # hysteresis control for turning evaporation off to avoid state flickering
            elif (sen_B0201.value < (threshold_min_B0201 - 1.0) or not(evap_duty_cycle)) and self.evaporation_running:

                # Turn actuators OFF
                act_M0201.set_state(False) # disc motor
                act_M0204.set_state(False) # fans out
                act_M0205.set_state(False) # fans in
                act_M0301.set_state(False) # dehumidifier

                # turn OFF routine status flag
                self.evaporation_running  = False
                self.add_log_file_entry("evaporation_run", 0)
                print("Evaporation process stopped")

            time.sleep(1)


    def relaunch_motor(self, actuator):
        pl = self.load_parameter_list()
        relaunch_flag = str(pl.get(f"relaunch_{self.name}"))

        if relaunch_flag == "True":
            actuator.set_state(True)


    # cyclic routine: concentrate discharge
    def concentrate_discharge(self, actuators, sensors, actuator_name_list, sensor_name_list):

        while not self.shutdown_event.is_set():
            pl = self.load_parameter_list()
            tau_M0203_interval  = float(pl.get("tau_M0203_interval"))
            tau_M0203_runtime   = float(pl.get("tau_M0203_runtime"))
            tau_M0203_delay     = float(pl.get("tau_M0203_delay"))
            threshold_min_B0201 = float(pl.get("threshold_min_B0201"))

            if tau_M0203_interval-tau_M0203_runtime <=1:
                print(f"WARNING: time difference between interval and runtime should be longer than 1 sec.")

            # get instance of required S&A
            act_M0202 = actuators[actuator_name_list.index("M0202")]
            act_M0203 = actuators[actuator_name_list.index("M0203")]
            sen_B0401 = sensors[sensor_name_list.index("B0401")]
            sen_B0201 = sensors[sensor_name_list.index("B0201")]
            sen_BM202 = sensors[sensor_name_list.index("BM202")]
        
            current_runtime = time.time() - (self.start_time + self.initial_wait_time)
            if int(current_runtime - tau_M0203_delay) % int(tau_M0203_interval) == 0:

                # only discharge when concentrate tank is not full (check whether sensor is NO or NC)
                # only discharge when evaporator tank liquid level is not below minimum
                if sen_B0401.value == True and sen_B0201.value > threshold_min_B0201:

                    if sen_BM202.value == False:
                        act_M0202.set_state(True) # fans
                    else:
                        time.sleep(12) # give observer some time to detect
                        act_M0202.set_state(False)
                        self.relaunch_motor(act_M0202) # relaunch depends on flag in parameters file

                    time.sleep(5) # let screw run for some seconds before pump is activated
                    act_M0203.set_state(True)

                    time.sleep(tau_M0203_runtime)  # Wait for the specified runtime
                    
                    act_M0202.set_state(False)
                    act_M0203.set_state(False)

            time.sleep(0.1)


    def observer(self, sensors, sensor_name_list):
        while not self.shutdown_event.is_set():
            # Load latest parameters
            pl = self.load_parameter_list()
            threshold_min_B0101 = float(pl.get("threshold_min_B0101"))
            threshold_max_B0101 = float(pl.get("threshold_max_B0101"))
            threshold_max_B0102 = float(pl.get("threshold_max_B0102"))
            threshold_max_B0202 = float(pl.get("threshold_max_B0202"))
            threshold_min_B0201 = float(pl.get("threshold_min_B0201"))
            threshold_min_B0111 = float(pl.get("threshold_min_B0111"))

            # Get sensor instances
            sen = {name: sensors[sensor_name_list.index(name)] for name in sensor_name_list}

            time.sleep(10)
            current_runtime = time.time() - (self.start_time + self.initial_wait_time)

            if self.check_and_log_rising_edge("B0102_high_pH", sen["B0102"].value > threshold_max_B0102,
                                        "B0102_pH_high", sen["B0102"].value):
                print("\n[[GUI]]")
                print("pH in Stabilizer is too low.")

            if self.check_and_log_rising_edge("B0202_high_pH", sen["B0202"].value > threshold_max_B0202,
                                        "B0202_pH_high", sen["B0202"].value):
                print("\n[[GUI]]")
                print("pH in Evaporator is too low.")

            if self.check_and_log_rising_edge("B0101_liquid_low", sen["B0101"].value < threshold_min_B0101,
                                        "B0101_level_low", sen["B0101"].value):
                print("\n[[GUI]]")
                print(f"Liquid level ({sen['B0101'].value}) in stabilizer tank below minimum ({threshold_min_B0101}). No feed to evaporator.")

            # if self.check_and_log_rising_edge("B0101_liquid_high", sen["B0101"].value > threshold_max_B0101,
            #                             "B0101_level_high", sen["B0101"].value):
            #     print("\n[[GUI]]")
            #     print(f"Liquid level ({sen['B0101'].value}) in stabilizer tank at maximum ({threshold_max_B0101}). Effluent via overflow!")

            if self.check_and_log_rising_edge("B0111_inflow", sen["B0111"].value > threshold_min_B0111,
                                        "event_number", self.event_nbr):
                print("\n[[GUI]]")
                print(f"Inflow detected: Event counter at [{self.event_nbr}]")

            if self.check_and_log_rising_edge("B0401_tank_full", not sen["B0401"].value,
                                        "B0401_concentrate_full", sen["B0401"].value):
                print("\n[[GUI]]")
                print("DETECTION: Concentrate tank is full")

            if self.check_and_log_rising_edge("B0201_level_low", sen["B0201"].value < threshold_min_B0201,
                                        "B0201_level_low", sen["B0201"].value):
                print("\n[[GUI]]")
                print(f"Liquid level ({sen['B0201'].value}) in evaporator at minimum ({threshold_min_B0201}). Evaporation and concentrate discharge disabled!")

            if self.check_and_log_rising_edge("BM101_detected", sen["BM101"].value,
                                        "overcurrent_detection", sen["BM101"].descr):
                print("\n[[GUI]]")
                print(f"DETECTION: {sen['BM101'].descr}")

            if self.check_and_log_rising_edge("BM201_detected", sen["BM201"].value,
                                        "overcurrent_detection", sen["BM201"].descr):
                print("\n[[GUI]]")
                print(f"DETECTION: {sen['BM201'].descr}")

            if self.check_and_log_rising_edge("BM202_detected", sen["BM202"].value,
                                        "overcurrent_detection", sen["BM202"].descr):
                print("\n[[GUI]]")
                print(f"DETECTION: {sen['BM202'].descr}")

            time.sleep(0.1)


    def check_and_log_rising_edge(self, condition_key, current_state, log_tag, log_value):
        previous_state = self.observer_states.get(condition_key, False)

        # Store the current state for the next iteration
        self.observer_states[condition_key] = current_state

        # Log only if it was False and is now True
        if not previous_state and current_state:
            self.add_log_file_entry(log_tag, log_value)
            return True  # Rising edge detected and logged

        return False  # No rising edge, no log

    # write information to log-file
    def add_log_file_entry(self, tag, value):

        new_entry = {
            'datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'tag': tag,
            'value': str(value)
            }
        
        # Safely write to file
        with self.file_lock:
            with open(self.log_file_path, mode="a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=['datetime', 'tag', 'value'])
                writer.writerow(new_entry)


    # Ca(OH)2 refill procedure
    def CaOH2_refill(self, actuators, actuator_name_list):
        
        while not self.shutdown_event.is_set():

            # read up-to-date control parameters (do this here in case parameters have been changed in toml file during program run)
            pl = self.load_parameter_list()
            CaOH2_dosing = float(pl.get("CaOH2_dosing"))
            flag = str(pl.get("CaOH2_refill"))

            # get instance of required S&A
            act_M0101 = actuators[actuator_name_list.index("M0101")]

            if flag == "True":
                last_CaOH2_refill = self.read_latest_from_log_file('CaOH2_refill')
                cumulative_inflow_last_CaOH2_added = self.read_latest_from_log_file('cumulative_inflow_last_CaOH2_refill')

                # cumulative inflow since last refill
                ci_diff = self.cumulative_inflow - cumulative_inflow_last_CaOH2_added

                # calculate remaining buffer capacity (based on CaOH2 dosing/consumption)
                buffer_cap_last_refill = last_CaOH2_refill/CaOH2_dosing
                remaining_buffer_cap = ci_diff - buffer_cap_last_refill

                print("\n********* Start Ca(OH)2 refill procedure *********")
                act_M0101.set_state(True)
                print(f"Remaining buffer capacity (in L, based on dosing/consumption of {CaOH2_dosing} g/L): {remaining_buffer_cap}\n")
                print("Procedure: 1) Weigh Ca(OH)2 amount to be added.")
                print("           2) Open stabilizer tank and add Ca(OH)2 while stirrer is running.")
                CaOH2_refill = input("           3) Enter added amount of Ca(OH)2 in [g]: ")
                time.sleep(2)
                act_M0101.set_state(False)
                self.add_log_file_entry("cumulative_inflow_last_CaOH2_refill", self.cumulative_inflow)
                self.add_log_file_entry("CaOH2_refill", CaOH2_refill)
                input("Change 'CaOH2_refill' to 'False' in parameters.toml and save file. (Press any key when done)")
                print("\n*********** End Ca(OH)2 refill procedure *********")

            time.sleep(0.1)


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

    # read latest event data from log-file
    def read_latest_from_log_file(self, tag):
        latest_value = 0
        rows = []
        with open(self.log_file_path, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                rows.append(row)
                if row['tag'] == tag:
                    latest_value = float(row['value'])
        return latest_value
        
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

        self.event_nbr += 1
        self.cumulative_inflow += inflow_volume

        self.add_log_file_entry('cumulative_inflow', self.cumulative_inflow)
        # logging of event numbe in 'observer'
