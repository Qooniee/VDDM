import os
import sys
import importlib

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from config import config_manager

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
    def __init__(self):
        self.config = config_manager.load_config(config_path)
        self.sensor_list = list(self.config.sensors.keys())
        self.sensor_instances = {}
        
        for sensor_type in self.sensor_list:
            sensor_config = getattr(self.config.sensors, sensor_type)
            sensor_instance = SensorFactory.create_sensor(sensor_type, sensor_config)
            if sensor_instance:
                self.sensor_instances[sensor_type] = sensor_instance

    def get_sensor(self, sensor_type):
        return self.sensor_instances.get(sensor_type)

def sensor_fusion_main():
    print("Start sensor fusion main")
    sensors = Sensors()
    print("Called an instance of Sensors class")
    
    for sensor_type in sensors.sensor_list:
        print(f"Sensor: {sensor_type}")
        sensor = sensors.get_sensor(sensor_type)
        if sensor:
            print(f"  Instance: {sensor}")
            # ここでセンサー固有のメソッドを呼び出すことができます
            # 例: sensor.start_measurement()
    
    print()

if __name__ == '__main__':
    sensor_fusion_main()