from signalprocessing.filter import butterlowpass
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def remove_outliers_with_z_score(data, threshold=3):
    """
    Removes outliers based on Z-score.
    
    Args:
        data (numpy array): The input data array.
        threshold (float): The Z-score threshold above which data is considered an outlier.

    Returns:
        numpy array: The data with outliers replaced by NaN.
    """
    data = data.astype(float) 
    mean = np.mean(data)
    std = np.std(data)
    z_scores = (data - mean) / std
    is_outlier = np.abs(z_scores) > threshold
    if np.any(is_outlier):
        data[is_outlier] = np.nan
    return data

def remove_outliers_with_iqr(data, multiplier=1.5):
    """
    Removes outliers based on the Interquartile Range (IQR).

    Args:
        data (numpy array): The input data array.
        multiplier (float): The multiplier for the IQR to define outliers.

    Returns:
        numpy array: The data with outliers replaced by NaN.
    """
    data = data.astype(float)
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)
    
    is_outlier = (data < lower_bound) | (data > upper_bound)
    if np.any(is_outlier):
        data[is_outlier] = np.nan
    
    return data

def filtering(df, SAMPLING_FREQUENCY, FPASS, FSTOP, GPASS, GSTOP, labellist, checkflag=False, remove_outlier_method="z-score"):
    """
    Label list must dropped "Time" label.
    Filter function doesn't need "Time" for the computation.
    """
    filtered_df = df.copy()
    SAMPLING_TIME = 1 / SAMPLING_FREQUENCY
    
    for labelname in labellist:
        x = df[labelname].to_numpy()
        
        # NaNを補完する（線形補間）
        if np.any(np.isnan(x)):
            x = pd.Series(x).interpolate().to_numpy()
        
        
        # 外れ値を除去してNaNにする　3σ
        if remove_outlier_method == "z-score":
            x = remove_outliers_with_z_score(x, threshold=3)
        elif remove_outlier_method == "iqr":
            x = remove_outliers_with_iqr(x)
        
        # NaNを補完する（線形補間）
        if np.any(np.isnan(x)):
            x = pd.Series(x).interpolate().to_numpy()
        
        
        # NaNを無視してフィルタリング
        if not np.any(np.isnan(x)):
            filtered_df[labelname] = butterlowpass(
                x=x,  # Correctly pass the numpy array as 'x'
                fpass=FPASS,
                fstop=FSTOP,
                gpass=GPASS,
                gstop=GSTOP,
                fs=SAMPLING_FREQUENCY,
                dt=SAMPLING_TIME,
                checkflag=checkflag,
                labelname=labelname
            )
        else:
            print(f"Column {labelname} contains NaN after interpolation and is skipped.")
    
    return filtered_df

    
if __name__ == '__main__':
    CSV_PATH = "data/20240831160108/20240831160108_measurement_raw_data.csv"
    SAMPLING_FREQUENCY = 50
    FPASS = int(SAMPLING_FREQUENCY / 2.56) #10 # int(SAMPLING_FREQUENCY / 2.56)
    FSTOP = int(SAMPLING_FREQUENCY / 2) #15 # int(SAMPLING_FREQUENCY / 2)
    GPASS = 3
    GSTOP = 40
    SAMPLING_RATE = 1 / SAMPLING_FREQUENCY
    df = pd.read_csv(CSV_PATH, header=0)
    labellist = df.columns.drop("Time")
    filtered_df = filtering(df, SAMPLING_FREQUENCY, FPASS, FSTOP, GPASS, GSTOP, labellist, False, "iqr")
    filtered_df.to_csv(CSV_PATH.replace('.csv', '_filt_data.csv'), sep=',', encoding='utf-8', index=False, header=True)
    filtered_df.plot(x='Time', y='linear_accel_x', kind='line', figsize=(12, 6))
    plt.savefig("graph.png")
    