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
        self.SAVE_DATA_DIR = config.save_data_dir
        self.SEQUENCE_LENGTH = config.sequence_length
        self.SAVE_INTERVAL = config.save_interval
        self.FPASS = config.filter_params.fpass
        self.FSTOP = config.filter_params.fstop
        self.GPASS = config.filter_params.gpass
        self.GSTOP = config.filter_params.gstop
        self.Isfilter = config.filter_params.is_filter
        
        self.IsStart = False
        self.IsStop = True
        self.Is_show_real_time_data = config.is_show_real_time_data 

        i2c_instance = board.I2C() # Create i2c instance
        self.bno055_sensor = adafruit_bno055.BNO055_I2C(i2c_instance) # create BNO055_I2C instance

    def calibration(self):
        print("Start calibration!")
        while not self.bno055_sensor.calibrated:
            print('SYS: {0}, Gyro: {1}, Accel: {2}, Mag: {3}'.format(*(self.bno055_sensor.calibration_status)))
            time.sleep(1)


    def calcEulerfromQuaternion(self, _w, _x, _y, _z):
        """
        Calculate Euler angles (roll, pitch, yaw) from quaternion components.

        This method converts quaternion components (_w, _x, _y, _z) into Euler angles
        (roll, pitch, yaw) in degrees. If any of the quaternion components are None,
        it returns (0.0, 0.0, 0.0) and prints an error message.

        Args:
            _w (float): The w component of the quaternion.
            _x (float): The x component of the quaternion.
            _y (float): The y component of the quaternion.
            _z (float): The z component of the quaternion.

        Returns:
            tuple: A tuple containing the roll, pitch, and yaw angles in degrees.
                If an error occurs, it returns (0.0, 0.0, 0.0) and prints an error message.
        """
        if None in (_w, _x, _y, _z):
            print(f"Error: One or more quaternion values are None: {_w}, {_x}, {_y}, {_z}")
            return 0.0, 0.0, 0.0
        
        try:
            sqw = _w ** 2
            sqx = _x ** 2
            sqy = _y ** 2
            sqz = _z ** 2
            COEF_EULER2DEG = 57.2957795131
            
            # Yaw
            term1 = 2.0 * (_x * _y + _z * _w)
            term2 = sqx - sqy - sqz + sqw
            yaw = np.arctan2(term1, term2)
            
            # Pitch
            term1 = -2.0 * (_x * _z - _y * _w)
            term2 = sqx + sqy + sqz + sqw
            pitch = np.arcsin(term1 / term2) if -1 <= term1 / term2 <= 1 else 0.0
            
            # Roll
            term1 = 2.0 * (_y * _z + _x * _w)
            term2 = -sqx - sqy + sqz + sqw
            roll = np.arctan2(term1, term2)
            
            return COEF_EULER2DEG * roll, COEF_EULER2DEG * pitch, COEF_EULER2DEG * yaw
        
        except Exception as e:
            print(f"Error in calcEulerfromQuaternion: {e}")
            return 0.0, 0.0, 0.0

    def get_data_from_sensor(self):
        """
        Retrieve data from the BNO055 sensor and return it as a dictionary.

        This method collects various sensor readings from the BNO055 sensor, including
        Euler angles, gyroscope data, linear acceleration, quaternion, magnetic field,
        and calibration status. It then constructs a dictionary with these values and
        returns only the columns specified in self.COLUMNS.

        Returns:
            dict: A dictionary containing the sensor data. Only the columns specified
                in self.COLUMNS are included in the returned dictionary.
        """
        # Get data
        euler_z, euler_y, euler_x = [val for val in self.bno055_sensor.euler]  # X: yaw, Y: pitch, Z: roll
        gyro_x, gyro_y, gyro_z = [val for val in self.bno055_sensor.gyro]  # Gyro[rad/s]
        linear_accel_x, linear_accel_y, linear_accel_z = [val for val in self.bno055_sensor.linear_acceleration]  # Linear acceleration[m/s^2]
        quaternion_1, quaternion_2, quaternion_3, quaternion_4 = [val for val in self.bno055_sensor.quaternion]  # Quaternion
        quat_roll, quat_pitch, quat_yaw = self.calcEulerfromQuaternion(quaternion_1, quaternion_2, quaternion_3, quaternion_4)  # Cal Euler angle from quaternion
        magnetic_x, magnetic_y, magnetic_z = [val for val in self.bno055_sensor.magnetic]  # Magnetic field
        calibstat_sys, calibstat_gyro, calibstat_accel, calibstat_mag = [val for val in self.bno055_sensor.calibration_status]  # Status of calibration

        
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

        return {column: data_dict[column] for column in self.COLUMNS if column in data_dict}


def format_sensor_data(data, labels):
    """
    Format sensor data into a string for display.

    This method takes a dictionary of sensor data and a list of labels, and formats
    the data into a string where each label is followed by its corresponding value.
    If a value is None, it is replaced with the string "None". Each label-value pair
    is separated by " / ".

    Args:
        data (dict): The sensor data to format.
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
    return formatted_str.rstrip(" / ")

def test_main():
    """
    Main function for testing sensor data collection and display.

    This function initializes the BNO055 sensor, starts a loop to collect data,
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
    meas_bno055 = BNO055(config.sensors['bno055'])
    
    start_time = perf_counter()
    sampling_counter = 0
    
    try:
        main_loop_start_time = perf_counter()
        while True:
            iteration_start_time = perf_counter()
            
            # Data acquisition process
            data = meas_bno055.get_data_from_sensor()
            current_time = perf_counter() - start_time
            sampling_counter += 1
    
            if meas_bno055.Is_show_real_time_data:
                formatted_data = format_sensor_data(data, meas_bno055.COLUMNS)
                # current time    
                print("--------------------------------------------------------------------")
                print("Current Time is: {:.3f}".format(current_time))
                print(formatted_data)
            
            # Wait to meet the sampling frequency based on the sampling interval and execution time
            elapsed_time = perf_counter() - iteration_start_time
            sleep_time = meas_bno055.SAMPLING_TIME - elapsed_time
            if sleep_time > 0:
                wait_process(sleep_time)
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    
    finally:
        # Calculate the sampling delay from the number of samples and the current time
        main_loop_end_time = perf_counter() - main_loop_start_time
        print("Program terminated")
        print("main loop is ended. current time is: {:.3f}".format(current_time))
        print("main loop is ended. end time is: {:.3f}".format(main_loop_end_time))
        print("sampling num is: {}".format(sampling_counter)) # Since it is 0-based, the number of samples is current_time + 1
        
        # Calculate the ideal sampling time
        ideal_time = ((sampling_counter - 1) / meas_bno055.SAMPLING_FREQUENCY_HZ)
        # Calculate the delay
        delay_time = current_time - ideal_time
        # The reliability rate is the delay divided by the sampling time
        sampling_reliability_rate = (delay_time / (sampling_counter / meas_bno055.SAMPLING_FREQUENCY_HZ)) * 100
        
        print("sampling delay is: {:.3f} s".format(delay_time))
        print("sampling delay rate is: {:.3f} %".format(sampling_reliability_rate))
        



if __name__ == '__main__':
    test_main()