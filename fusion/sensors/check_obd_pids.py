
import obd
import os
import time
from collections import deque
import numpy as np
import pandas as pd
import datetime
import asyncio
import scipy
from scipy import signal
import matplotlib as plt
import sys
from collections import defaultdict
import random
from obd import OBDCommand
from obd.utils import bytes_to_int
from obd.decoders import *
from obd.protocols import ECU

obd.logger.setLevel(obd.logging.DEBUG)

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)

from fusion.sensors.obdscanner_measurement import OBDSCANNER
from config.config_manager import load_config
config_path = os.path.join(parent_dir, 'config', 'measurement_system_config.yaml')

class Custom_OBD_Commands:
    def __init__(self):
        self.obd_command_map = {}
        self.define_custom_command()
        
    def define_custom_command(self): 

        def decode_steering_angle(data):
            """
            デコーダー関数：ステアリング角をデコードする。
            """
            if len(data) >= 3:
                # 例えば、最初の3バイトをステアリング角として解釈する例
                angle = int.from_bytes(data[:3], byteorder='big')
                return angle
            return None
        # コマンドの実行
        steering_angle_command = OBDCommand(
            name="Steering Angle", 
            desc="Steering Angle",
            command=b"0138",  # CAN ID 312 (16進数で0x138)
            _bytes=3,  # 返却されるデータのバイト数
            decoder=decode_steering_angle,  # デコーダー関数
            ecu=ECU.ALL,  # ECUの指定
            fast=True
        )
        

        
        vehicle_speed_command = OBDCommand(name="SPEED", 
                                            desc="Vehicle Speed",
                                            command=b"010D",                    # ServiceID 01とPID 0Dの結合-> 010D. 16進から2進変換する
                                            _bytes=3,                   # 返却されるデータのバイト数
                                            decoder=uas(0x09),              # データの単位などの変換で使う関数名 uas関数に0x09を渡す
                                            ecu=ECU.ENGINE,                 # Engine ECU
                                            fast=True
                                            )
        
        
        vehicle_engine_rpm = OBDCommand(name="RPM", 
                                            desc="Engine RPM", 
                                            command=b"010C", 
                                            _bytes=4, 
                                            decoder=uas(0x07),
                                            ecu=ECU.ENGINE,
                                            fast=True)
        

        unknown_pid_command = obd.OBDCommand(
                                            name="Unknown PID",
                                            desc="Unknown PID",
                                            command=b"B73FAA",  # 16進数のCAN ID (10進数の12015050に対応)
                                            _bytes=64,  # 最大64バイトのデータを取得
                                            decoder=decode_steering_angle,  # デコーダー関数は未定義
                                            ecu=obd.ECU.ALL,
                                            fast=True
                                            )
        
        
        
        

        self.obd_command_map["STEERING_ANGLE"] = steering_angle_command
        self.obd_command_map["VEHICLE_SPEED"] = vehicle_speed_command
        self.obd_command_map["VEHICLE_ENGINE_RPM"] = vehicle_engine_rpm
        self.obd_command_map["UNKNOWN"] = unknown_pid_command

    
def test_main():
    print("Main start")
    config = load_config(config_path)
    meas_obdscanner = OBDSCANNER(config.sensors['obdscanner'])
    command_list = Custom_OBD_Commands()
    if meas_obdscanner.res == 'Not Connected':
        config["master"]["is_offline"] = True
        print("Could not connect a car...")
        print("offline mode...")
    
    print("Create an obd scanner instance")
    while True:
        command = command_list.obd_command_map["UNKNOWN"]
        response = meas_obdscanner.connection.query(command)
        
        command = command_list.obd_command_map["VEHICLE_ENGINE_RPM"]
        response = meas_obdscanner.connection.query(command)
        if response is not None:
            print(f"Engine RPM: {response.value}")
        command =  command_list.obd_command_map["STEERING_ANGLE"]
        response = meas_obdscanner.connection.query(command)    
        if response.is_successful():
            print(f"Steering Angle: {response.value}")
            
        time.sleep(1)
    
     
    
if __name__ == '__main__':
    test_main()

    