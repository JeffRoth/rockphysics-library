# rockphysics/io/well_io.py
"""
Well I/O Module

This module provides functionality to load and save a Well object
from/to Log ASCII Standard (LAS) files.
"""
import lasio
import pandas as pd
from typing import Optional
from ..core.well import Well 

def load_well_from_las(filepath: str) -> Well:
    """
    Loads data from a LAS file and returns a fully populated Well object.

    This function leverages the Well class's constructor, which is
    designed to parse a lasio object directly.

    Args:
        filepath (str): Path to the LAS file.

    Returns:
        Well: An instance of the Well class containing the loaded data.
    """
    try:
        # Read the LAS file using lasio
        las = lasio.read(filepath, autodetect_encoding=True)
        # The Well class constructor does all the heavy lifting
        return Well(las)
    except FileNotFoundError:
        raise FileNotFoundError(f"LAS file not found at: {filepath}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while loading '{filepath}': {e}")


def save_well_to_las(well: Well, filepath: str):
    """
    Saves a Well object's log data and metadata to a LAS file.

    Args:
        well (Well): The Well object to save.
        filepath (str): Path to save the new LAS file.
    """
    las = lasio.LASFile()
    
    # Set log data; lasio uses the DataFrame index as the depth curve
    las.set_data(well.logs)
    
    # Populate header from Well object attributes
    las.well.WELL.value = well.name
    las.well.UWI.value = well.api_uwi if well.api_uwi else ""
    las.well.NULL.value = well.null_value
    
    # Add other well header items if they exist in the well.well dict
    for key, item in well.well.items():
        if key not in ['WELL', 'UWI', 'NULL']: # Avoid overwriting primary fields
            las.well[key] = lasio.HeaderItem(key, item.get('unit',''), item.get('value',''), item.get('descr',''))

    # Add curve metadata (units and descriptions)
    for curve in las.curves:
        if curve.mnemonic in well.curve_info:
            curve.unit = well.curve_info[curve.mnemonic].get('unit', '')
            curve.descr = well.curve_info[curve.mnemonic].get('descr', '')

    try:
        las.write(filepath, version=2.0)
        print(f"Well '{well.name}' saved to {filepath}")
    except Exception as e:
        raise Exception(f"Error writing LAS file '{filepath}': {e}")