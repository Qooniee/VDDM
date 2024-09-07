import asyncio
import sys
import os

# Add the parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
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
