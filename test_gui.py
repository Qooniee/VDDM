import tkinter as tk
import sys
from threading import Thread
from fusion.sensor_fusion import Sensors
from config.config_manager import load_config
from utils.tools import perf_counter, wait_process
from utils.visualize_data import format_sensor_fusion_data
import os

# グローバル変数
is_running = False
sensors = None

config_path = "config/measurement_system_config.yaml"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.insert(tk.END, text)
        self.text_widget.yview(tk.END)

    def flush(self):
        pass  # 何もする必要はありません

def start_measurement_thread():
    global is_running
    global sensors
    
    if not is_running:
        is_running = True
        print("Measurement started.")
        measurement(sensors, load_config(config_path))
    else:
        print("Measurement is already running.")

def stop_measurement_thread():
    global is_running
    global sensors

    if is_running:
        is_running = False
        print("Measurement stopped.")
    else:
        print("Measurement is not running.")

def measurement(sensors, config):
    print("Measurement function called.")
    start_time = perf_counter()
    sampling_counter = 0
    try:
        while is_running:
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

def setup_gui():
    global sensors
    global is_running
    
    config = load_config(config_path)
    sensors = Sensors(config["master"])

    root = tk.Tk()
    root.title("Measurement Control")
    root.geometry("800x600")  # ウィンドウサイズを拡大

    # GUIのカスタマイズ
    root.configure(bg='black')
    
    # ログ表示用ウィジェット
    log_frame = tk.Frame(root, bg='black')
    log_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    log_text = tk.Text(log_frame, wrap=tk.WORD, height=30, width=100, bg='black', fg='white', font=('Courier', 12))
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    log_scroll = tk.Scrollbar(log_frame, command=log_text.yview, bg='gray')
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    log_text.config(yscrollcommand=log_scroll.set)

    # 標準出力のリダイレクト
    sys.stdout = RedirectText(log_text)

    button_frame = tk.Frame(root, bg='black')
    button_frame.pack(pady=10)

    start_button = tk.Button(button_frame, text="Start Measurement", command=lambda: Thread(target=start_measurement_thread).start(), bg='green', fg='white', font=('Arial', 14))
    start_button.pack(side=tk.LEFT, padx=10)

    stop_button = tk.Button(button_frame, text="Stop Measurement", command=stop_measurement_thread, bg='red', fg='white', font=('Arial', 14))
    stop_button.pack(side=tk.LEFT, padx=10)

    root.mainloop()

if __name__ == '__main__':
    print("Start Main function...")
    setup_gui()
