from time import perf_counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def wait_process(wait_sec):
    until = perf_counter() + wait_sec
    while perf_counter() < until:
        pass
    return



def disp_historicalgraph(df, mode="gyro"):

    fig, ax = plt.subplots(1, 3, figsize=(8,3), tight_layout=True)
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
                    
    #plt.show()
    #fig = plt.gcf()
    return



import math

def format_sensor_fusion_data(data, labels):
    formatted_str = ""
    if isinstance(data, dict):
        for label in labels:
            value = "None"
            for sensor_data in data.values():
                if isinstance(sensor_data, dict):
                    value = sensor_data.get(label, "None")
                    if value != "None":
                        break
            
            # None または NaN、数値の場合に応じてフォーマット
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