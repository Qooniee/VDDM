import os
import sys
import importlib
from time import perf_counter

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from config import config_manager
from utils.tools import wait_process
config_path = os.path.join(parent_dir, 'config', 'measurement_system_config.yaml')

class SensorFactory:
    @staticmethod
    def create_sensor(sensor_type, config):
        try:
            # センサータイプに基づいてモジュールをインポート
            module = importlib.import_module(f"sensors.{sensor_type}_measurement")
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
        self.sensor_list = list(self.config.sensors.keys())
        self.sensor_instances = {}
        self.is_running = False
        
        
        self.SAMPLING_FREQUENCY_HZ = config.sampling_frequency_hz
        self.SAMPLING_TIME = 1 / self.SAMPLING_FREQUENCY_HZ
        self.SAVE_DATA_PATH = config.save_data_path
        self.SEQUENCE_LENGTH = config.sequence_length
        self.INIT_LEN = self.SEQUENCE_LENGTH // self.SAMPLING_FREQUENCY_HZ
        self.SAVE_INTERVAL = config.save_interval
        self.FPASS = config.filter_params.fpass
        self.FSTOP = config.filter_params.fstop
        self.GPASS = config.filter_params.gpass
        self.GSTOP = config.filter_params.gstop
        self.is_filter = config.filter_params.is_filter
        self.is_show_real_time_data = config.is_show_real_time_data
        
        
        
        
        
        for sensor_type in self.sensor_list:
            sensor_config = self.config.sensors[sensor_type]
            sensor_instance = SensorFactory.create_sensor(sensor_type, sensor_config)
            if sensor_instance:
                self.sensor_instances[sensor_type] = sensor_instance

    def get_sensor(self, sensor_type):
        return self.sensor_instances.get(sensor_type)
    
    def collect_data(self):
        """全てのセンサーからデータを収集し、動的に辞書に格納する"""
        data = {}
        for sensor_type, sensor in self.sensor_instances.items():
            # 各センサーからデータを取得し、辞書に格納
            data[sensor_type] = sensor.get_data_from_sensor()
        return data
    
    def start_all_measurements(self):
        self.is_running = True

def format_sensor_fusion_data(data, labels):
    formatted_str = ""
    if isinstance(data, dict):
        for label in labels:
            # 各センサーからラベルに対応するデータを検索
            value = "None"
            for sensor_data in data.values():
                if isinstance(sensor_data, dict):
                    value = sensor_data.get(label, "None")
                    if value != "None":
                        break
            # データが存在する場合、フォーマットして表示
            if value != "None":
                value = f"{value:.4f}"
            formatted_str += f"{label}: {value} / "
    return formatted_str.rstrip(" / ")





def sensor_fusion_main():
    print("Start sensor fusion main")
    config = config_manager.load_config(config_path)
    sensors = Sensors(config["master"])
    print("Called an instance of Sensors class")
    
    sensors.start_all_measurements()
    start_time = perf_counter()
    sampling_counter = 0
    try:
        main_loop_start_time = perf_counter()
        while sensors.is_running:
            iteration_start_time = perf_counter()
            current_time = perf_counter() - start_time
            sampling_counter += 1
            data = sensors.collect_data()
            
            if sensors.is_show_real_time_data:
                all_sensor_data_columns = []
                for key in sensors.config.sensors.keys():
                    all_sensor_data_columns += sensors.config.sensors[key].data_columns
                formatted_data = format_sensor_fusion_data(data, all_sensor_data_columns)
                # 現在時間    
                print("--------------------------------------------------------------------")
                print("Current Time is: {:.3f}".format(current_time))
                print(formatted_data)
            # サンプリング間隔と処理の実行時間に応じてサンプリング周波数を満たすように待機
            elapsed_time = perf_counter() - iteration_start_time
            sleep_time = sensors.SAMPLING_TIME - elapsed_time
            if sleep_time > 0:
                wait_process(sleep_time)
    
            
            
            
            
    except Exception as e:
        print(e)
    
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        
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


    
    print()

if __name__ == '__main__':
    sensor_fusion_main()
