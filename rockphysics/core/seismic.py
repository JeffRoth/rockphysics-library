"""
Seismic Calculation Module

This module contains functions for time-depth conversion, synthetic
seismogram generation, and related seismic processing tasks. These functions
are designed to operate on rockphysics.Well objects and pandas DataFrames.
"""
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import convolve
from typing import Union, Tuple, Callable, List

# Assuming the Well class is defined elsewhere, e.g., from rockphysics.well import Well

def load_checkshot_data(filepath: str) -> pd.DataFrame:
    """
    Loads checkshot data (time-depth pairs) from a CSV file.
    The CSV file must contain 'depth' and 'time' columns.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        pd.DataFrame: DataFrame with 'depth' and 'time' columns, sorted by depth.
    """
    checkshot_df = pd.read_csv(filepath)
    if 'depth' not in checkshot_df.columns or 'time' not in checkshot_df.columns:
        raise ValueError("Checkshot CSV must contain 'depth' and 'time' columns.")
    return checkshot_df.sort_values(by='depth').reset_index(drop=True)


def create_depth_time_interpolators(checkshot_data: pd.DataFrame) -> Tuple[Callable, Callable]:
    """
    Creates linear interpolation functions for depth-to-time and time-to-depth
    conversion based on checkshot data.

    Args:
        checkshot_data (pd.DataFrame): DataFrame with 'depth' and 'time' columns.

    Returns:
        Tuple[Callable, Callable]: A tuple of (depth_to_time, time_to_depth) functions.
    """
    if len(checkshot_data) < 2:
        raise ValueError("Checkshot data must have at least two points for interpolation.")
    
    unique_depth_data = checkshot_data.drop_duplicates(subset=['depth'], keep='first')
    unique_time_data = checkshot_data.drop_duplicates(subset=['time'], keep='first')

    depth_to_time_func = interp1d(
        unique_depth_data['depth'], unique_depth_data['time'],
        kind='linear', fill_value="extrapolate", assume_sorted=True
    )
    sorted_time_data = unique_time_data.sort_values(by='time')
    time_to_depth_func = interp1d(
        sorted_time_data['time'], sorted_time_data['depth'],
        kind='linear', fill_value="extrapolate", assume_sorted=True
    )
    return depth_to_time_func, time_to_depth_func


def resample_log_to_time(log_depth_series: pd.Series, depth_to_time_func: Callable, target_time_index: pd.Index) -> pd.Series:
    """
    Resamples a single depth-indexed log to a new regular time index.
    
    Args:
        log_depth_series (pd.Series): The input log data, indexed by depth.
        depth_to_time_func (Callable): Interpolation function that converts depth to time.
        target_time_index (pd.Index): The desired regular time index for the output log.

    Returns:
        pd.Series: The log data resampled to the target time index.
    """
    original_depths = log_depth_series.index.values
    corresponding_times = depth_to_time_func(original_depths)
    
    temp_time_log = pd.Series(log_depth_series.values, index=corresponding_times).sort_index()
    temp_time_log = temp_time_log.groupby(temp_time_log.index).mean()

    combined_index = temp_time_log.index.union(target_time_index).sort_values()
    aligned_series = temp_time_log.reindex(combined_index)
    interpolated_log = aligned_series.interpolate(method='index')
    
    log_time_series = interpolated_log.reindex(target_time_index)
    log_time_series.name = f"{log_depth_series.name}_time"
    log_time_series.index.name = target_time_index.name or "Time"
    return log_time_series


def convert_well_to_time(
    well, log_mnemonics: List[str], depth_to_time_func: Callable, target_time_index: pd.Index
) -> pd.DataFrame:
    """
    Converts multiple specified logs from a Well object to a time-indexed DataFrame.

    Args:
        well (Well): The Well object containing the source log data.
        log_mnemonics (List[str]): A list of log mnemonics to convert.
        depth_to_time_func (Callable): An interpolation function that converts depth to time.
        target_time_index (pd.Index): The desired regular time index for the output.

    Returns:
        pd.DataFrame: A new DataFrame containing the specified logs resampled to the time index.
    """
    time_logs = {}
    for mnemonic in log_mnemonics:
        if mnemonic in well.logs.columns:
            log_time_series = resample_log_to_time(
                well.logs[mnemonic], depth_to_time_func, target_time_index
            )
            time_logs[log_time_series.name] = log_time_series
        else:
            print(f"Warning: Log '{mnemonic}' not found in well. Skipping.")
    
    return pd.DataFrame(time_logs)


def calculate_reflectivity(acoustic_impedance: pd.Series) -> pd.Series:
    """
    Calculates the reflection coefficient series from an acoustic impedance log.

    Args:
        acoustic_impedance (pd.Series): A Series representing the acoustic impedance log.

    Returns:
        pd.Series: The reflection coefficient series.
    """
    z = acoustic_impedance.values
    z1, z2 = z[:-1], z[1:]
    rc = (z2 - z1) / (z2 + z1)
    # Pad to match original length, placing RC at the top of the interface
    reflectivity_log = np.append(rc, np.nan) 
    return pd.Series(reflectivity_log, index=acoustic_impedance.index, name='Reflectivity')


def generate_ricker_wavelet(peak_frequency: float, length_ms: float, dt_ms: float) -> pd.Series:
    """
    Generates a Ricker (Mexican hat) wavelet.

    Args:
        peak_frequency (float): The peak frequency of the wavelet in Hz.
        length_ms (float): The total length of the wavelet in milliseconds.
        dt_ms (float): The sample interval in milliseconds.

    Returns:
        pd.Series: A Series representing the Ricker wavelet.
    """
    num_samples = int(length_ms / dt_ms)
    num_samples = num_samples + 1 if num_samples % 2 == 0 else num_samples
    t_ms = np.linspace(-length_ms / 2, length_ms / 2, num_samples)
    t_s = t_ms / 1000.0

    pi_f_t_sq = (np.pi * peak_frequency * t_s) ** 2
    wavelet_amplitude = (1 - 2 * pi_f_t_sq) * np.exp(-pi_f_t_sq)
    return pd.Series(wavelet_amplitude, index=t_ms, name=f"Ricker_{peak_frequency}Hz")


def create_synthetic(rc_series: pd.Series, wavelet: pd.Series) -> pd.Series:
    """
    Convolves a reflectivity series with a wavelet to produce a synthetic seismogram.

    Args:
        rc_series (pd.Series): The time-indexed reflectivity coefficient series.
        wavelet (pd.Series): The wavelet to convolve with.

    Returns:
        pd.Series: The synthetic seismogram.
    """
    rc_values = rc_series.fillna(0).values
    wavelet_values = wavelet.values
    synthetic_values = convolve(rc_values, wavelet_values, mode='same')
    return pd.Series(synthetic_values, index=rc_series.index, name="Synthetic")


