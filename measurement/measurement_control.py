import asyncio
import sys
import os

# Add the parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from fusion.sensor_fusion import Sensors
from utils.tools import perf_counter, wait_process
from utils.visualize_data import format_sensor_fusion_data
from config.config_manager import load_config
import time
import threading

import pandas as pd

class MeasurementControl:
    def __init__(self, config_path):
        """
        Initializes the MeasurementControl class with the given configuration path.

        Args:
            config_path (str): Path to the configuration file.
        """
        self.is_running = False
        self.sensors = Sensors(load_config(config_path)["master"])  # Initialize sensors
        self.loop = asyncio.new_event_loop()  # Create a new event loop for non-main thread usage
        self.config_path = config_path

    def show_real_time_data(self, sensors, data, current_time):
        formatted_data = format_sensor_fusion_data(data, sensors.all_data_columns_list)
        print("--------------------------------------------------------------------")
        print("Current Time is: {:.3f}".format(current_time))
        print(formatted_data)
    
    async def start_measurement(self):
        """
        Starts the measurement process if it is not already running.

        If the measurement is already running, it will print a message indicating so.
        """
        if not self.is_running:
            self.is_running = True
            print("Measurement started.")
            await self.measurement(self.sensors)
        else:
            print("Measurement is already running.")
    
    def stop_measurement(self):
        """
        Stops the measurement process if it is currently running.

        If the measurement is not running, it will print a message indicating so.
        """
        if self.is_running:
            self.is_running = False
            print("Measurement stopped.")
        else:
            print("Measurement is not running.")
            
    def on_change_sampling_frequency(self, new_sampling_frequency):
        """
        Updates the sampling frequency of the sensors.

        Args:
            new_sampling_frequency (float): New sampling frequency in Hz (samples per second).
        """
        PREV_SAMPLING_FREQUENCY_HZ = self.sensors.SAMPLING_FREQUENCY_HZ
        PREV_SAMPLING_TIME = self.sensors.SAMPLING_TIME
        PREV_MAX_DATA_BUF_LEN = self.sensors.MAX_DATA_BUF_LEN
        
        self.sensors.SAMPLING_FREQUENCY_HZ = new_sampling_frequency
        self.sensors.SAMPLING_TIME = 1 / new_sampling_frequency
        self.sensors.MAX_DATA_BUF_LEN = int(self.sensors.SEQUENCE_LENGTH * self.sensors.SAMPLING_FREQUENCY_HZ)
        print("----------------------CHANGE SAMPLING FREQUENCY-------------------------------")
        print("--------------------------------BEFORE----------------------------------------")
        print("previous sampling frequency: {0}Hz".format(PREV_SAMPLING_FREQUENCY_HZ))
        print("previous sampling time     : {0}s".format(PREV_SAMPLING_TIME))
        print("previous max buffer length : {0}s".format(PREV_MAX_DATA_BUF_LEN))
        print("--------------------------------AFTER----------------------------------------")
        print("Update sampling frequency: {0}Hz".format(self.sensors.SAMPLING_FREQUENCY_HZ))
        print("Update sampling time     : {0}s".format(self.sensors.SAMPLING_TIME))
        print("Update max buffer length : {0}s".format(self.sensors.MAX_DATA_BUF_LEN))
        
        
    def on_change_sequence_length(self, new_sequence_length):
        """
        Updates the sequence length of the sensors.

        Args:
            new_sequence_length (int): New sequence length in sec.
        """
        PREV_SEQUENCE_LENGTH = self.sensors.SEQUENCE_LENGTH
        
        self.sensors.SEQUENCE_LENGTH = int(new_sequence_length)
        self.sensors.MAX_DATA_BUF_LEN = int(self.sensors.SEQUENCE_LENGTH * self.sensors.SAMPLING_FREQUENCY_HZ)
        print("------------------------CHANGE SEQUENCE LENGTH--------------------------------")
        print("--------------------------------BEFORE----------------------------------------")
        print("previous sequence length  : {0}s".format(PREV_SEQUENCE_LENGTH))
        print("--------------------------------AFTER----------------------------------------")
        print("Update sequence length    : {0}s".format(self.sensors.SEQUENCE_LENGTH))
        
    
    async def save_measurement_data(self):
        """
        Triggers the process to finalize the measurement and save the data.

        This function should be called to save the collected data.
        """
        print("Pressed save button")
        await self.sensors.finish_measurement_and_save_data()

    async def measurement(self, sensors):
        """
        Handles the measurement process, including data collection, processing, and display.

        Args:
            sensors (Sensors): The Sensors instance used for data collection.
        """
        print("Measurement function called.")
        main_loop_start_time = None
        sampling_counter = 0
        self.sensors.data_buffer = pd.DataFrame()
        if os.path.exists(sensors.SAVE_BUF_CSVDATA_PATH):
            os.remove(sensors.SAVE_BUF_CSVDATA_PATH)
            print(f"File  '{self.sensors.SAVE_BUF_CSVDATA_PATH}' was deleted")
        else:
            print(f"File '{self.sensors.SAVE_BUF_CSVDATA_PATH}' is not existed")
        try:
            while self.is_running:
                iteration_start_time = perf_counter() # Start time of each iteration
                
                if main_loop_start_time is None:
                    main_loop_start_time = iteration_start_time  # Initialize main loop start time
                    
                current_time = perf_counter() - main_loop_start_time # Current time
                data = sensors.collect_data() # Get data from multiple sensors
                sampling_counter += 1 # Count sampling times                                       
                converted_data = sensors.convert_dictdata(current_time, data) # Convert data to dataframe format

                # Update the data buffer. If it reaches the buffer limit, write the data to a CSV file.
                await sensors.update_data_buffer(converted_data)
                # Display data in real time. This process is executed on additional thread.
                if sensors.is_show_real_time_data:
                    show_real_time_data_thread = threading.Thread(target=self.show_real_time_data, 
                                                        args=(sensors, data, current_time), 
                                                        name="show_real_time_data_thread")
                    show_real_time_data_thread.start()

                # Wait based on the sampling interval and execution time to maintain the sampling frequency.
                iteration_end_time = perf_counter() # Iteration end time
                iteration_duration = iteration_end_time - iteration_start_time # Elapsed time of each iteration
                sleep_time = max(0, sensors.SAMPLING_TIME - iteration_duration) # Sleep time
                if sleep_time > 0:
                    wait_process(sleep_time)
            # Wait the finish of the last thread 
            show_real_time_data_thread.join()
                
        except Exception as e:
            print(e)
    
    

    
    def run_async(self, coroutine):
        """
        Runs an asynchronous coroutine in the event loop.

        Args:
            coroutine (asyncio.Future): The coroutine to run.

        If the event loop is already running, the coroutine is scheduled to run in the existing loop.
        Otherwise, a new event loop is created, and the coroutine is run until complete.
        """
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        else:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(coroutine)
    
    def cleanup(self):
        """
        Performs cleanup tasks.

        Stops the measurement process if it is running and prints a cleanup completion message.
        """
        if self.is_running:
            self.stop_measurement()
        print("Cleanup completed.")
