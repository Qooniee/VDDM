import time
import os
from collections import deque
import numpy as np
import sys
import time
import adafruit_bno055
import board
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import asyncio
import shutil

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)
config_path = os.path.join(parent_dir, 'config', 'measurement_system_config.yaml')


from signalprocessing.filter import butterlowpass
from utils.tools import wait_process
from config.config_manager import load_config

path = os.getcwd()

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
        self.Isfilter=config.filter_params.is_filter
        
        self.IsStart = False
        self.IsStop = True
        self.IsShow = False

        
        
        

        self.Time_queue = deque(np.zeros(self.INIT_LEN))# Time
        self.linear_accel_x_queue = deque(np.zeros(self.INIT_LEN))# linear_accel_x
        self.linear_accel_y_queue = deque(np.zeros(self.INIT_LEN))# linear_accel_y
        self.linear_accel_z_queue = deque(np.zeros(self.INIT_LEN))# linear_accel_z
        self.gyro_x_queue = deque(np.zeros(self.INIT_LEN))# gyro_x
        self.gyro_y_queue = deque(np.zeros(self.INIT_LEN))# gyro_y
        self.gyro_z_queue = deque(np.zeros(self.INIT_LEN))# gyro_z
        self.euler_x_queue = deque(np.zeros(self.INIT_LEN))# euler_x Roll
        self.euler_y_queue = deque(np.zeros(self.INIT_LEN))# euler_y Roll
        self.euler_z_queue = deque(np.zeros(self.INIT_LEN))# euler_z yaw
        self.quat_roll_queue = deque(np.zeros(self.INIT_LEN))# quat_roll
        self.quat_pitch_queue = deque(np.zeros(self.INIT_LEN))# quat_pitch
        self.quat_yaw_queue = deque(np.zeros(self.INIT_LEN))# quat_yaw
        self.quat1_queue = deque(np.zeros(self.INIT_LEN))# quat1 w
        self.quat2_queue = deque(np.zeros(self.INIT_LEN))# quat2 x
        self.quat3_queue = deque(np.zeros(self.INIT_LEN))# quat3 y
        self.quat4_queue = deque(np.zeros(self.INIT_LEN))# quat4 z
        self.magnetic_x_queue = deque(np.zeros(self.INIT_LEN))# magnetic_x
        self.magnetic_y_queue = deque(np.zeros(self.INIT_LEN))# magnetic_y
        self.magnetic_z_queue = deque(np.zeros(self.INIT_LEN))# magnetic_z
        self.calibstat_sys_queue = deque(np.zeros(self.INIT_LEN))# calibstat_sys
        self.calibstat_gyro_queue = deque(np.zeros(self.INIT_LEN))# calibstat_gyro
        self.calibstat_accel_queue = deque(np.zeros(self.INIT_LEN))# calibstat_accel
        self.calibstat_mag_queue = deque(np.zeros(self.INIT_LEN))# calibstat_mag

        self.current_data_list = np.array([])
        self.assy_data = np.array([])
        self.df = pd.DataFrame(columns=self.COLUMNS)
        self.filtered_df = None
        i2c_instance = board.I2C()
        self.bno055_sensor = adafruit_bno055.BNO055_I2C(i2c_instance)






    def calibration(self):
        print("Start calibration!")
        while self.bno055_sensor.calibrated is not True:
            print('SYS: {0}, Gyro: {1}, Accel: {2}, Mag: {3}'.format(*(self.bno055_sensor.calibration_status)))



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
        euler_z, euler_y, euler_x = [val for val in self.bno055_sensor.euler]# X: yaw, Y: pitch, Z: roll
        gyro_x, gyro_y, gyro_z = [val for val in self.bno055_sensor.gyro]# Gyro[rad/s]
        linear_accel_x, linear_accel_y, linear_accel_z = [val for val in self.bno055_sensor.linear_acceleration]# Linear acceleration[m/s^2]

        quaternion_1, quaternion_2, quaternion_3, quaternion_4 = [val for val in self.bno055_sensor.quaternion]# quaternion
        quat_roll, quat_pitch, quat_yaw = self.calcEulerfromQuaternion(quaternion_1, quaternion_2, quaternion_3, quaternion_4)# Cal Euler angle from quaternion
        magnetic_x, magnetic_y, magnetic_z = [val for val in self.bno055_sensor.magnetic]# magnetic field
        calibstat_sys, calibstat_gyro, calibstat_accel, calibstat_mag = [val for val in self.bno055_sensor.calibration_status]# Status of calibration

        ## Convert values
        linear_accel_x = linear_accel_x
        linear_accel_y = linear_accel_y
        linear_accel_z = linear_accel_z
        gyro_x = gyro_x
        gyro_y = 0.0 if gyro_y == None else gyro_y
        gyro_z = gyro_z
        euler_x = 0.0 if euler_x == None else (-1) * euler_x
        euler_y = 0.0 if euler_y == None else (-1) * euler_y
        euler_z = euler_z
        quat_roll = quat_roll
        quat_pitch = quat_pitch
        quat_yaw = quat_yaw
        #quaternion_1, quaternion_2, quaternion_3, quaternion_4 = quaternion_1, quaternion_2, quaternion_3, quaternion_4
        #magnetic_x, magnetic_y, magnetic_z = magnetic_x, magnetic_y, magnetic_z

        return linear_accel_x, linear_accel_y, linear_accel_z, \
                gyro_x, gyro_y, gyro_z, \
                euler_x, euler_y, euler_z, \
                quat_roll, quat_pitch, quat_yaw, \
                quaternion_1, quaternion_2, quaternion_3, quaternion_4, \
                magnetic_x, magnetic_y, magnetic_z,\
                calibstat_sys, calibstat_gyro, calibstat_accel, calibstat_mag


    def get_update_data_stream(self, Isreturnval=True):
        def update_queue(stream_queue, val):
            stream_queue.popleft()
            stream_queue.append(val)
            return stream_queue
        
        linear_accel_x, linear_accel_y, linear_accel_z, \
        gyro_x, gyro_y, gyro_z, \
        euler_x, euler_y, euler_z, \
        quat_roll, quat_pitch, quat_yaw, \
        quat1, quat2, quat3, quat4, \
        magnetic_x, magnetic_y, magnetic_z, \
        calibstat_sys, calibstat_gyro, calibstat_accel, calibstat_mag = self.get_data_from_BNO055()

        update_queue(self.Time_queue, self.current_time)
        update_queue(self.linear_accel_x_queue, linear_accel_x)
        update_queue(self.linear_accel_y_queue, linear_accel_y)
        update_queue(self.linear_accel_z_queue, linear_accel_z)
        update_queue(self.gyro_x_queue, gyro_x)
        update_queue(self.gyro_y_queue, gyro_y)
        update_queue(self.gyro_z_queue, gyro_z)
        update_queue(self.euler_x_queue, euler_x)
        update_queue(self.euler_y_queue, euler_y)
        update_queue(self.euler_z_queue, euler_z)
        update_queue(self.quat_roll_queue, quat_roll)
        update_queue(self.quat_pitch_queue, quat_pitch)
        update_queue(self.quat_yaw_queue, quat_yaw)
        update_queue(self.quat1_queue, quat1)
        update_queue(self.quat2_queue, quat2)
        update_queue(self.quat3_queue, quat3)
        update_queue(self.quat4_queue, quat4)
        update_queue(self.magnetic_x_queue, magnetic_x)
        update_queue(self.magnetic_y_queue, magnetic_y)
        update_queue(self.magnetic_z_queue, magnetic_z)
        update_queue(self.calibstat_sys_queue, calibstat_sys)
        update_queue(self.calibstat_gyro_queue, calibstat_gyro)
        update_queue(self.calibstat_accel_queue, calibstat_accel)
        update_queue(self.calibstat_mag_queue, calibstat_mag)
        
        if Isreturnval:
            return  np.array([linear_accel_x, linear_accel_y, linear_accel_z, \
                    gyro_x, gyro_y, gyro_z, \
                    euler_x, euler_y, euler_z, \
                    quat_roll, quat_pitch, quat_yaw, \
                    quat1, quat2, quat3, quat4, \
                    magnetic_x, magnetic_y, magnetic_z, \
                    calibstat_sys, calibstat_gyro, calibstat_accel, calibstat_mag])
        else:
            return False

    # def concat_meas_data(self):
    #     dataset = np.append(self.current_time, self.current_data_list).reshape(1, -1)
    #     if self.main_loop_clock == 0:
    #         self.assy_data = dataset
    #     else:
    #         self.assy_data = np.concatenate([self.assy_data, dataset], axis=0)
            
            
    def concat_meas_data(self):
            current_data = np.append([self.current_time], self.current_data_list)
            dataset = current_data.reshape(1, -1)  # Reshape to ensure 2D
            
            print(f'self.assy_data shape: {self.assy_data.shape}')
            print(f'dataset shape: {dataset.shape}')
            
            if self.main_loop_clock == 0:
                self.assy_data = dataset
            else:
                # Ensure the dimensions are correct for concatenation
                try:
                    if self.assy_data.shape[1] == dataset.shape[1]:
                        self.assy_data = np.concatenate([self.assy_data, dataset], axis=0)
                    else:
                        print("Dimension mismatch between assy_data and dataset")
                except IndexError as e:
                    print("IndexError during concatenation:", e)
            





    def show_current_data(self, data_list, data_label):
        message = ""
        for i in range(len(self.COLUMNS)-1):
            val = data_list[i] if data_list[i] != None else "No val"
            message = message + data_label[i] + ": " + str(val) + " / "

        return message


    # async def save_data(self):
    #     # Convert the DataFrame from the numpy array
    #     self.df = pd.DataFrame(self.assy_data, columns=self.COLUMNS, dtype=np.float32)
    #     await save_data_async(self.df, self.current_file_path)
    #     self.assy_data = np.zeros((0, len(self.COLUMNS)))  # Clear data but keep the correct shape
    
    async def save_data(self):
        batch_df = pd.DataFrame(self.assy_data, columns=self.COLUMNS, dtype=np.float32)
        await asyncio.to_thread(batch_df.to_csv, self.SAVE_DATA_PATH + '/' + 'measurement_raw_data.csv', sep=',', encoding='utf-8', index=False, header=False, mode='a')
        self.assy_data = np.zeros((0, len(self.COLUMNS)))


    def finish_measurement_and_save_data(self):
        t_delta = datetime.timedelta(hours=9)
        JST = datetime.timezone(t_delta, 'JST')# You have to set your timezone
        now = datetime.datetime.now(JST)
        timestamp = now.strftime('%Y%m%d%H%M%S')
        
        os.makedirs(self.SAVE_DATA_PATH + '/' + timestamp)
        src_file_path = self.SAVE_DATA_PATH + '/' + 'measurement_raw_data.csv'
        dst_file_path = self.SAVE_DATA_PATH + '/' + timestamp + '/' + timestamp + '_measurement_raw_data.csv'
        shutil.copy2(src_file_path, dst_file_path)
        shutil.copy2(src_file_path, self.SAVE_DATA_PATH + '/' + 'backup_measurement_raw_data.csv')
        os.remove(src_file_path)
        
     

        print("Dataframe was saved!")


    def filtering(self, df, labellist):
        """
        Label list must dropped "Time" label.
        Filter function doesn't need "Time" for the computation.
        """
        filtered_df = df.copy()
        for idx, labelname in enumerate(labellist):
            filtered_df[labelname] = butterlowpass(x=df[labelname], 
                                                   fpass=self.FPASS,
                                                   fstop=self.FSTOP,
                                                   gpass=self.GPASS,
                                                   gstop=self.GSTOP,
                                                   fs=1 / self.SAMPLING_TIME,
                                                   dt = self.SAMPLING_TIME,
                                                   checkflag=False,
                                                   labelname=labelname)

        return filtered_df

    async def meas_start(self):
        
        self.main_loop_clock = 0# Clock
        ## Measurement Main Loop ##
        print("Measurement is started")

        wait_process(2)# sensor initialization
        self.meas_start_time = time.time()#Logic start time
        self.IsStart = True
        self.IsStop = False
        # Main Loop for measurement
        try: 
            while self.IsStart:
                self.itr_start_time = time.time()# Start time of iteration loop
                self.current_time = (self.main_loop_clock / self.SAMPLING_FREQUENCY_HZ)
                ## Process / update data stream, concat data
                """
                1. get data fron a sensor BNO055
                2. deque data from que
                3. enque data to que
                4. create data set at current sample
                5. concatinate data 
                6. Convert numpuy aray to dataframe
                7. save dataframe

                """
                self.current_data_list = self.get_update_data_stream(Isreturnval=True)
                self.concat_meas_data()
                if self.IsShow:
                    message = self.show_current_data(self.current_data_list, self.COLUMNS[1:])
                    print(f'Time: {self.current_time:.3f}')
                    print(message)
                else:
                    message = self.show_current_data(self.current_data_list, self.COLUMNS[1:])


                self.itr_end_time = time.time()# End time of iteration loop
                wait_process(self.SAMPLING_TIME - (self.itr_end_time - self.itr_start_time))# For keeping sampling frequency
                self.main_loop_clock += 1
                
                if self.main_loop_clock % (self.SAVE_INTERVAL * self.SAMPLING_FREQUENCY_HZ) == 0:
                    await self.save_data()
                


        except Exception as e:
            print("Error")
            print(e)
        
        except KeyboardInterrupt:
            self.meas_end_time = time.time()#0.002s
            
            #plt.plot(self.Time_queue, self.euler_x_queue, 'r', '*')
            #plt.show()
            
            # Elapsed time
            self.elapsed_time = self.meas_end_time - self.meas_start_time
            print("KeybordInterrupt!")     
            print(f'Elapsed Time: {self.elapsed_time:.3f}')

            # concat and save data
            await self.save_data()

            # save whole data
            self.finish_measurement_and_save_data()



        print("Finish")


    def Run(self):
        print()



async def test_main():
    print("Main start")
    
    config = load_config(config_path)
    
    meas_bno055 = BNO055(config.sensors['bno055'])
    
    Isneed_calib = False
    if Isneed_calib:
        meas_bno055.calibration()
        print("Calibration was finished!")
    
    if True:
        meas_bno055.IsShow = True
        await meas_bno055.meas_start()


        
        
  

if __name__ == '__main__':
    import time
    #simple_main()
    asyncio.run(test_main())
    print()