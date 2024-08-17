import os
import yaml
from types import SimpleNamespace

class ConfigDict:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigDict(value))
            else:
                setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

def load_config(config_path: str):
    try:
        with open(config_path, 'r') as file:
            config_dict = yaml.safe_load(file)
            return ConfigDict(config_dict)
        
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print(f"Current working directory: {os.getcwd()}")
        raise
    except PermissionError:
        print(f"Permission denied when trying to read: {config_path}")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error when loading config: {e}")
        raise


if __name__ == '__main__':
    
    # get the script path
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # generate config file path
    config_path = os.path.join(script_dir, 'measurement_system_config.yaml')
    
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Failed to load config: {e}")
        
    print(config.bno055)
    print(config.elm327)
    print(config.bno055.sampling_frequency_hz)
    print(config.elm327.data_columns)
    print(config.general.data_path)