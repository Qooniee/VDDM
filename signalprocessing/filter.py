from scipy import signal
import matplotlib.pyplot as plt
import numpy as np

def butterlowpass(x, fpass, fstop, gpass, gstop, fs, dt, checkflag, labelname='Signal[-]'):
    
    """
    Applies a Butterworth low-pass filter to the input signal.

    This function designs a low-pass Butterworth filter based on the given passband and stopband
    frequencies, as well as the passband and stopband ripples. It then applies this filter to the 
    input signal using zero-phase filtering.

    Args:
        x (array-like): The input signal to be filtered.
        fpass (float): The passband frequency of the filter (Hz).
        fstop (float): The stopband frequency of the filter (Hz).
        gpass (float): The maximum loss in the passband (dB).
        gstop (float): The minimum attenuation in the stopband (dB).
        fs (float): The sampling frequency of the input signal (Hz).
        dt (float): The time step between samples in the input signal (seconds).
        checkflag (bool): If True, plots the raw and filtered signals for comparison.
        labelname (str, optional): The label for the signal in the plot. Defaults to 'Signal[-]'.

    Returns:
        array-like: The filtered signal.
    """


    print('Applying filter against: {0}...'.format(labelname))
    fn = 1 / (2 * dt)
    Wp = fpass / fn
    Ws = fstop / fn
    N, Wn = signal.buttord(Wp, Ws, gpass, gstop)
    b1, a1 = signal.butter(N, Wn, "low")
    y = signal.filtfilt(b1, a1, x)
    # print(y)

    if checkflag == True:
        time = np.arange(x.__len__()) * dt
        plt.figure(figsize = (12, 5))
        plt.title('Comparison between signals')
        plt.plot(time, x, color='black', label='Raw signal')
        plt.plot(time, y, color='red', label='Filtered signal')
        plt.xlabel('Time[s]')
        plt.ylabel(labelname)
        plt.show()
    return y
