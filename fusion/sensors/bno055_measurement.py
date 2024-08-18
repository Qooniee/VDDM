import time
import numpy as np
import adafruit_bno055
import board
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)

from config.config_manager import load_config
config_path = os.path.join(parent_dir, 'config', 'measurement_system_config.yaml')


class BNO055:
    def __init__(self, config):
        self.COLUMNS = config.data_columns    
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
        self.Isfilter = config.filter_params.is_filter
        
        self.IsStart = False
        self.IsStop = True
        self.Is_show_real_time_data = config.is_show_real_time_data 

        i2c_instance = board.I2C()
        self.bno055_sensor = adafruit_bno055.BNO055_I2C(i2c_instance)

    def calibration(self):
        print("Start calibration!")
        while not self.bno055_sensor.calibrated:
            print('SYS: {0}, Gyro: {1}, Accel: {2}, Mag: {3}'.format(*(self.bno055_sensor.calibration_status)))
            time.sleep(1)

    def calcEulerfromQuaternion(self, _w, _x, _y, _z):
        try:
            sqw = _w ** 2
            sqx = _x ** 2
            sqy = _y ** 2
            sqz = _z ** 2
            COEF_EULER2DEG = 57.2957795131
            yaw = COEF_EULER2DEG * (np.arctan2(2.0 * (_x * _y + _z * _w), (sqx - sqy - sqz + sqw)))  # Yaw
            pitch = COEF_EULER2DEG * (np.arcsin(-2.0 * (_x * _z - _y * _w) / (sqx + sqy + sqz + sqw)))  # Pitch
            roll = COEF_EULER2DEG * (np.arctan2(2.0 * (_y * _z + _x * _w), (-sqx - sqy + sqz + sqw)))  # Roll
            return roll, pitch, yaw
        except Exception as e:
            print(f"Error in calcEulerfromQuaternion: {e}")
            return 0.0, 0.0, 0.0

    def get_data_from_BNO055(self):
        # データを取得
        euler_z, euler_y, euler_x = [val for val in self.bno055_sensor.euler]  # X: yaw, Y: pitch, Z: roll
        gyro_x, gyro_y, gyro_z = [val for val in self.bno055_sensor.gyro]  # Gyro[rad/s]
        linear_accel_x, linear_accel_y, linear_accel_z = [val for val in self.bno055_sensor.linear_acceleration]  # Linear acceleration[m/s^2]
        quaternion_1, quaternion_2, quaternion_3, quaternion_4 = [val for val in self.bno055_sensor.quaternion]  # Quaternion
        quat_roll, quat_pitch, quat_yaw = self.calcEulerfromQuaternion(quaternion_1, quaternion_2, quaternion_3, quaternion_4)  # Cal Euler angle from quaternion
        magnetic_x, magnetic_y, magnetic_z = [val for val in self.bno055_sensor.magnetic]  # Magnetic field
        calibstat_sys, calibstat_gyro, calibstat_accel, calibstat_mag = [val for val in self.bno055_sensor.calibration_status]  # Status of calibration

        # データの変換マップ
        conversion_map = {
            "linear_accel_x": lambda x: x,
            "linear_accel_y": lambda y: y,
            "linear_accel_z": lambda z: z,
            "gyro_x": lambda x: x,
            "gyro_y": lambda y: 0.0 if y is None else y,
            "gyro_z": lambda z: z,
            "euler_x": lambda x: 0.0 if x is None else (-1) * x,
            "euler_y": lambda y: 0.0 if y is None else (-1) * y,
            "euler_z": lambda z: z,
            "quat_roll": lambda roll: roll,
            "quat_pitch": lambda pitch: pitch,
            "quat_yaw": lambda yaw: yaw,
            "quaternion_1": lambda q1: q1,
            "quaternion_2": lambda q2: q2,
            "quaternion_3": lambda q3: q3,
            "quaternion_4": lambda q4: q4,
            "magnetic_x": lambda mx: mx,
            "magnetic_y": lambda my: my,
            "magnetic_z": lambda mz: mz,
            "calibstat_sys": lambda sys: sys,
            "calibstat_gyro": lambda gyro: gyro,
            "calibstat_accel": lambda accel: accel,
            "calibstat_mag": lambda mag: mag
        }

        # データを辞書にまとめる
        data_dict = {
            "linear_accel_x": linear_accel_x,
            "linear_accel_y": linear_accel_y,
            "linear_accel_z": linear_accel_z,
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z,
            "euler_x": euler_x,
            "euler_y": euler_y,
            "euler_z": euler_z,
            "quat_roll": quat_roll,
            "quat_pitch": quat_pitch,
            "quat_yaw": quat_yaw,
            "quaternion_1": quaternion_1,
            "quaternion_2": quaternion_2,
            "quaternion_3": quaternion_3,
            "quaternion_4": quaternion_4,
            "magnetic_x": magnetic_x,
            "magnetic_y": magnetic_y,
            "magnetic_z": magnetic_z,
            "calibstat_sys": calibstat_sys,
            "calibstat_gyro": calibstat_gyro,
            "calibstat_accel": calibstat_accel,
            "calibstat_mag": calibstat_mag
        }

        # 設定されたデータカラムのみを返す
        return tuple(conversion_map[column](data_dict[column]) for column in self.COLUMNS)


def format_data_for_display(data, labels):
    formatted_str = ""
    for label, value in zip(labels, data):
        if value is None:
            value = "None"
        else:
            value = f"{value:.4f}"
        formatted_str += f"{label}: {value} / "
    return formatted_str.rstrip(" / ")


def test_main():
    from utils.tools import wait_process
    from time import perf_counter
    import matplotlib.pyplot as plt
    
    print("Main start")
    
    config = load_config(config_path)
    meas_bno055 = BNO055(config.sensors['bno055'])
    
    start_time = perf_counter()
    sampling_counter = 0
    # 0基準のため最初のサンプリングは0秒に紐づけられる
    try:
        main_loop_start_time = perf_counter()
        while True:
            iteration_start_time = perf_counter()
            
            # データ取得処理
            data = meas_bno055.get_data_from_BNO055()
            current_time = perf_counter() - start_time
            sampling_counter += 1
    
            if meas_bno055.Is_show_real_time_data:
                formatted_data = format_data_for_display(data, meas_bno055.COLUMNS)
                # 現在時間    
                print("--------------------------------------------------------------------")
                print("Current Time is: {:.3f}".format(current_time))
                print(formatted_data)
            
            # サンプリング間隔と処理の実行時間に応じてサンプリング周波数を満たすように待機
            elapsed_time = perf_counter() - iteration_start_time
            sleep_time = meas_bno055.SAMPLING_TIME - elapsed_time
            if sleep_time > 0:
                wait_process(sleep_time)
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    
    finally:
        # サンプリングの個数と現在時間からサンプリングの遅れを計算
        main_loop_end_time = perf_counter() - main_loop_start_time
        print("Program terminated")
        print("main loop is ended. current time is: {:.3f}".format(current_time))
        print("main loop is ended. end time is: {:.3f}".format(main_loop_end_time))
        print("sampling num is: {}".format(sampling_counter))# 0基準であるためcurrent_time + 1個のサンプルになる
        
        
        
        # 理想的なサンプリング時間の計算
        ideal_time = ((sampling_counter - 1) / meas_bno055.SAMPLING_FREQUENCY_HZ)
        # 遅れの計算
        delay_time = current_time - ideal_time
        # 遅れの割合をサンプリング時間で割った値を信頼性率とする
        sampling_reliability_rate = (delay_time / (sampling_counter / meas_bno055.SAMPLING_FREQUENCY_HZ)) * 100
        
        
        print("sampling delay is: {:.3f} s".format(delay_time))
        print("sampling delay rate is: {:.3f} %".format(sampling_reliability_rate))
        
        
        
        



if __name__ == '__main__':
    from time import perf_counter
    test_main()