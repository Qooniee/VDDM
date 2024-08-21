from fusion.sensor_fusion import Sensors
from config.config_manager import load_config
from utils.tools import perf_counter
from utils.visualize_data import format_sensor_fusion_data
import sys
import os
config_path = "config/measurement_system_config.yaml"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.tools import wait_process


is_running = False


def on_click_stop_measurement(sensors):
    sensors.is_running = False

def on_click_start_measurement(sensors):
    sensors.is_running = True

def measurement(sensors, config):
    print("measurement")
    print("Start sensor fusion main")
    print("Called an instance of Sensors class")
    
    # sensors.start_all_measurements()
    start_time = perf_counter()
    sampling_counter = 0
    sensors.is_running = True
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
    
    


def measurement_ctrl_main_loop():
    print("Measurement main loop...")
    config = load_config(config_path)
    sensors = Sensors(config["master"])
    measurement(sensors, config)
 
    

        
    

def main():
    print()
    print("Start sensor fusion main")
    measurement_ctrl_main_loop()
    

if __name__ == '__main__':
    print("Start Main function...")
    main()
    