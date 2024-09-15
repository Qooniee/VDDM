import tkinter as tk
import sys
from threading import Thread
import os


# Add the parent directory to PATH
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
    root.geometry("2048x1200")
    root.configure(bg='black')

    # GUI Settings
    log_frame = tk.Frame(root, bg='black')
    log_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    log_text = tk.Text(log_frame, wrap=tk.WORD, height=30, width=100, bg='black', fg='white', font=('Courier', 12))
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    log_scroll = tk.Scrollbar(log_frame, command=log_text.yview, bg='gray')
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    log_text.config(yscrollcommand=log_scroll.set)

    sys.stdout = RedirectText(log_text)

    button_frame = tk.Frame(root, bg='black')
    button_frame.pack(pady=10)


    def update_sampling_frequency():
        try:
            new_frequency = float(freq_entry.get())
            if new_frequency <= 0:
                raise ValueError("Frequency must be greater than zero.")
            measurement_control.on_change_sampling_frequency(new_frequency)
        except ValueError as e:
            print(f"Invalid input for frequency: {e}")

    
    freq_label = tk.Label(button_frame, text="Sampling Frequency (Hz):", bg='black', fg='white', font=('Arial', 14))
    freq_label.pack(side=tk.LEFT, padx=10)
    freq_entry = tk.Entry(button_frame, width=5, font=('Arial', 14))
    freq_entry.insert(0, str(measurement_control.sensors.SAMPLING_FREQUENCY_HZ))  # Default value
    freq_entry.pack(side=tk.LEFT, padx=10)
    update_button = tk.Button(button_frame, text="Update Frequency", command=update_sampling_frequency)
    update_button.pack(side=tk.LEFT, padx=10)



    def start_measurement():
        start_button.config(state=tk.DISABLED)  # Disable Start Button
        stop_button.config(state=tk.NORMAL)  # Enable Stop Button
        save_button.config(state=tk.DISABLED)  # Disable Save Button
        freq_entry.config(state=tk.DISABLED)  # Disable frequency entry
        Thread(target=lambda: measurement_control.run_async(measurement_control.start_measurement())).start()

    def stop_measurement():
        measurement_control.stop_measurement()
        start_button.config(state=tk.NORMAL)  # Enable Start Button
        stop_button.config(state=tk.DISABLED)  # Disable Stop Button
        save_button.config(state=tk.NORMAL)  # Enable Save Button
        freq_entry.config(state=tk.NORMAL)  # Re-enable frequency entry


    # Button Style Settings
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

    # Start Button
    start_button = tk.Button(button_frame, text="▷", command=start_measurement, **button_style)
    start_button.config(bg='green')
    start_button.pack(side=tk.LEFT, padx=10)

    # Stop Button
    stop_button = tk.Button(button_frame, text="□", command=stop_measurement, **button_style)
    stop_button.config(state=tk.DISABLED, bg='red')
    stop_button.pack(side=tk.LEFT, padx=10)

    # Save Button
    save_button = tk.Button(button_frame, text="Save", command=lambda: Thread(target=lambda: measurement_control.run_async(measurement_control.save_measurement_data())).start(), **button_style)
    save_button.config(bg='blue')
    save_button.pack(side=tk.LEFT, padx=10)
    
    # Clean up when press a close button
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop() # Call the Main Loop of tk


if __name__ == '__main__':
    setup_gui()
    