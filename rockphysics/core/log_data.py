import pandas as pd
import numpy as np
from typing import Callable, Optional

class LogData:
    """
    A class to hold and manipulate well log data.
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initialize the LogData object with a DataFrame.

        Args:
            data (pd.DataFrame): DataFrame containing log data. 
                                 The index should represent depth.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input 'data' must be a Pandas DataFrame.")
        self.data = data
        self.domain = self._infer_domain(data.index.name)

    def _infer_domain(self, index_name: Optional[str]) -> str:
        """
        Infers the domain (depth or time) from the index name.
        """
        if index_name:
            name_lower = index_name.lower()
            if "depth" or "dept" in name_lower:
                return "depth"
            elif "time" in name_lower or "twt" in name_lower:
                return "time"
        return "unknown" # Default if domain cannot be clearly inferred

    def get_curve_names(self) -> list:
        """
        Get a list of the names of all curves in the LogData object.

        Returns:
            list: A list of curve names.
        """
        return list(self.data.columns)

    def get_curve(self, log_name: str) -> pd.Series:
        """
        Get a specific log curve by name.

        Args:
            log_name (str): Name of the log curve.

        Returns:
            pd.Series: The requested log curve.

        Raises:
            ValueError: If the log curve is not found.
        """
        if log_name in self.data.columns:
            return self.data[log_name]
        else:
            raise ValueError(f"Log curve '{log_name}' not found in data.")

    def rename_curve(self, old_name: str, new_name: str) -> None:
        """
        Rename a log curve.

        Args:
            old_name (str): The current name of the curve.
            new_name (str): The new name for the curve.

        Raises:
            ValueError: If the old curve name is not found.
        """
        if old_name not in self.data.columns:
            raise ValueError(f"Curve '{old_name}' not found.")
        self.data.rename(columns={old_name: new_name}, inplace=True)

    def add_curve(self, log_name: str, data: pd.Series, sort_index: bool = True, drop_duplicates: bool = True, reset_index: bool = False):
        """
        Add a new log curve to the DataFrame.

        Args:
            log_name (str): Name of the new log curve.
            data (pd.Series): The data for the new log curve.
            sort_index(bool): if true sort the index.
            drop_duplicates(bool): if true drop duplicate index values.
            reset_index(bool): if true reset the index.

        Raises:
            ValueError: if the passed in pandas Series index does not match the LogData index.
        """
        if not data.index.equals(self.data.index):
            raise ValueError("The provided pandas Series index does not match LogData index.")

        self.data[log_name] = data
        if sort_index:
            self.data = self.data.sort_index()

        if drop_duplicates:
             if self.data.index.has_duplicates:
                self.data = self.data.loc[~self.data.index.duplicated(keep='first')]
        if reset_index:
            self.data = self.data.reset_index(drop=True)

    def remove_curve(self, log_name: str):
        """
        Remove a log curve from the DataFrame.

        Args:
            log_name (str): Name of the log curve to remove.

        Raises:
            ValueError: If the log curve is not found.
        """
        if log_name in self.data.columns:
            del self.data[log_name]
        else:
            raise ValueError(f"Log curve '{log_name}' not found in data.")

    def get_depth(self, depth_curve_name: Optional[str] = None) -> pd.Series:
        """
        Get the depth data from the DataFrame.
        Prioritizes a specified curve, then 'DEPT', then 'DEPTH', then the index.

        Args:
            depth_curve_name (str, optional): Name of the depth curve. Defaults to None.

        Returns:
            pd.Series: The depth data.
        """
        if depth_curve_name and depth_curve_name in self.data.columns:
            return self.data[depth_curve_name]
        elif "DEPT" in self.data.columns: # Common LAS curve name for depth
            return self.data["DEPT"]
        elif "DEPTH" in self.data.columns: # Another common depth curve name
            return self.data["DEPTH"]
        else:
            return pd.Series(self.data.index)

    def apply_function(self, curve: str, func: Callable) -> pd.Series:
        """
        Apply a function to a specific log curve.

        Args:
            curve (str): Name of the log curve.
            func (callable): Function to apply to the log curve.

        Returns:
            pd.Series: The result of applying the function.

        Raises:
            ValueError: If the log curve is not found.
        """
        if curve in self.data.columns:
            return func(self.data[curve])
        else:
            raise ValueError(f"Log curve '{curve}' not found in data.")

    def __iter__(self):
        """Iterator for LogData object, yielding curve name and Series."""
        for curve_name, series in self.data.items():
            yield curve_name, series

    def __repr__(self):
        return (f"<LogData object with curves: {self.get_curve_names()}, "
                f"domain: {self.domain}, and {len(self.data)} data points. "
                f"Index: {self.data.index.name}>")