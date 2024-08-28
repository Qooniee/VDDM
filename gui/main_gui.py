import tkinter as tk
import sys
from threading import Thread
import os


# 親ディレクトリをパスに追加
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from measurement.measurement_control import MeasurementControl
from config.config_manager import load_config

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.insert(tk.END, text)
        self.text_widget.yview(tk.END)

    def flush(self):
        pass

def setup_gui():
    measurement_control = MeasurementControl("config/measurement_system_config.yaml")
    
    def on_closing():
        measurement_control.cleanup()
        root.destroy()
    
    root = tk.Tk()
    root.title("Measurement Control")
    root.geometry("2048x1200")  # ウィンドウサイズを拡大
    root.configure(bg='black')

    # GUIのカスタマイズ
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

    def start_measurement():
        start_button.config(state=tk.DISABLED)  # Startボタンを無効化
        stop_button.config(state=tk.NORMAL)  # Stopボタンを有効化
        save_button.config(state=tk.DISABLED)  # Saveボタンを無効化
        Thread(target=lambda: measurement_control.run_async(measurement_control.start_measurement())).start()

    def stop_measurement():
        measurement_control.stop_measurement()
        start_button.config(state=tk.NORMAL)  # Startボタンを有効化
        stop_button.config(state=tk.DISABLED)  # Stopボタンを無効化
        save_button.config(state=tk.NORMAL)  # Saveボタンを有効化

    # ボタンのスタイルを丸く設定
    button_style = {
        'bg': 'green',
        'fg': 'white',
        'font': ('Arial', 14),
        'width': 5,
        'height': 2,
        'bd': 0,
        'highlightthickness': 0,
        'relief': tk.FLAT,
        'cursor': 'hand2'
    }

    # Startボタンを作成
    start_button = tk.Button(button_frame, text="▷", command=start_measurement, **button_style)
    start_button.config(bg='green')  # Startボタンの色を緑に設定
    start_button.pack(side=tk.LEFT, padx=10)

    # Stopボタンを作成
    stop_button = tk.Button(button_frame, text="□", command=stop_measurement, **button_style)
    stop_button.config(state=tk.DISABLED, bg='red')  # Stopボタンの初期状態を無効化し、色を赤に設定
    stop_button.pack(side=tk.LEFT, padx=10)

    # Saveボタンを作成
    save_button = tk.Button(button_frame, text="Save", command=lambda: Thread(target=lambda: measurement_control.run_async(measurement_control.save_measurement_data())).start(), **button_style)
    save_button.config(bg='blue')  # Saveボタンの色を青に設定
    save_button.pack(side=tk.LEFT, padx=10)

    root.protocol("WM_DELETE_WINDOW", on_closing)  # ウィンドウの閉じるボタンにクリーンアップ処理を設定

    root.mainloop()


if __name__ == '__main__':
    setup_gui()
    