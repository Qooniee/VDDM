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
    
    def update_sampling_frequency():
        try:
            new_frequency = float(freq_entry.get())
            if new_frequency <= 0:
                raise ValueError("Frequency must be greater than zero.")
            measurement_control.on_change_sampling_frequency(new_frequency)
        except ValueError as e:
            print(f"Invalid input for frequency: {e}")
    
    def update_sequence_length():
        try:
            new_sequence_length = int(sequence_length_entry.get())
            if new_sequence_length <= 0:
                raise ValueError("Sequence length must be greater than zero.")
            measurement_control.on_change_sequence_length(new_sequence_length)
        except ValueError as e:
            print(f"Invalid input for sequence length: {e}")
    
    def update_parameters():
        update_sampling_frequency()
        update_sequence_length()
    
    
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


    def on_closing():
        measurement_control.cleanup()
        root.destroy()
    
    
    # ----------- GUI Layout ---------- #
    
    root = tk.Tk()
    root.title("Measurement Control")
    root.geometry("2048x1200")
    root.configure(bg='black')

    # Log frame
    log_frame = tk.Frame(root, bg='black')
    log_text = tk.Text(log_frame, wrap=tk.WORD, height=30, width=100, bg='black', fg='white', font=('Courier', 12))
    log_scroll = tk.Scrollbar(log_frame, command=log_text.yview, bg='gray')
    log_text.config(yscrollcommand=log_scroll.set)
    
    log_frame.place(relx=0, rely=0.5, relwidth=1.0, relheight=0.5)
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    sys.stdout = RedirectText(log_text)

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
    start_button = tk.Button(root, text="▷", command=start_measurement, **button_style)
    start_button.config(bg='green')
    start_button.place(x=10, y=10, width=80, height=60)

    # Stop Button
    stop_button = tk.Button(root, text="□", command=stop_measurement, **button_style)
    stop_button.config(state=tk.DISABLED, bg='red')
    stop_button.place(x=100, y=10, width=80, height=60)

    # Save Button
    save_button = tk.Button(root, text="Save", command=lambda: Thread(target=lambda: measurement_control.run_async(measurement_control.save_measurement_data())).start(), **button_style)
    save_button.config(bg='blue')
    save_button.place(x=190, y=10, width=80, height=60)

    # Sampling Frequency Entry
    freq_label = tk.Label(root, text="fs (Hz):", bg='black', fg='white', font=('Arial', 14))
    freq_label.place(x=280, y=10)
    
    freq_entry = tk.Entry(root, width=5, font=('Arial', 14))
    freq_entry.insert(0, str(measurement_control.sensors.SAMPLING_FREQUENCY_HZ))  # Default value
    freq_entry.place(x=380, y=10)

    # Sequence Length Entry
    sequence_length_label = tk.Label(root, text="Seq Len (s):", bg='black', fg='white', font=('Arial', 14))
    sequence_length_label.place(x=480, y=10)
    
    sequence_length_entry = tk.Entry(root, width=5, font=('Arial', 14))
    sequence_length_entry.insert(0, str(measurement_control.sensors.SEQUENCE_LENGTH))  # Default value
    sequence_length_entry.place(x=610, y=10)

    # Update Button
    update_button = tk.Button(root, text="Update", command=update_parameters, **button_style)
    update_button.config(bg='orange', width=15)
    update_button.place(x=720, y=10, width=80, height=60) 

    # Clean up when press a close button
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()  # Call the Main Loop of tk


if __name__ == '__main__':
    setup_gui()
