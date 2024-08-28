from time import perf_counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

def disp_historicalgraph(df, mode="gyro"):
    """
    Displays a historical graph for the specified sensor data.

    This function creates a series of subplots to visualize the time series data for different
    sensor measurements. Depending on the mode specified, it will plot the data for gyro,
    Euler angles, linear acceleration, or quaternion angles.

    Args:
        df (pandas.DataFrame): The DataFrame containing the sensor data. It must include 
                               'Time' and the corresponding sensor columns depending on the mode.
        mode (str, optional): The type of data to plot. Can be "gyro", "euler", 
                              "linear_accel", or "quat_angle". Defaults to "gyro".

    Returns:
        None: The function modifies the current figure and axes directly.
    """
    fig, ax = plt.subplots(1, 3, figsize=(8, 3), tight_layout=True)
    if mode == "gyro":
        ax[0].plot(df['Time'], df['gyro_x'], marker='*')
        ax[1].plot(df['Time'], df['gyro_y'], marker='*')
        ax[2].plot(df['Time'], df['gyro_z'], marker='*')
        ax[0].set_xlabel('Time[s]')
        ax[0].set_ylabel('Gyro_x(Roll Rate)[rad/s]')
        ax[1].set_xlabel('Time[s]')
        ax[1].set_ylabel('Gyro_y(Pitch Rate)[rad/s]')
        ax[2].set_xlabel('Time[s]')
        ax[2].set_ylabel('Gyro_z(Yaw Rate)[rad/s]')

    if mode == "euler":
        ax[0].plot(df['Time'], df['euler_x'], marker='*')
        ax[1].plot(df['Time'], df['euler_y'], marker='*')
        ax[2].plot(df['Time'], df['euler_z'], marker='*')
        ax[0].set_xlabel('Time[s]')
        ax[0].set_ylabel('Roll Angle[deg]')
        ax[1].set_xlabel('Time[s]')
        ax[1].set_ylabel('Pitch Angle[deg]')
        ax[2].set_xlabel('Time[s]')
        ax[2].set_ylabel('Yaw Angle[deg]')

    if mode == "linear_accel":
        ax[0].plot(df['Time'], df['linear_accel_x'], marker='*')
        ax[1].plot(df['Time'], df['linear_accel_y'], marker='*')
        ax[2].plot(df['Time'], df['linear_accel_z'], marker='*')
        ax[0].set_xlabel('Time[s]')
        ax[0].set_ylabel('linear_accel_x[m/s^2]')
        ax[1].set_xlabel('Time[s]')
        ax[1].set_ylabel('linear_accel_y[m/s^2]')
        ax[2].set_xlabel('Time[s]')
        ax[2].set_ylabel('linear_accel_z[m/s^2]')

    if mode == "quat_angle":
        ax[0].plot(df['Time'], df['quat_roll'], marker='*')
        ax[1].plot(df['Time'], df['quat_pitch'], marker='*')
        ax[2].plot(df['Time'], df['quat_yaw'], marker='*')
        ax[0].set_xlabel('Time[s]')
        ax[0].set_ylabel('quat_roll[deg]')
        ax[1].set_xlabel('Time[s]')
        ax[1].set_ylabel('quat_pitch[deg]')
        ax[2].set_xlabel('Time[s]')
        ax[2].set_ylabel('quat_yaw[deg]')

    return


def format_sensor_fusion_data(data, labels):
    """
    Formats sensor fusion data into a readable string.

    This function takes in a dictionary of sensor data and a list of labels,
    then formats each label's corresponding value into a string with 4 decimal
    places. If a value is None or NaN, it is appropriately labeled in the output.

    Args:
        data (dict or list): The sensor data, either as a dictionary or a list. 
                             If it's a dictionary, the values should be either 
                             floats or nested dictionaries.
        labels (list): A list of labels that correspond to the data keys. These 
                       labels will be used in the formatted output.

    Returns:
        str: A formatted string that displays each label and its corresponding value.
    """
    formatted_str = ""
    if isinstance(data, dict):
        for label in labels:
            value = "None"
            for sensor_data in data.values():
                if isinstance(sensor_data, dict):
                    value = sensor_data.get(label, "None")
                    if value != "None":
                        break

            if value is None:
                formatted_str += f"{label}: None / "
            elif isinstance(value, float) and math.isnan(value):
                formatted_str += f"{label}: NaN / "
            else:
                try:
                    formatted_value = f"{float(value):.4f}"
                except (ValueError, TypeError):
                    formatted_str += f"{label}: {value} / "
                else:
                    formatted_str += f"{label}: {formatted_value} / "
    else:
        for label, value in zip(labels, data):
            if value is None:
                formatted_str += f"{label}: None / "
            elif isinstance(value, float) and math.isnan(value):
                formatted_str += f"{label}: NaN / "
            else:
                try:
                    formatted_value = f"{float(value):.4f}"
                except (ValueError, TypeError):
                    formatted_str += f"{label}: {value} / "
                else:
                    formatted_str += f"{label}: {formatted_value} / "

    return formatted_str.rstrip(" / ")
