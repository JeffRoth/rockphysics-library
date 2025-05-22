import lasio
import pandas as pd
from ..core import LogData # Use relative import

def load_las_file(filepath: str) -> LogData:
    """
    Load log data from a LAS file.

    Args:
        filepath (str): Path to the LAS file.

    Returns:
        LogData: An instance of LogData containing the loaded data.

    Raises:
        FileNotFoundError: If the LAS file does not exist.
        lasio.exceptions.LASException: If there is an error reading the LAS file.
    """
    try:
        las = lasio.read(filepath)
        df = las.df()
        # It's common for LAS files to use the first curve (often depth) as index.
        # lasio.read().df() already sets the depth curve as index.
        # If 'DEPTH' column is desired explicitly, it can be added from index:
        # if 'DEPTH' not in df.columns and df.index.name is not None and ('DEPT' in df.index.name.upper() or 'DEPTH' in df.index.name.upper()):
        #    df['DEPTH'] = df.index 
        return LogData(df)
    except FileNotFoundError:
        raise FileNotFoundError(f"LAS file not found at: {filepath}")
    except lasio.exceptions.LASException as e:
        raise lasio.exceptions.LASException(f"Error reading LAS file '{filepath}': {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while loading '{filepath}': {e}")

def save_las_file(log_data: LogData, filepath: str, use_index_as_depth: bool = True):
    """
    Save the log data to a LAS file.

    Args:
        log_data (LogData): The LogData object to save.
        filepath (str): Path to save the LAS file.
        use_index_as_depth (bool): If true, reset index to be a column (if index is named e.g. 'DEPTH'),
                                   or save the current index as the depth curve.
                                   lasio typically uses the DataFrame's index as the depth curve.
    """
    las = lasio.LASFile()
    df_to_save = log_data.data.copy() # Work with a copy
    # lasio.set_data() expects the depth to be the index of the DataFrame.
    # If use_index_as_depth is True and index is not already depth, this might need adjustment
    # based on how LogData is structured (e.g. if 'DEPTH' is a column or the index).
    # Assuming log_data.data.index is the depth:
    if use_index_as_depth and not isinstance(df_to_save.index, pd.MultiIndex):
        if df_to_save.index.name is None: # Ensure index has a name for LAS
            df_to_save.index.name = "DEPTH" 
    # If 'DEPTH' is a column and should be index:
    # if 'DEPTH' in df_to_save.columns and not use_index_as_depth:
    #    df_to_save = df_to_save.set_index('DEPTH')
        
    las.set_data(df_to_save)
    try:
        las.write(filepath, version=2.0) # Specify LAS version for consistency
    except Exception as e:
        raise Exception(f"Error writing LAS file '{filepath}': {e}")