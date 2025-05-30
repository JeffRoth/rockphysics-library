# rockphysics/core/seismic.py
from rockphysics.core.log_data import LogData
"""
Seismic Calculation Module

This module contains functions related to seismic wave properties,
modeling, synthetic seismogram generation, and time-depth conversion.
"""
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import convolve
from typing import Union, Tuple, Callable, Optional, List

def load_checkshot_data(filepath: str) -> pd.DataFrame:
    """
    Loads checkshot data (time-depth pairs) from a CSV file.
    The CSV file must contain 'depth' and 'time' columns.
    Time is typically in milliseconds (TWT - Two-Way Time).

    Parameters
    ----------
    filepath : str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame with 'depth' and 'time' columns, sorted by depth.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If 'depth' or 'time' columns are missing in the CSV.
    """
    try:
        checkshot_df = pd.read_csv(filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"Checkshot file not found: {filepath}")

    if 'depth' not in checkshot_df.columns or 'time' not in checkshot_df.columns:
        raise ValueError("Checkshot CSV must contain 'depth' and 'time' columns.")

    # Ensure data is sorted by depth for interpolation
    checkshot_df = checkshot_df.sort_values(by='depth').reset_index(drop=True)
    return checkshot_df[['depth', 'time']]


def create_depth_time_interpolators(
    checkshot_data: pd.DataFrame
) -> Tuple[Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]],
           Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]]:
    """
    Creates linear interpolation functions for depth-to-time and time-to-depth
    conversion based on checkshot data.

    Parameters
    ----------
    checkshot_data : pd.DataFrame
        A DataFrame with 'depth' and 'time' columns, sorted by depth.
        Time is typically in milliseconds (TWT).

    Returns
    -------
    Tuple[Callable, Callable]
        A tuple containing two interpolation functions:
        - depth_to_time(depth_array): Converts depth(s) to time(s).
        - time_to_depth(time_array): Converts time(s) to depth(s).
        Both functions allow extrapolation.

    Raises
    ------
    ValueError
        If checkshot data has fewer than 2 points for interpolation.
    """
    if len(checkshot_data) < 2:
        raise ValueError("Checkshot data must have at least two points for interpolation.")

    # Ensure no duplicate depths or times which can cause issues with interp1d
    # Keep the first occurrence if duplicates exist
    unique_depth_data = checkshot_data.drop_duplicates(subset=['depth'], keep='first')
    unique_time_data = checkshot_data.drop_duplicates(subset=['time'], keep='first')

    if len(unique_depth_data) < 2:
        raise ValueError("Not enough unique depth points in checkshot data for depth-to-time interpolation.")
    if len(unique_time_data) < 2:
         raise ValueError("Not enough unique time points in checkshot data for time-to-depth interpolation.")


    # Interpolator: Depth (input) to Time (output)
    # Using fill_value="extrapolate" allows getting times for depths outside checkshot range.
    # Use with caution, as extrapolation can be inaccurate.
    depth_to_time_func = interp1d(
        unique_depth_data['depth'].values,
        unique_depth_data['time'].values,
        kind='linear',
        fill_value="extrapolate",
        assume_sorted=True # We sorted it earlier
    )

    # Interpolator: Time (input) to Depth (output)
    # Re-sort by time specifically for time_to_depth to ensure assume_sorted=True can be used
    sorted_time_data = unique_time_data.sort_values(by='time')
    time_to_depth_func = interp1d(
        sorted_time_data['time'].values,
        sorted_time_data['depth'].values,
        kind='linear',
        fill_value="extrapolate",
        assume_sorted=True
    )
    return depth_to_time_func, time_to_depth_func


def resample_log_to_time_domain(
    log_depth_series: pd.Series,
    depth_to_time_func: Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]],
    target_time_index: pd.Index
) -> pd.Series:
    """
    Resamples a depth-indexed log to a new regular time index.

    Parameters
    ----------
    log_depth_series : pd.Series
        The input log data, indexed by depth.
    depth_to_time_func : Callable
        An interpolation function that converts depth to time.
    target_time_index : pd.Index
        The desired regular time index for the output log (e.g., in milliseconds).

    Returns
    -------
    pd.Series
        The log data resampled to the target_time_index.
        The series will be named based on the input series name, suffixed with "_time".
    """
    if not isinstance(log_depth_series, pd.Series):
        raise TypeError("Input log_depth_series must be a Pandas Series.")
    if log_depth_series.empty:
        # Return an empty series with the correct index and name
        name = f"{log_depth_series.name}_time" if log_depth_series.name else "log_time"
        return pd.Series(index=target_time_index, dtype=log_depth_series.dtype, name=name)

    # 1. Convert the original log's depth index to time
    original_depths = log_depth_series.index.values
    try:
        corresponding_times = depth_to_time_func(original_depths)
    except ValueError as e:
        raise ValueError(f"Error converting depths to times for log '{log_depth_series.name}': {e}. "
                         "Ensure depth_to_time_func is valid for the log's depth range.")


    # 2. Create a new temporary Series with these (irregular time, value) pairs
    # Ensure the new time index is sorted for interpolation
    temp_time_log = pd.Series(log_depth_series.values, index=corresponding_times)
    temp_time_log = temp_time_log.sort_index()
    
    # 3. Handle duplicate time entries if any (e.g., if multiple depth samples map to nearly the same time)
    # Taking the mean of values at duplicate times.
    temp_time_log = temp_time_log.groupby(temp_time_log.index).mean()

    # 4. Reindex/interpolate this temporary series onto the target_time_index
    # Pandas reindex with method='interpolate' can be simpler here.
    # First, combine the original (now time-indexed) data with an empty series on the target index
    # This ensures all target times are present for interpolation.
    
    combined_index = temp_time_log.index.union(target_time_index)
    # Ensure combined_index is sorted before interpolation
    combined_index = combined_index.sort_values()
    
    aligned_series = temp_time_log.reindex(combined_index)

    # Interpolate (linear by default for pd.Series.interpolate)
    # Using 'index' method for interpolation based on index values (time)
    interpolated_log_time = aligned_series.interpolate(method='index')
    
    # Select only the values at the target_time_index
    log_time_series = interpolated_log_time.reindex(target_time_index)

    log_time_series.name = f"{log_depth_series.name}_time" if log_depth_series.name else "log_time"
    
    if hasattr(target_time_index, 'name') and target_time_index.name:
        log_time_series.index.name = target_time_index.name
    else:
        # Default index name if target_time_index has no name
        log_time_series.index.name = "Time (ms)" 

    return log_time_series


def convert_well_logs_to_time_domain(
    depth_log_dataframe: pd.DataFrame,
    log_mnemonics: List[str],
    depth_to_time_func: Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]],
    target_time_index: pd.Index
) -> LogData:
    """
    Converts multiple specified logs from a depth-indexed DataFrame to a new
    LogData object containing time-indexed logs.

    Parameters
    ----------
    depth_log_dataframe : pd.DataFrame
        The input DataFrame containing log data, indexed by depth.
    log_mnemonics : List[str]
        A list of log mnemonics (column names) to convert from the depth_log_dataframe.
    depth_to_time_func : Callable
        An interpolation function that converts depth to time.
    target_time_index : pd.Index
        The desired regular time index for the output DataFrame (e.g., in milliseconds).
    output_log_data_name : Optional[str], default="TimeDomainLogs"
        This parameter is currently not directly used to name the LogData object
        if using the user's provided LogData class structure. It's kept for potential future use
        or if the LogData class is extended.

    Returns
    -------
    LogData
        A new LogData object containing the specified logs, resampled to the
        target_time_index. Columns in the internal DataFrame will be named
        based on original log names, suffixed with "_time".

    Raises
    ------
    ValueError
        If any of the specified log_mnemonics are not found in the input DataFrame.
    """
    time_domain_series_collection = {} # Store Series to build DataFrame
    missing_logs = []

    for mnemonic in log_mnemonics:
        if mnemonic in depth_log_dataframe.columns:
            log_depth_series = depth_log_dataframe[mnemonic]
            log_time_series = resample_log_to_time_domain(
                log_depth_series,
                depth_to_time_func,
                target_time_index
            )
            # Use the new name (e.g., "GR_time") as key for the dict and for the series name
            time_domain_series_collection[log_time_series.name] = log_time_series
        else:
            missing_logs.append(mnemonic)
            print(f"Warning: Log mnemonic '{mnemonic}' not found in depth_log_dataframe. Skipping.")

    # Create DataFrame from the collected time-domain series
    if not time_domain_series_collection:
        # If no logs were successfully converted, create an empty DataFrame
        time_log_dataframe = pd.DataFrame(index=target_time_index)
    else:
        time_log_dataframe = pd.DataFrame(time_domain_series_collection)

    # Ensure the DataFrame index has the correct name
    # This name will be part of the DataFrame inside the LogData object
    time_log_dataframe.index.name = target_time_index.name if target_time_index.name else "Time (ms)"

    # Create and return a LogData object using the user's class definition
    # The user's LogData class __init__ only takes 'data'.
    # The 'output_log_data_name' is not directly passed to this constructor.
    # If the user wants to name the LogData instance, they can do it when they receive the object.
    return LogData(data=time_log_dataframe)


def calculate_reflectivity_series(
    acoustic_impedance: Union[pd.Series, np.ndarray],
    mode: str = 'interface_above'
) -> Union[pd.Series, np.ndarray]:
    """
    Calculates the reflection coefficient series from an acoustic impedance log.
    (This function is from the previous context and remains unchanged here for completeness of the module)

    The reflection coefficient R at an interface is given by:
        R = (Z2 - Z1) / (Z2 + Z1)
    where Z1 is the acoustic impedance of the upper layer and Z2 is the
    acoustic impedance of the lower layer.

    Parameters
    ----------
    acoustic_impedance : Union[pd.Series, np.ndarray]
        A 1D array or Pandas Series representing the acoustic impedance log.
        Values should be depth-ordered (top to bottom) if in depth, or time-ordered if in time.
    mode : str, default='interface_above'
        Determines the length and alignment of the output reflectivity series.
        - 'interface_above': Reflectivity is assigned to the depth/time of Z1 (the top
          of the interface). The output series will have the same length as the
          input, with the last value being NaN (as there's no Z2 below it).
        - 'interface_below': Reflectivity is assigned to the depth/time of Z2 (the bottom
          of the interface). The output series will have the same length as the
          input, with the first value being NaN.
        - 'interface_between': Reflectivity is assigned to the interface itself.
          The output series will be one sample shorter than the input.

    Returns
    -------
    Union[pd.Series, np.ndarray]
        The reflection coefficient series.
    """
    if len(acoustic_impedance) < 2:
        raise ValueError("Acoustic impedance log must have at least two samples to calculate reflectivity.")

    is_series = isinstance(acoustic_impedance, pd.Series)
    if is_series:
        z = acoustic_impedance.values
        original_index = acoustic_impedance.index
        series_name = acoustic_impedance.name
    else:
        z = np.asarray(acoustic_impedance)

    z1 = z[:-1]
    z2 = z[1:]

    epsilon = 1e-9 # To prevent division by zero
    numerator = z2 - z1
    denominator = z2 + z1
    
    rc = np.full_like(denominator, np.nan, dtype=np.float64)
    valid_denominator_mask = np.abs(denominator) > epsilon
    rc[valid_denominator_mask] = numerator[valid_denominator_mask] / denominator[valid_denominator_mask]

    output_index = None # Initialize
    if mode == 'interface_above':
        reflectivity_log = np.append(rc, np.nan)
        if is_series: output_index = original_index
    elif mode == 'interface_below':
        reflectivity_log = np.insert(rc, 0, np.nan)
        if is_series: output_index = original_index
    elif mode == 'interface_between':
        reflectivity_log = rc
        if is_series: output_index = original_index[:-1]
    else:
        raise ValueError(f"Invalid mode '{mode}'. Choose from 'interface_above', 'interface_below', 'interface_between'.")

    if is_series:
        series_name_out = "Reflectivity"
        if series_name:
            series_name_out = f"Reflectivity_{series_name}"
        return pd.Series(reflectivity_log, index=output_index, name=series_name_out)
    else:
        return reflectivity_log

def generate_ricker_wavelet(peak_frequency: float, length_ms: float, dt_ms: float) -> pd.Series:
    """
    Generates a Ricker (Mexican hat) wavelet.

    Parameters
    ----------
    peak_frequency : float
        The peak (dominant) frequency of the wavelet in Hz.
    length_ms : float
        The total length of the wavelet in milliseconds (e.g., 128 ms).
        Should be an even multiple of dt_ms for symmetry, or adjusted.
    dt_ms : float
        The sample interval in milliseconds (e.g., 2 ms).

    Returns
    -------
    pd.Series
        A Pandas Series representing the Ricker wavelet, indexed by time (ms)
        centered around 0.
    """
    if peak_frequency <= 0:
        raise ValueError("Peak frequency must be positive.")
    if length_ms <= 0:
        raise ValueError("Length of wavelet must be positive.")
    if dt_ms <= 0:
        raise ValueError("Sample interval (dt) must be positive.")

    num_samples = int(length_ms / dt_ms)
    if num_samples % 2 == 0: # Ensure odd number of samples for a center peak
        num_samples +=1
        # Recalculate length_ms to be precise if num_samples was adjusted
        length_ms = num_samples * dt_ms


    # Create time vector centered around 0
    # t goes from -length_ms/2 to +length_ms/2
    t_ms = np.linspace(-length_ms / 2, length_ms / 2, num_samples)
    t_s = t_ms / 1000.0  # Convert time to seconds for the formula

    # Ricker wavelet formula
    # f = peak_frequency (in Hz)
    # t = time (in seconds)
    # A = (1 - 2 * (pi * f * t)^2) * exp(-(pi * f * t)^2)
    pi_f_t = np.pi * peak_frequency * t_s
    pi_f_t_sq = pi_f_t**2
    wavelet_amplitude = (1 - 2 * pi_f_t_sq) * np.exp(-pi_f_t_sq)
    
    return pd.Series(wavelet_amplitude, index=t_ms, name=f"Ricker_{peak_frequency}Hz")

def convolve_traces(
    rc_series: pd.Series,
    wavelet: Union[np.ndarray, pd.Series],
    mode: str = 'same'
) -> pd.Series:
    """
    Convolves a reflectivity series with a wavelet to produce a synthetic seismogram.

    Parameters
    ----------
    rc_series : pd.Series
        The time-indexed reflectivity coefficient series. NaNs will be treated as 0.
    wavelet : Union[np.ndarray, pd.Series]
        The wavelet. If a Pandas Series, its values are used.
    mode : str, default='same'
        Convolution mode passed to scipy.signal.convolve:
        - 'full': The output is the full discrete linear convolution.
        - 'valid': The output consists only of those parts of the convolution
                   that are computed without zero-padding.
        - 'same': The output is the same size as `rc_series`, centered
                  with respect to the 'full' output.

    Returns
    -------
    pd.Series
        The synthetic seismogram (convolved trace), with an index matching
        `rc_series` if mode is 'same'.
    """
    if not isinstance(rc_series, pd.Series):
        raise TypeError("rc_series must be a Pandas Series.")
    
    rc_values = rc_series.fillna(0).values # Replace NaNs with 0 for convolution
    
    if isinstance(wavelet, pd.Series):
        wavelet_values = wavelet.values
    elif isinstance(wavelet, np.ndarray):
        wavelet_values = wavelet
    else:
        raise TypeError("Wavelet must be a NumPy array or Pandas Series.")

    if rc_values.ndim != 1 or wavelet_values.ndim != 1:
        raise ValueError("Input series and wavelet must be 1-dimensional.")

    synthetic_values = convolve(rc_values, wavelet_values, mode=mode, method='auto')

    output_index = rc_series.index # Default for mode='same'
    if mode == 'full':
        # For 'full' mode, the length is len(rc) + len(wavelet) - 1.
        # Creating a meaningful index is more complex and depends on conventions.
        if len(synthetic_values) != len(rc_series.index):
             print(f"Warning: Convolution mode '{mode}' results in a different length ({len(synthetic_values)}) "
                   f"than input ({len(rc_series.index)}). Index alignment might not be straightforward.")
             # Attempt to align start time if possible, otherwise simple range
             dt_index = 1.0 # Default dt
             if len(rc_series.index) > 1:
                 dt_index = rc_series.index[1] - rc_series.index[0]
             
             # Calculate the shift of the wavelet center from its start
             wavelet_center_offset_samples = (len(wavelet_values) - 1) // 2
             start_time_offset_ms = wavelet_center_offset_samples * dt_index
             
             # Align the start of the 'full' convolution output with the start of the input signal,
             # adjusted by the wavelet's one-sided length before its center.
             start_time = rc_series.index.min() - start_time_offset_ms
             
             output_index = pd.Index(np.arange(len(synthetic_values)) * dt_index + start_time)


    elif mode == 'valid':
        # 'valid' mode also changes length, making direct index mapping tricky.
        if len(synthetic_values) != len(rc_series.index) and len(synthetic_values) > 0:
            print(f"Warning: Convolution mode '{mode}' results in a different length ({len(synthetic_values)}) "
                  f"than input ({len(rc_series.index)}). Index alignment will be approximate.")
            # The 'valid' output starts after (len(wavelet) - 1) // 2 samples of rc_series
            start_idx_offset = (len(wavelet_values) - 1) // 2
            if len(rc_series.index) >= start_idx_offset + len(synthetic_values):
                 output_index = rc_series.index[start_idx_offset : start_idx_offset + len(synthetic_values)]
            else: # Fallback if calculation is off or input too short for 'valid'
                 output_index = pd.RangeIndex(start=0, stop=len(synthetic_values))
        elif len(synthetic_values) == 0: # 'valid' convolution resulted in empty output
            output_index = pd.Index([])


    synthetic_series_name = f"Synthetic_{rc_series.name}" if rc_series.name else "Synthetic"
    # Ensure output_index has a name if possible
    if hasattr(output_index, 'name') and output_index.name is None and hasattr(rc_series.index, 'name') and rc_series.index.name is not None:
        output_index.name = rc_series.index.name
    elif not hasattr(output_index, 'name') and hasattr(rc_series.index, 'name') and rc_series.index.name is not None:
        # If output_index is a basic np.ndarray (should not happen with pd.Index/RangeIndex)
        # this line would error. It's more for pd.Index objects.
        pass


    return pd.Series(synthetic_values, index=output_index, name=synthetic_series_name)