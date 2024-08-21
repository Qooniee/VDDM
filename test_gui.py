import tkinter as tk
from tkinter import messagebox

from fusion.sensor_fusion import Sensors
from config.config_manager import load_config
from utils.tools import perf_counter
import sys
import os
config_path = "config/measurement_system_config.yaml"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))




class MeasurementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Measurement Control")

        self.start_button = tk.Button(root, text="Start", command=self.start_measurement)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_measurement)
        self.stop_button.pack(pady=10)

        self.is_measuring = False
        
        
        self.config = load_config(config_path)
        self.sensors = Sensors(self.config["master"])
        
        
        

    def start_measurement(self):
        if not self.is_measuring:
            # ここに計測開始の処理を追加
            print("Measurement started.")
            self.is_measuring = True
        else:
            messagebox.showinfo("Info", "Measurement is already running.")

    def stop_measurement(self):
        if self.is_measuring:
            # ここに計測停止の処理を追加
            print("Measurement stopped.")
            self.is_measuring = False
        else:
            messagebox.showinfo("Info", "Measurement is not running.")

def main():
    print("Start sensor fusion main")
    print("Called an instance of Sensors class")
    
    root = tk.Tk()
    app = MeasurementApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
