import obd
import os
import time
from collections import deque
import numpy as np
import pandas as pd
import datetime
import asyncio
import scipy
from scipy import signal
import matplotlib as plt
import sys
from collections import defaultdict
import random

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)

from config.config_manager import load_config
config_path = os.path.join(parent_dir, 'config', 'measurement_system_config.yaml')

class ELM327:
    def __init__(self, config):
        """
        Initialize the ELM327 class with configuration parameters.

        Args:
            config (dict): Configuration parameters for the ELM327.
        """
        self.COLUMNS = config.data_columns    
        self.SAMPLING_FREQUENCY_HZ = config.sampling_frequency_hz
        self.SAMPLING_TIME = 1 / self.SAMPLING_FREQUENCY_HZ
        self.SAVE_DATA_DIR = config.save_data_dir
        self.SEQUENCE_LENGTH = config.sequence_length
        self.FPASS = config.filter_params.fpass
        self.FSTOP = config.filter_params.fstop
        self.GPASS = config.filter_params.gpass
        self.GSTOP = config.filter_params.gstop
        self.Isfilter = config.filter_params.is_filter
        self.res = self.connect_to_elm327()
        
        self.is_offline = config.is_offline
        self.IsStart = False
        self.IsStop = True
        self.Is_show_real_time_data = config.is_show_real_time_data

    def initialize_BLE(self):
        """
        Initialize Bluetooth Low Energy (BLE) for ELM327 connection.
        """
        os.system('sudo hcitool scan')
        os.system('sudo hciconfig hci0 up')
        os.system('sudo rfcomm bind 0 8A:2A:D4:FF:38:F3')
        os.system('sudo rfcomm listen 0 1 &')

    def connect_to_elm327(self):
        """
        Establish a connection to the ELM327 device.

        Returns:
            res (obd.OBDStatus): The connection status of the ELM327 device.
        """
        res = None
        try:
            self.initialize_BLE()
            self.connection = obd.OBD()
            print(self.connection.status())
            res = self.connection.status()
            if res == obd.OBDStatus.CAR_CONNECTED:
                print("----------Connection establishment is successful!----------")
                return res
            else:
                print("----------Connection establishment failed!----------")
                print("End program. Please check settings of the computer and ELM327")
        except Exception as e:
            print("----------Exception!----------")
            print(e)
        finally:
            return res

    def get_data_from_sensor(self):
        """
        Retrieve data from the sensor.

        Returns:
            dict: A dictionary containing sensor data.
        """
        if self.is_offline:
            data = self.get_data_from_sensor_stub()
        else:
            # Retrieve data and save it in dictionary format
            data = {column: self.get_obd2_value(column) for column in self.COLUMNS}
        return data

    def get_obd2_value_debug(self, column):
        """
        Retrieve OBD-II value for a specific column with debug information.

        Args:
            column (str): The OBD-II command column.

        Returns:
            float or None: The value of the OBD-II command, or None if not available.
        """
        command = getattr(obd.commands, column, None)
        if command:
            response = self.connection.query(command)
            if response:
                print(f"Response for command '{command}': {response}")
                if response.value is not None:  # Check for None
                    print(f"Response value for command '{command}': {response.value}")
                    return response.value.magnitude
                else:
                    print(f"No value in response for command '{command}'")
            else:
                print(f"No response for command '{command}'")
        else:
            print(f"No command found for column '{column}'")
        return None

    def get_obd2_value(self, column):
        """
        Retrieve OBD-II value for a specific column.

        Args:
            column (str): The OBD-II command column.

        Returns:
            float or None: The value of the OBD-II command, or None if not available.
        """
        command = getattr(obd.commands, column, None)
        if command:
            response = self.connection.query(command)
            if response.value is not None:  # Check for None
                return response.value.magnitude
        return None

    def get_data_from_sensor_stub(self):
        """
        Generate stub data for the sensor.

        Returns:
            dict: A dictionary containing stub sensor data.
        """
        data_stub = {column: np.abs(np.random.randn()).astype(np.float32).item() for column in self.COLUMNS}        
        # Randomly insert None or 0.0
        if random.choice([True, False]):
            random_column = random.choice(self.COLUMNS)
            if random.choice([True, False]):
                data_stub[random_column] = None
            else:
                data_stub[random_column] = 0.0
        
        return data_stub

def format_data_for_display(data, labels):
    """
    Format sensor data for display.

    Args:
        data (dict): The sensor data to format.
        labels (list of str): The list of labels to include in the formatted string.

    Returns:
        str: A formatted string containing the sensor data.
    """
    formatted_str = ""
    for label, value in zip(labels, data.values()):
        if value is None:
            value = "None"
        else:
            value = f"{value:.4f}"
        formatted_str += f"{label}: {value} / "
    return formatted_str.rstrip(" / ")

def format_sensor_data(data, labels):
    """
    Format sensor data for display.

    Args:
        data (dict or list): The sensor data to format.
        labels (list of str): The list of labels to include in the formatted string.

    Returns:
        str: A formatted string containing the sensor data.
    """
    formatted_str = ""
    if isinstance(data, dict):
        for label in labels:
            value = data.get(label, None)
            if value is None:
                value = "None"
            else:
                value = f"{value:.4f}"
            formatted_str += f"{label}: {value} / "
    else:
        for label, value in zip(labels, data):
            if value is None:
                value = "None"
            else:
                value = f"{value:.4f}"
            formatted_str += f"{label}: {value} / "
    return formatted_str.rstrip(" / ")

def test_main():
    """
    Main function for testing sensor data collection and display.

    This function initializes the ELM327 sensor, starts a loop to collect data,
    formats the data for display, and prints it in real-time. It also calculates
    and prints the sampling delay and reliability rate upon termination.

    The main loop runs until interrupted by the user.

    Raises:
        KeyboardInterrupt: If a keyboard interrupt occurs, the loop is terminated
                           and the final statistics are printed.
    """
    from utils.tools import wait_process
    from time import perf_counter
    import matplotlib.pyplot as plt
    
    print("Main start")
    config = load_config(config_path)
    meas_elm327 = ELM327(config.sensors['elm327'])
    # res = meas_elm327.connect_to_elm327()
    
    start_time = perf_counter()
    sampling_counter = 0
    try:
        main_loop_start_time = perf_counter()
        while True:
            iteration_start_time = perf_counter()
            
            # Data acquisition process
            data = meas_elm327.get_data_from_sensor()
            
            current_time = perf_counter() - start_time
            sampling_counter += 1
    
            if meas_elm327.Is_show_real_time_data:
                formatted_data = format_sensor_data(data, meas_elm327.COLUMNS)
                print("--------------------------------------------------------------------")
                print("Current Time is: {:.3f}".format(current_time))
                print(formatted_data)
            
            # Wait to meet the sampling frequency based on the sampling interval and execution time
            elapsed_time = perf_counter() - iteration_start_time
            sleep_time = meas_elm327.SAMPLING_TIME - elapsed_time
            if sleep_time > 0:
                wait_process(sleep_time)
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    
    finally:
        main_loop_end_time = perf_counter() - main_loop_start_time
        print("Program terminated")
        print("main loop is ended. current time is: {:.3f}".format(current_time))
        print("main loop is ended. end time is: {:.3f}".format(main_loop_end_time))
        print("sampling num is: {}".format(sampling_counter))
        
        # Calculate the ideal sampling time
        ideal_time = ((sampling_counter - 1) / meas_elm327.SAMPLING_FREQUENCY_HZ)
        # Calculate the delay
        delay_time = current_time - ideal_time
        # The reliability rate is the delay divided by the sampling time
        sampling_reliability_rate = (delay_time / (sampling_counter / meas_elm327.SAMPLING_FREQUENCY_HZ)) * 100
        
        print("sampling delay is: {:.3f} s".format(delay_time))
        print("sampling delay rate is: {:.3f} %".format(sampling_reliability_rate))
    
if __name__ == '__main__':
    test_main()