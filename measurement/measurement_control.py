import asyncio
import sys
import os

# 親ディレクトリをパスに追加
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from fusion.sensor_fusion import Sensors
from utils.tools import perf_counter, wait_process
from utils.visualize_data import format_sensor_fusion_data
from config.config_manager import load_config

class MeasurementControl:
    def __init__(self, config_path):
        self.is_running = False
        self.sensors = Sensors(load_config(config_path)["master"])  # センサーを初期化
        self.loop = asyncio.new_event_loop()  # メインスレッド以外で使用するための新しいイベントループ
        self.config_path = config_path
    
    async def start_measurement(self):
        if not self.is_running:
            self.is_running = True
            print("Measurement started.")
            await self.measurement(self.sensors, load_config(self.config_path))
        else:
            print("Measurement is already running.")
    
    def stop_measurement(self):
        if self.is_running:
            self.is_running = False
            print("Measurement stopped.")
        else:
            print("Measurement is not running.")
    
    async def save_measurement_data(self):
        print("pressed save button")
        await self.sensors.finish_measurement_and_save_data()

    async def measurement(self, sensors, config):
        print("Measurement function called.")
        start_time = perf_counter()
        sampling_counter = 0
        try:
            while self.is_running:
                iteration_start_time = perf_counter()
                current_time = perf_counter() - start_time
                sampling_counter += 1
                data = sensors.collect_data()
                
                if sensors.is_show_real_time_data:
                    all_sensor_data_columns = []
                    for key in sensors.config.sensors.keys():
                        all_sensor_data_columns += sensors.config.sensors[key].data_columns
                        formatted_data = format_sensor_fusion_data(data, all_sensor_data_columns)

                    print("--------------------------------------------------------------------")
                    print("Current Time is: {:.3f}".format(current_time))
                    print(formatted_data)
                
                converted_data = sensors.convert_dictdata(current_time, data)
                await sensors.update_data_buffer(converted_data)
                
                elapsed_time = perf_counter() - iteration_start_time
                sleep_time = sensors.SAMPLING_TIME - elapsed_time
                if sleep_time > 0:
                    wait_process(sleep_time)
        except Exception as e:
            print(e)
    
    def run_async(self, coroutine):
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        else:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(coroutine)
    
    
    def cleanup(self):
        """クリーンアップ処理を定義します。"""
        if self.is_running:
            self.stop_measurement()
        print("Cleanup completed.")