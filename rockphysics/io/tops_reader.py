"""
Tops Reader Module

This module provides functionality to read formation top data from files.
"""
import pandas as pd

def load_tops(filepath: str) -> pd.DataFrame:
    """
    Loads formation top data (name-depth pairs) from a CSV file.

    The CSV file must contain 'name' and 'depth' columns.
    Additional columns (e.g., 'tvd', 'source') will be preserved.

    Parameters
    ----------
    filepath : str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the tops data, sorted by depth.
        The DataFrame will have at least 'name' and 'depth' columns.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If 'name' or 'depth' columns are missing in the CSV.
    """
    try:
        tops_df = pd.read_csv(filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"Tops file not found: {filepath}")

    if 'name' not in tops_df.columns or 'depth' not in tops_df.columns:
        raise ValueError("Tops CSV must contain 'name' and 'depth' columns.")

    # Ensure depth is a numeric type
    tops_df['depth'] = pd.to_numeric(tops_df['depth'], errors='coerce')
    tops_df.dropna(subset=['depth'], inplace=True) # Remove tops where depth couldn't be parsed

    # Sort data by depth for proper interval definition
    tops_df = tops_df.sort_values(by='depth').reset_index(drop=True)
    
    return tops_df

