"""
Core Well Module

This module defines the Well class, which is used to represent
a well, including its header information, log data, formation tops,
and associated metadata.
"""
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

class TimeDomainAccessor:
    def __init__(self, well_obj):
        self._well = well_obj
        if 'TWT' not in self._well.logs.columns:
            raise AttributeError("Time-depth relationship 'TWT' not found in well.logs. Please calculate it first.")
        
        # Create a time-indexed view for convenience
        self._time_df = self._well.logs.set_index('TWT', drop=False)

    @property
    def tops(self) -> pd.DataFrame:
        """Returns the formation tops converted to Two-Way Time."""
        top_names = list(self._well.tops.keys())
        top_depths = list(self._well.tops.values())

        # If there are no tops, return an empty DataFrame with the correct columns.
        if not top_names:
            return pd.DataFrame(columns=['depth', 'twt'])

        # 2. Interpolate the TWT for each top's depth using the well's main log data.
        twt_values = np.interp(top_depths, self._well.logs.index, self._well.logs['TWT'])

        # 3. Create a new DataFrame from the results.
        #    This structure is useful for display and for the get_interval method.
        time_tops_df = pd.DataFrame(
            data={'depth': top_depths, 'twt': twt_values},
            index=pd.Index(top_names, name='name')
        )
        
        return time_tops_df

    def get_log(self, mnemonic: str) -> pd.Series:
        """Returns a single log curve indexed by TWT."""
        return self._time_df[mnemonic]

    def get_interval(self, top_name: str, base_name: str) -> pd.DataFrame:
        """Returns a slice of the log dataframe between two formation tops in the time domain."""
        time_tops = self.tops
        top_time = time_tops.loc[top_name, 'twt']
        base_time = time_tops.loc[base_name, 'twt']
        
        if top_time is None or base_time is None:
            raise ValueError("One or both formation tops not found.")
            
        return self._time_df[(self._time_df.index >= top_time) & (self._time_df.index <= base_time)]

class Well:
    def __init__(self, las_file):
        self.name: Optional[str] = str(las_file.well.WELL.value)
        # self.tops: pd.DataFrame = pd.DataFrame(columns=['name', 'depth']) # Formation tops
        self.tops: Dict[str, float] = {}
        self.api_uwi: Optional[str] = str(las_file.well.UWI.value)
        self.logs: pd.DataFrame = las_file.df()
        self.null_value: Optional[float] = las_file.well.NULL.value if las_file.well.NULL else -999.25
        self.version = {h.mnemonic: {'unit': h.unit, 'value': h.value, 'descr': h.descr} for h in las_file.version}
        self.well = {h.mnemonic: {'unit': h.unit, 'value': h.value, 'descr': h.descr} for h in las_file.well}
        self.parameter_info = {p.mnemonic: {'unit': p.unit, 'value': p.value, 'descr': p.descr} for p in las_file.params}
        self.log_info = {c.mnemonic: {'unit': c.unit, 'descr': c.descr} for c in las_file.curves}

        self._time_domain = None

    @property
    def time_domain(self) -> TimeDomainAccessor:
        """Accessor for working with logs in the time domain."""
        if self._time_domain is None:
            # Lazily instantiate the accessor the first time it's called
            self._time_domain = TimeDomainAccessor(self)
        return self._time_domain

    def add_top(self, name: str, depth: float):
        """Adds a new formation top to the well."""
        # Adding to a dictionary is much simpler
        self.tops[name] = depth

    def add_tops_from_df(self, tops_df: pd.DataFrame, name_col: str, depth_col: str):
        """
        Adds multiple formation tops from a pandas DataFrame.

        Args:
            tops_df (pd.DataFrame): DataFrame containing the tops information.
            name_col (str): The name of the column containing the top names.
            depth_col (str): The name of the column containing the top depths.
        """
        for _, row in tops_df.iterrows():
            name = row[name_col]
            depth = row[depth_col]
            self.add_top(name, depth)

    def get_log_names(self) -> list:
        """Returns a list of all log curve names in the well."""
        return list(self.logs.columns)

    def get_log(self, mnemonic: str) -> pd.Series:
        """Convenience function to get a single log curve."""
        return self.logs[mnemonic]
    
    def add_log(self, mnemonic: str, data: pd.Series):
        """Adds a new log curve to the well's log data."""
        if not isinstance(data, pd.Series):
            raise TypeError("Data must be a Pandas Series.")
        if data.index.name != self.logs.index.name:
            raise ValueError("Index of new log must match existing log index.")
        self.logs[mnemonic] = data

    def get_depth(self, depth_curve_name: Optional[str] = None) -> pd.Series:
        """
        Get the depth data from the DataFrame.
        Prioritizes a specified curve, then 'DEPT', then 'DEPTH', then the index.

        Args:
            depth_curve_name (str, optional): Name of the depth curve. Defaults to None.

        Returns:
            pd.Series: The depth data.
        """
        if depth_curve_name and depth_curve_name in self.logs.columns:
            return self.logs[depth_curve_name]
        elif "DEPT" in self.logs.columns: # Common LAS curve name for depth
            return self.logs["DEPT"]
        elif "DEPTH" in self.logs.columns: # Another common depth curve name
            return self.logs["DEPTH"]
        else:
            return pd.Series(self.logs.index)


    def get_intervals(self) -> List[Tuple[str, float, str, float]]:
        """
        Defines intervals from the well's sorted tops data.
        An interval is defined from one top to the next one below it.

        Returns:
            A list of tuples, where each tuple is (top_name, top_depth, base_name, base_depth).
        """
        if len(self.tops) < 2:
            return []
        
        # Sort the tops by depth to ensure correct interval definition
        sorted_tops = sorted(self.tops.items(), key=lambda item: item[1])
        
        intervals = []
        for i in range(len(sorted_tops) - 1):
            top_name, top_depth = sorted_tops[i]
            base_name, base_depth = sorted_tops[i+1]
            intervals.append((top_name, top_depth, base_name, base_depth))
            
        return intervals

    def summarize_intervals(
        self,
        vsh_curve: str,
        vsh_cutoff: float,
        phi_curve: Optional[str] = None,
        phi_cutoff: Optional[float] = None,
        sw_curve: Optional[str] = None,
        sw_cutoff: Optional[float] = None,
        avg_curves: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calculates properties for each interval defined by the well's tops.

        Args:
            vsh_curve: The mnemonic for the Volume of Shale curve.
            vsh_cutoff: The Vshale cutoff for defining net sand.
            phi_curve, phi_cutoff, sw_curve, sw_cutoff: Optional parameters for net pay.
            avg_curves: Optional list of curves for which to calculate gross average properties.

        Returns:
            A DataFrame summarizing the properties for each interval.
        """
        intervals = self.get_intervals()
        if not intervals:
            return pd.DataFrame(columns=['Top', 'Base', 'TopMD', 'BaseMD']).set_index('Top')

        summary_list = []
        for top_name, top_depth, base_name, base_depth in intervals:
            interval_df = self.logs[(self.logs.index >= top_depth) & (self.logs.index < base_depth)]
            
            if interval_df.empty:
                continue

            interval_summary = {'Top': top_name, 'Base': base_name, 'TopMD': top_depth, 'BaseMD': base_depth}

            # 1. Net Sand Calculation
            net_sand_results = self._calculate_interval_net_sand(interval_df, vsh_curve, vsh_cutoff)
            interval_summary.update(net_sand_results)

            # 2. Net Pay Calculation (optional)
            if all([phi_curve, phi_cutoff is not None, sw_curve, sw_cutoff is not None]):
                net_pay_results = self._calculate_interval_net_pay(
                    interval_df, vsh_curve, vsh_cutoff, phi_curve, phi_cutoff, sw_curve, sw_cutoff
                )
                interval_summary.update(net_pay_results)

            # 3. Average Property Calculation (optional)
            if avg_curves:
                avg_results = self._calculate_interval_average_properties(interval_df, avg_curves)
                interval_summary.update(avg_results)

            summary_list.append(interval_summary)

        if not summary_list:
            return pd.DataFrame(columns=['Top', 'Base', 'TopMD', 'BaseMD']).set_index('Top')
            
        return pd.DataFrame(summary_list).set_index('Top')

    # --- Internal Helper Methods for Interval Calculations ---

    def _calculate_interval_thickness(self, interval_df: pd.DataFrame) -> Tuple[float, float]:
        """Calculates gross thickness and median step for an interval DataFrame."""
        if interval_df.empty:
            return 0.0, 0.0
        depth_steps = np.diff(interval_df.index)
        if len(depth_steps) == 0:
            return 0.0, 0.0 # Single point interval has no thickness
        step = np.median(depth_steps)
        gross_thickness = (interval_df.index.max() - interval_df.index.min()) + step
        return gross_thickness, step

    def _calculate_interval_net_sand(self, interval_df: pd.DataFrame, vsh_curve: str, vsh_cutoff: float) -> Dict:
        """Calculates net sand properties for an interval."""
        gross_thickness, step = self._calculate_interval_thickness(interval_df)
        if gross_thickness == 0:
            return {'gross_thickness': 0.0, 'net_sand': 0.0, 'ntg_sand': np.nan}
        
        vsh = interval_df.get(vsh_curve)
        if vsh is None:
            return {'gross_thickness': gross_thickness, 'net_sand': np.nan, 'ntg_sand': np.nan}
            
        net_sand_samples = vsh[vsh < vsh_cutoff].count()
        net_sand_thickness = net_sand_samples * step
        ntg_sand = net_sand_thickness / gross_thickness if gross_thickness > 0 else np.nan
        
        return {'gross_thickness': gross_thickness, 'net_sand': net_sand_thickness, 'ntg_sand': ntg_sand}

    def _calculate_interval_net_pay(self, interval_df, vsh_curve, vsh_cutoff, phi_curve, phi_cutoff, sw_curve, sw_cutoff) -> Dict:
        """Calculates net pay properties for an interval."""
        _, step = self._calculate_interval_thickness(interval_df)
        pay_mask = (interval_df.get(vsh_curve, 1) < vsh_cutoff) & \
                   (interval_df.get(phi_curve, 0) > phi_cutoff) & \
                   (interval_df.get(sw_curve, 1) < sw_cutoff)
        net_pay_thickness = pay_mask.sum() * step
        return {'net_pay': net_pay_thickness}
        
    def _calculate_interval_average_properties(self, interval_df: pd.DataFrame, avg_curves: List[str]) -> Dict:
        """Calculates average properties for specified curves over an interval."""
        averages = {}
        for curve in avg_curves:
            avg_name = f"{curve}_avg"
            if curve in interval_df:
                averages[avg_name] = interval_df[curve].mean()
            else:
                averages[avg_name] = np.nan
        return averages

    def __repr__(self):
        """Returns an unambiguous string representation of the Well object."""
        # Correctly access the 'UWI' value from the self.well dictionary in a safe way.
        uwi = self.well.get('UWI', {}).get('value', 'N/A')
        return f"Well(UWI: {uwi}, Logs: {list(self.logs.columns)})"
