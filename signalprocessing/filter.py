from scipy import signal
import matplotlib.pyplot as plt
import numpy as np

def butterlowpass(x, fpass, fstop, gpass, gstop, fs, dt, checkflag, labelname='Signal[-]'):

    print('Applying filter against: {0}...'.format(labelname))
    fn = 1 / (2 * dt)
    Wp = fpass / fn
    Ws = fstop / fn
    N, Wn = signal.buttord(Wp, Ws, gpass, gstop)
    b1, a1 = signal.butter(N, Wn, "low")
    y = signal.filtfilt(b1, a1, x)
    print(y)

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
