import os
import sys
import importlib
from time import perf_counter
from collections import defaultdict
import pandas as pd
import datetime
import asyncio
import numpy as np



parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from config import config_manager
from utils.tools import wait_process
from utils.visualize_data import format_sensor_fusion_data
from signalprocessing.filter import butterlowpass

config_path = os.path.join(parent_dir, 'config', 'measurement_system_config.yaml')


class SensorFactory:
    @staticmethod
    def create_sensor(sensor_type, config):
        try:
            # Import the appropriate sensor module based on sensor_type
            module = importlib.import_module(f"fusion.sensors.{sensor_type}_measurement")
            # Get a sensor class
            sensor_class = getattr(module, f"{sensor_type.upper()}")
            # Create a sensor instance and return
            return sensor_class(config)
        except (ImportError, AttributeError) as e:
            print(f"Error creating sensor {sensor_type}: {e}")
            return None
        

class Sensors:
    def __init__(self, config):
        self.config = config_manager.load_config(config_path)
        self.sensor_list = tuple(self.config.sensors.keys())
        self.sensor_instances = {}
        self.is_running = False
        
        
        self.SAMPLING_FREQUENCY_HZ = config.sampling_frequency_hz
        self.SAMPLING_TIME = 1 / self.SAMPLING_FREQUENCY_HZ
        self.SAVE_DATA_DIR = config.save_data_dir
        self.SAVE_BUF_CSVDATA_PATH = self.SAVE_DATA_DIR + "/" + "measurement_raw_data.csv"
        self.SEQUENCE_LENGTH = config.sequence_length # Windows size [s]
        # Buffer size is determined by the relation of sequence length and sampling frequency
        # Buffer secures data for SEQUENCE_LENGTH[s]
        self.MAX_DATA_BUF_LEN = self.SEQUENCE_LENGTH * self.SAMPLING_FREQUENCY_HZ
        self.FPASS = config.filter_params.fpass
        self.FSTOP = config.filter_params.fstop
        self.GPASS = config.filter_params.gpass
        self.GSTOP = config.filter_params.gstop
        self.is_filter = config.filter_params.is_filter
        self.is_show_real_time_data = config.is_show_real_time_data
        self.TIMEZONE = config.timezone
        self.all_data_columns_list = ()
        for sensor_name in self.sensor_list:
            self.all_data_columns_list += tuple(self.config["sensors"][sensor_name]["data_columns"])            
            
        

        
        self.data_buffer = pd.DataFrame()  # data buffer
    
        for sensor_type in self.sensor_list:
            sensor_config = self.config.sensors[sensor_type]
            sensor_instance = SensorFactory.create_sensor(sensor_type, sensor_config)
            if sensor_instance:
                self.sensor_instances[sensor_type] = sensor_instance
                
                
        if os.path.exists(self.SAVE_BUF_CSVDATA_PATH):
            os.remove(self.SAVE_BUF_CSVDATA_PATH)
            print(f"File  '{self.SAVE_BUF_CSVDATA_PATH}' was deleted for initialization")                
    

    def get_sensor(self, sensor_type):
        """
        Retrieve the sensor instance corresponding to the specified sensor type.

        Args:
            sensor_type (str): The type of the sensor to retrieve.

        Returns:
            object: The sensor instance corresponding to the specified sensor type.
                    Returns None if the sensor type does not exist.
        """
        return self.sensor_instances.get(sensor_type)

    def collect_data(self):
        """
        Collect data from all sensors.

        This method iterates over all sensor instances and collects data from each sensor.
        The collected data is stored in a dictionary where the keys are sensor types and
        the values are the data collected from the corresponding sensors.

        Returns:
            dict: A dictionary containing the collected data from all sensors.
                The keys are sensor types and the values are the data from each sensor.

        Raises:
            Exception: If an error occurs while collecting data from any sensor, the exception
                    is caught and printed.
        """
        data = {}
        try:
            for sensor_type, sensor in self.sensor_instances.items():
                # get data from sensors
                data[sensor_type] = sensor.get_data_from_sensor()
            return data
        except Exception as e:
            print(e)
    
    

    def on_change_start_measurement(self):
        """
        Start the measurement process.

        This method sets the is_running flag to True, indicating that the measurement
        process should start.
        """
        self.is_running = True

    def on_change_stop_measurement(self):
        """
        Stop the measurement process.

        This method sets the is_running flag to False, indicating that the measurement
        process should stop.
        """
        self.is_running = False
        

    def filtering(self, df, labellist):
        """
        Apply a low-pass filter to the specified columns in the DataFrame.
    
        This method applies a Butterworth low-pass filter to each column specified
        in the labellist. The "Time" column should be excluded from the labellist
        as it is not needed for the computation.
    
        Args:
            df (pd.DataFrame): The input DataFrame containing the data to be filtered.
            labellist (list of str): A list of column names to be filtered. The "Time"
                                     column should not be included in this list.
    
        Returns:
            pd.DataFrame: A new DataFrame with the filtered data.
        """
        filtered_df = df.copy()
        for labelname in labellist:
            # Ensure the column is converted to a numpy array
            x = df[labelname].to_numpy()
            filtered_df[labelname] = butterlowpass(
                x=x,  # Correctly pass the numpy array as 'x'
                fpass=self.FPASS,
                fstop=self.FSTOP,
                gpass=self.GPASS,
                gstop=self.GSTOP,
                fs=self.SAMPLING_FREQUENCY_HZ,
                dt=self.SAMPLING_TIME,
                checkflag=False,
                labelname=labelname
            )
        return filtered_df

    def convert_dictdata(self, current_time, sensor_data_dict):
        """
        Convert nested dictionary data from multiple sensors into a single DataFrame.
    
        This method converts nested dictionary data obtained from multiple sensors
        into a single dictionary and then converts it into a pandas DataFrame. The
        current_time information is associated with the data.
    
        Args:
            current_time (float): The current time at which the data was obtained.
            sensor_data_dict (dict): A nested dictionary containing data from multiple sensors.
    
        Returns:
            pd.DataFrame: A DataFrame containing the converted data with the current time information.
        """
        converted_data = {'Time': current_time}
        for sensor, data in sensor_data_dict.items():
            converted_data.update(data)
        
        converted_data = pd.DataFrame([converted_data])
        
        return converted_data



    async def update_data_buffer(self, dict_data):
        """
        Add data from sensors to the buffer and save it if necessary.
    
        This method adds the provided sensor data to the internal buffer. If the buffer
        exceeds the specified maximum length, the oldest data is saved to a CSV file
        and removed from the buffer.
    
        Args:
            dict_data (dict): The data from sensors to be added to the buffer.
        """
        
        # Add data to the buffer
        self.data_buffer = pd.concat([self.data_buffer, dict_data], ignore_index=True)
    
        # If the buffer exceeds the specified length, save the oldest data
        if len(self.data_buffer) > self.MAX_DATA_BUF_LEN:
            # Save the oldest data to a CSV file
            old_data = self.data_buffer.head(self.MAX_DATA_BUF_LEN)
            
            await self.save_data(old_data, self.SAVE_BUF_CSVDATA_PATH)
            
            # Update the buffer
            self.data_buffer = self.data_buffer.tail(len(self.data_buffer) - self.MAX_DATA_BUF_LEN)        
    
    
    
    async def save_data_async(self, df, path):
        """
        Save the DataFrame to a CSV file asynchronously.
    
        This method uses asyncio.to_thread to run the synchronous to_csv method
        in a separate thread, allowing it to be handled asynchronously.
    
        Args:
            df (pd.DataFrame): The DataFrame to be saved.
            path (str): The file path where the DataFrame should be saved.
        """
        if not os.path.isfile(path):
            await asyncio.to_thread(df.to_csv, path, sep=',', encoding='utf-8', index=False, header=True, mode='w')
        else:
            await asyncio.to_thread(df.to_csv, path, sep=',', encoding='utf-8', index=False, header=False, mode='a')
    
    async def save_data(self, df, path):
        """
        Save the DataFrame to a CSV file asynchronously.
    
        This method calls save_data_async to save the DataFrame to a CSV file
        asynchronously.
    
        Args:
            df (pd.DataFrame): The DataFrame to be saved.
            path (str): The file path where the DataFrame should be saved.
        """
        await self.save_data_async(df, path)
        


    async def finish_measurement_and_save_data(self):
        """
        Finish the measurement process and save the data.

        This method finalizes the measurement process by saving the buffered data
        to a CSV file. It also applies filtering if specified and saves the filtered
        data to a separate CSV file. The method handles time zone settings and
        generates a timestamp for the file names.

        The buffered data is saved to a temporary CSV file, which is then read back
        and saved to a final file path with a timestamp. If filtering is enabled,
        the filtered data is also saved. The temporary CSV file is deleted after
        the data is saved.

        Raises:
            Exception: If an error occurs during the file operations.
        """
        t_delta = datetime.timedelta(hours=9)
        TIMEZONE = datetime.timezone(t_delta, self.TIMEZONE)# You have to set your timezone
        now = datetime.datetime.now(TIMEZONE)
        timestamp = now.strftime('%Y%m%d%H%M%S')
        final_file_path = self.SAVE_BUF_CSVDATA_PATH.replace(self.SAVE_BUF_CSVDATA_PATH.split('/')[-1], 
                                                   timestamp + "/" + timestamp + '_' + 
                                                   self.SAVE_BUF_CSVDATA_PATH.split('/')[-1])
        await self.save_data_async(self.data_buffer, self.SAVE_BUF_CSVDATA_PATH)
        raw_df = pd.read_csv(self.SAVE_BUF_CSVDATA_PATH, header=0)
        os.makedirs(self.SAVE_DATA_DIR + "/" + timestamp, exist_ok=True)
        raw_df.to_csv(final_file_path, sep=',', encoding='utf-8', index=False, header=True)
        

        if self.is_filter:
            filt_df = self.filtering(df=raw_df, labellist=raw_df.columns[1:])
            filt_df.to_csv(final_file_path.replace('_raw_data.csv', '_filt_data.csv'), sep=',', encoding='utf-8', index=False, header=True)

        if os.path.exists(self.SAVE_BUF_CSVDATA_PATH):
            os.remove(self.SAVE_BUF_CSVDATA_PATH)
            print(f"File  '{self.SAVE_BUF_CSVDATA_PATH}' was deleted")
        else:
            print(f"File '{self.SAVE_BUF_CSVDATA_PATH}' is not existed")





        
async def sensor_fusion_main():
    """
    Main function for sensor fusion.

    This function initializes the sensor fusion process, starts the measurement loop,
    collects data from multiple sensors, updates the data buffer, and handles real-time
    data display. It also calculates and prints the sampling delay and reliability rate
    upon termination.

    The main loop runs until the measurement process is stopped, either by an exception
    or a keyboard interrupt.

    Raises:
        Exception: If an error occurs during the measurement process, it is caught and printed.
        KeyboardInterrupt: If a keyboard interrupt occurs, the measurement process is stopped
                           and the data is saved.

    """
    print("Start sensor fusion main")
    config = config_manager.load_config(config_path)
    sensors = Sensors(config["master"])
    print("Called an instance of Sensors class")
    
    # sensors.start_all_measurements()
    sampling_counter = 0
    current_time = 0
    #sensors.is_running = True
    sensors.on_change_start_measurement()
    """
    計測メインループ
    実行時間：最大0.04sほど(is_show_real_time_data==True)
    """
    try:
        main_loop_start_time = None
        while sensors.is_running:
            iteration_start_time = perf_counter() # Start time of each iteration
            
            if main_loop_start_time is None:
                    main_loop_start_time = iteration_start_time  # initialize main loop start time
            
            current_time = perf_counter() - main_loop_start_time # Current time
            
            data = sensors.collect_data() # Get data from sensors                                        
            sampling_counter += 1 # Num of sampling
            
            converted_data = sensors.convert_dictdata(current_time, data) # Convert data to dataframe format
            # Update the data buffer. If it reaches the buffer limit, write the data to a CSV file.
            await sensors.update_data_buffer(converted_data)
            # Display data in real time. This process is executed on additional thread.
            if sensors.is_show_real_time_data:
                formatted_data = format_sensor_fusion_data(data, sensors.all_data_columns_list)    
                print("--------------------------------------------------------------------")
                print("Current Time is: {:.3f}".format(current_time))
                print(formatted_data)
            
            # Wait based on the sampling interval and execution time to maintain the sampling frequency.
            iteration_end_time = perf_counter()
            iteration_duration = iteration_end_time - iteration_start_time 
            print("Iteration duration is: {0} [s]".format(iteration_duration))
            sleep_time = max(0, sensors.SAMPLING_TIME - iteration_duration)
            if sleep_time > 0:
                wait_process(sleep_time)
    
    except Exception as e:
        print(e)
    
    except KeyboardInterrupt:
        sensors.on_change_stop_measurement()
        print("KeyboardInterrupt")
        await sensors.finish_measurement_and_save_data()
        
    finally:
        print("finish")
         # Compute delay of sampling
        main_loop_end_time = perf_counter() - main_loop_start_time
        print("Program terminated")
        print("main loop is ended. current time is: {:.3f}".format(current_time))
        print("main loop is ended. end time is: {:.3f}".format(main_loop_end_time))
        print("sampling num is: {}".format(sampling_counter))
        
        
        
        # Compute ideal sampliing time
        ideal_time = ((sampling_counter - 1) / sensors.SAMPLING_FREQUENCY_HZ)
        # Cpmpute a delay
        delay_time = current_time - ideal_time
        # reliability rate
        sampling_reliability_rate = (delay_time / (sampling_counter / sensors.SAMPLING_FREQUENCY_HZ)) * 100
        
        
        print("sampling delay is: {:.3f} s".format(delay_time))
        print("sampling delay rate is: {:.3f} %".format(sampling_reliability_rate))


if __name__ == '__main__':
    asyncio.run(sensor_fusion_main())
