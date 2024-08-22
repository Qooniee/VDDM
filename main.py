import tkinter as tk  # TkinterをインポートしてGUIを作成する
import sys  # システム関連の操作を行うためにsysをインポート
from threading import Thread  # スレッド処理を行うためにThreadをインポート
from fusion.sensor_fusion import Sensors  # センサー操作のために独自のSensorsクラスをインポート
from config.config_manager import load_config  # 設定ファイルの読み込みのためにload_config関数をインポート
from utils.tools import perf_counter, wait_process  # ツール関数としてperf_counterとwait_processをインポート
from utils.visualize_data import format_sensor_fusion_data  # データのフォーマット用関数をインポート
import os  # OS関連の操作を行うためにosをインポート

import asyncio # 非同期処理用ライブラリ
import pandas as pd
import datetime




# グローバル変数
is_running = False  # 測定が実行中かどうかを示すフラグ
sensors = None  # Sensorsクラスのインスタンスを保持するための変数

# 設定ファイルのパスを指定
config_path = "config/measurement_system_config.yaml"
# カレントディレクトリをPythonのモジュール検索パスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 標準出力をGUIのテキストウィジェットにリダイレクトするためのクラス
class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget  # テキストウィジェットの参照を保持

    def write(self, text):
        # テキストウィジェットにテキストを挿入し、自動的にスクロールする
        self.text_widget.insert(tk.END, text)
        self.text_widget.yview(tk.END)

    def flush(self):
        pass  # 何もしない（標準出力のフラッシュを無視）

# 測定を開始するスレッドを起動する関数
def start_measurement_thread():
    global is_running  # グローバル変数を使用
    global sensors
    
    if not is_running:  # 測定がまだ実行されていない場合
        is_running = True  # 測定を実行中に設定
        print("Measurement started.")
        measurement(sensors, load_config(config_path))  # 測定を開始
    else:
        print("Measurement is already running.")  # 既に実行中であることを通知

# 測定を停止する関数
def stop_measurement_thread():
    global is_running  # グローバル変数を使用
    
    if is_running:  # 測定が実行中であれば
        is_running = False  # 測定を停止
        print("Measurement stopped.")
    else:
        print("Measurement is not running.")  # 測定が実行されていないことを通知

# 実際の測定を行う関数
def measurement(sensors, config):
    print("Measurement function called.")
    start_time = perf_counter()  # 測定開始時間を記録
    sampling_counter = 0  # サンプリング回数を初期化
    try:
        while is_running:  # 測定が実行中の間ループ
            iteration_start_time = perf_counter()  # ループ開始時間を記録
            current_time = perf_counter() - start_time  # 経過時間を計算
            sampling_counter += 1  # サンプリング回数をインクリメント
            data = sensors.collect_data()  # センサーからデータを収集
            
            if sensors.is_show_real_time_data:  # リアルタイムデータ表示が有効であれば
                all_sensor_data_columns = []
                for key in sensors.config.sensors.keys():  # 各センサーのデータカラムを収集
                    all_sensor_data_columns += sensors.config.sensors[key].data_columns
                    formatted_data = format_sensor_fusion_data(data, all_sensor_data_columns)  # データをフォーマット

                # 現在の時間とフォーマットされたデータを表示
                print("--------------------------------------------------------------------")
                print("Current Time is: {:.3f}".format(current_time))
                print(formatted_data)
                
            # サンプリング間隔と処理時間に応じて適切なタイミングまで待機
            elapsed_time = perf_counter() - iteration_start_time
            sleep_time = sensors.SAMPLING_TIME - elapsed_time
            if sleep_time > 0:
                wait_process(sleep_time)
    except Exception as e:
        print(e)  # エラーが発生した場合にエラーメッセージを表示

        
# asyncio.to_threadにより同期関数を別スレッドで実行し、その結果を非同期で扱う
async def save_data_async(df, path):
    await asyncio.to_thread(df.to_csv, path, sep=',', encoding='utf-8', index=False, header=False, mode='a')
 
async def save_data(self):
        # Convert the DataFrame from the numpy array
        self.df = pd.DataFrame(self.assy_data, columns=self.COLUMNS, dtype=np.float32)
        await save_data_async(self.df, self.current_file_path)
        self.assy_data = np.zeros((0, len(self.COLUMNS)))  # Clear data but keep the correct shape

        # if self.Isfilter:
        #     self.filtered_df = self.filtering(df=self.df, labellist=self.COLUMNS[1:])
        #     await save_data_async(self.filtered_df, self.current_file_path.replace('_raw_data.csv', '_filt_data.csv'))


async def finish_measurement_and_save_data(self):
    # Convert the DataFrame from the numpy array
    t_delta = datetime.timedelta(hours=9)
    TIMEZONE = datetime.timezone(t_delta, self.timezone)# You have to set your timezone
    now = datetime.datetime.now(TIMEZONE)
    timestamp = now.strftime('%Y%m%d%H%M%S')
    self.df = pd.DataFrame(self.assy_data, columns=self.COLUMNS, dtype=np.float32)
    final_file_path = self.current_file_path.replace(self.current_file_path.split('/')[-1], 
                                                timestamp + '_' + self.current_file_path.split('/')[-1])
    await save_data_async(self.df, self.current_file_path)
    raw_df = pd.read_csv(self.current_file_path, header=None)
    raw_df.columns = self.COLUMNS
    raw_df.to_csv(final_file_path, sep=',', encoding='utf-8', index=False, header=True)
    print()

    if self.Isfilter:
        filt_df = self.filtering(df=raw_df, labellist=self.COLUMNS[1:])
        filt_df.to_csv(final_file_path.replace('_raw_data.csv', '_filt_data.csv'), sep=',', encoding='utf-8', index=False, header=True)

    if os.path.exists(self.current_file_path):
        os.remove(self.current_file_path)
        print(f"File  '{self.current_file_path}' was deleted")
    else:
        print(f"File '{self.current_file_path}' is not existed")




# GUIをセットアップする関数
def setup_gui():
    global sensors
    global is_running
    
    config = load_config(config_path)  # 設定ファイルを読み込む
    sensors = Sensors(config["master"])  # Sensorsクラスのインスタンスを初期化

    root = tk.Tk()  # Tkinterのルートウィンドウを作成
    root.title("Measurement Control")  # ウィンドウタイトルを設定
    root.geometry("800x600")  # ウィンドウサイズを設定

    # GUIの背景色をカスタマイズ
    root.configure(bg='black')
    
    # ログ表示用のフレームを作成
    log_frame = tk.Frame(root, bg='black')
    log_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # テキストウィジェットを作成してログ表示に使用
    log_text = tk.Text(log_frame, wrap=tk.WORD, height=30, width=100, bg='black', fg='white', font=('Courier', 12))
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # スクロールバーを作成してテキストウィジェットに関連付け
    log_scroll = tk.Scrollbar(log_frame, command=log_text.yview, bg='gray')
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # テキストウィジェットにスクロールバーを設定
    log_text.config(yscrollcommand=log_scroll.set)

    # 標準出力をテキストウィジェットにリダイレクト
    sys.stdout = RedirectText(log_text)

    # ボタンを配置するフレームを作成
    button_frame = tk.Frame(root, bg='black')
    button_frame.pack(pady=10)

    # 測定開始ボタンを作成し、クリック時に測定を開始するスレッドを起動
    start_button = tk.Button(button_frame, text="Start Measurement", command=lambda: Thread(target=start_measurement_thread).start(), bg='green', fg='white', font=('Arial', 14))
    start_button.pack(side=tk.LEFT, padx=10)

    # 測定停止ボタンを作成し、クリック時に測定を停止
    stop_button = tk.Button(button_frame, text="Stop Measurement", command=stop_measurement_thread, bg='red', fg='white', font=('Arial', 14))
    stop_button.pack(side=tk.LEFT, padx=10)

    root.mainloop()  # Tkinterのイベントループを開始

# メイン関数
if __name__ == '__main__':
    print("Start Main function...")
    setup_gui()  # GUIのセットアップを実行
