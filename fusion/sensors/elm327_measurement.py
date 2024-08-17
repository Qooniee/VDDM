
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)
config_path = os.path.join(parent_dir, 'config', 'measurement_system_config.yaml')

from config.config_manager import load_config

class ELM327:
    def __init__(self, config):    
        self.COLUMNS = config.data_columns    
        self.SAMPLING_FREQUENCY_HZ = config.sampling_frequency_hz
        self.SAMPLING_TIME = 1 / self.SAMPLING_FREQUENCY_HZ
        
        
        
        
       
    def calc_sum(self, x, y):
        return x + y
    
    def print_sth(self, messeage):
        print(messeage)

def main():
    print("Main start")
    
    config = load_config(config_path)
    
    meas_elm327 = ELM327(config.sensors['elm327'])
    
    meas_elm327.print_sth("HEY")

if __name__ == '__main__':
    main()
    