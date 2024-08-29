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
SAVE_INTERVAL = 10  # Save interval in seconds


class SensorFactory:
    @staticmethod
    def create_sensor(sensor_type, config):
        try:
            # センサータイプに基づいてモジュールをインポート
            module = importlib.import_module(f"fusion.sensors.{sensor_type}_measurement")
            # センサークラスを取得
            sensor_class = getattr(module, f"{sensor_type.upper()}")
            # センサーインスタンスを作成して返す
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
        self.SEQUENCE_LENGTH = config.sequence_length
        self.MAX_DATA_BUF_LEN = self.SEQUENCE_LENGTH // self.SAMPLING_FREQUENCY_HZ
        self.SAVE_INTERVAL = config.save_interval
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
            
        

        
        self.data_buffer = pd.DataFrame()  # データを保持するための空のDataFrame
    
        for sensor_type in self.sensor_list:
            sensor_config = self.config.sensors[sensor_type]
            sensor_instance = SensorFactory.create_sensor(sensor_type, sensor_config)
            if sensor_instance:
                self.sensor_instances[sensor_type] = sensor_instance
                
                
        if os.path.exists(self.SAVE_BUF_CSVDATA_PATH):
            os.remove(self.SAVE_BUF_CSVDATA_PATH)
            print(f"File  '{self.SAVE_BUF_CSVDATA_PATH}' was deleted for initialization")                
    

    def get_sensor(self, sensor_type):
        return self.sensor_instances.get(sensor_type)
    
    def collect_data(self):
        """全てのセンサーからデータを収集し、動的に辞書に格納する"""
        data = {}
        try:
            for sensor_type, sensor in self.sensor_instances.items():
                # 各センサーからデータを取得し、辞書に格納
                data[sensor_type] = sensor.get_data_from_sensor()
            return data
        except Exception as e:
            print(e)
    
    

    
    
    def on_change_start_measurement(self):
        self.is_running = True
    
    def on_change_stop_measurement(self):
        self.is_running = False



    def filtering(self, df, labellist):
        """
        Label list must dropped "Time" label.
        Filter function doesn't need "Time" for the computation.
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
        """_summary_
        複数のセンサから取得した入れ子辞書型データを
        一つの辞書データに変換する
        その後pandas dataframeに変換
        データを取得した際のcurrent_timeの情報を紐づける

        Args:
            sensor_data_dict (_type_): _description_

        Returns:
            _type_: _description_
        """
        converted_data = {'Time': current_time}
        for sensor, data in sensor_data_dict.items():
            converted_data.update(data)
        
        converted_data = pd.DataFrame([converted_data])
        
        return converted_data



    async def update_data_buffer(self, dict_data):
        """センサーからのデータをバッファに追加し、必要に応じて保存する
        
        Args:
            sensor_data_dict (dict): センサーからのデータ
        """
        
        # バッファに追加
        self.data_buffer = pd.concat([self.data_buffer, dict_data], ignore_index=True)

        # バッファが指定した長さを超えている場合、古いデータを保存
        if len(self.data_buffer) > self.MAX_DATA_BUF_LEN:
            # 古いデータをCSVに保存
            old_data = self.data_buffer.head(self.MAX_DATA_BUF_LEN)
            
            await self.save_data(old_data, self.SAVE_BUF_CSVDATA_PATH)
            
            # バッファを更新
            self.data_buffer = self.data_buffer.tail(len(self.data_buffer) - self.MAX_DATA_BUF_LEN)
        
    
    
    
    # asyncio.to_threadにより同期関数を別スレッドで実行し、その結果を非同期で扱う
    async def save_data_async(self, df, path):
        if not os.path.isfile(path):
            await asyncio.to_thread(df.to_csv, path, sep=',', encoding='utf-8', index=False, header=True, mode='w')
        else:
            await asyncio.to_thread(df.to_csv, path, sep=',', encoding='utf-8', index=False, header=False, mode='a')

    
    async def save_data(self, df, path):
        """非同期でデータをCSVファイルに保存する"""
        await self.save_data_async(df, path)
        


    async def finish_measurement_and_save_data(self):
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
        main_loop_start_time = perf_counter()# main loopの開始時間
        while sensors.is_running:
            iteration_start_time = perf_counter() #各イテレーションの開始時間
            current_time = perf_counter() - main_loop_start_time # main loopの実行からの経過時間(Current time)
            sampling_counter += 1 # サンプリングの回数
            data = sensors.collect_data() # 複数のセンサからデータの取得                                        
            # print("Current Time is: {:.3f}".format(current_time))
            converted_data = sensors.convert_dictdata(current_time, data) # 複数のセンサから取得したデータをdataframeに変換
            # 複数のセンサから取得したデータを変換したdataframeをバッファに追加
            # さらにバッファが一定量に達したらcsvファイルに保存する
            await sensors.update_data_buffer(converted_data)
            if sensors.is_show_real_time_data:
                formatted_data = format_sensor_fusion_data(data, sensors.all_data_columns_list)
                # 現在時間  
                print("--------------------------------------------------------------------")
                print("Current Time is: {:.3f}".format(current_time))
                print(formatted_data)
             
            # サンプリング間隔と処理の実行時間に応じてサンプリング周波数を満たすように待機
            iteration_end_time = perf_counter() # イテレーションの終了時間
            iteration_duration = iteration_end_time - iteration_start_time # 1イテレーションで経過した時間
            print("Iteration duration is: {0} [s]".format(iteration_duration))
            sleep_time = max(0, sensors.SAMPLING_TIME - iteration_duration) # サンプリング周波数(())
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
         # サンプリングの個数と現在時間からサンプリングの遅れを計算
        main_loop_end_time = perf_counter() - main_loop_start_time
        print("Program terminated")
        print("main loop is ended. current time is: {:.3f}".format(current_time))
        print("main loop is ended. end time is: {:.3f}".format(main_loop_end_time))
        print("sampling num is: {}".format(sampling_counter))# 0基準であるためcurrent_time + 1個のサンプルになる
        
        
        
        # 理想的なサンプリング時間の計算
        ideal_time = ((sampling_counter - 1) / sensors.SAMPLING_FREQUENCY_HZ)
        # 遅れの計算
        delay_time = current_time - ideal_time
        # 遅れの割合をサンプリング時間で割った値を信頼性率とする
        sampling_reliability_rate = (delay_time / (sampling_counter / sensors.SAMPLING_FREQUENCY_HZ)) * 100
        
        
        print("sampling delay is: {:.3f} s".format(delay_time))
        print("sampling delay rate is: {:.3f} %".format(sampling_reliability_rate))


if __name__ == '__main__':
    asyncio.run(sensor_fusion_main())
