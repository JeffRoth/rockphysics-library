# rockphysics/core/project.py
"""
Project Module

This module defines the Project class, which serves as a container
for managing a collection of Well objects.
"""
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Callable
 
from .well import Well

class Project:
    """
    A class to manage a collection of well objects for multi-well analysis.
    """
    def __init__(self, name: str, wells: Optional[List] = None):
        """
        Args:
            name (str): The name of the project or study area.
            wells (Optional[List[Well]]): An optional list of Well objects to initialize with.
        """
        self.name: str = name
        self.wells: Dict[str, Well] = {}
        if wells:
            for well in wells:
                self.add_well(well)

    def add_well(self, well: Well, name_override: Optional[str] = None):
        """
        Adds a well to the project, keyed by its name.

        Args:
            well (Well): The Well object to add.
            name_override (Optional[str]): A name to use if the well's own name is not suitable (e.g., filename).
        
        Raises:
            ValueError: If the well cannot be given a unique name.
        """
        key = well.name or name_override
        if not key:
            raise ValueError("Well cannot be added to project because it has no name.")
        if key in self.wells:
            print(f"Warning: Well with name '{key}' already exists in the project. Overwriting.")
        self.wells[key] = well

    def get_well(self, name: str) -> Optional[Well]:
        """Retrieves a well from the project by its name."""
        return self.wells.get(name)

    def apply_calculation(self, calculation_func: Callable, **kwargs):
        """
        Applies a calculation function from another module to all wells in the project.

        This is a powerful way to run batch processes, e.g., calculating VSH for all wells.

        Args:
            calculation_func (Callable): The function to apply (e.g., pp.calculate_vshale_linear).
                                         This function must accept a Well object as its first argument.
            **kwargs: Keyword arguments to be passed to the calculation_func.
        """
        for well in self.wells.values():
            try:
                new_curve = calculation_func(well, **kwargs)
                well.logs[new_curve.name] = new_curve
                print(f"Successfully applied '{calculation_func.__name__}' to well '{well.name}'.")
            except Exception as e:
                print(f"Could not apply '{calculation_func.__name__}' to well '{well.name}': {e}")

    def crossplot_interval(
        self, 
        top_name: str, 
        base_name: str, 
        x_curve: str, 
        y_curve: str, 
        color_by_curve: Optional[str] = None
    ):
        """
        Generates a crossplot for a specific interval across all wells in the project.

        Args:
            top_name (str): The name of the formation top defining the interval start.
            base_name (str): The name of the formation top defining the interval base.
            x_curve (str): The mnemonic of the log for the x-axis.
            y_curve (str): The mnemonic of the log for the y-axis.
            color_by_curve (Optional[str]): Mnemonic of the log to use for color-coding the points.
                                             If None, all points are the same color.
        """
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 8))

        for name, well in self.wells.items():
            try:
                # Use the well's get_interval method (you'll need to add/verify this in your Well class)
                interval_df = well.get_interval(top_name, base_name)
                
                if not all(c in interval_df.columns for c in [x_curve, y_curve]):
                    print(f"Warning: Skipping well {well.name} (UWI: {well.uwi}) - missing required curves for crossplot.")
                    continue

                if color_by_curve and color_by_curve in interval_df.columns:
                    # Plot with a color scale
                    scatter = ax.scatter(interval_df[x_curve], interval_df[y_curve], c=interval_df[color_by_curve],
                                         label=well.name, alpha=0.7, cmap='viridis')
                else:
                    # Plot with a single color
                    ax.scatter(interval_df[x_curve], interval_df[y_curve], label=well.name, alpha=0.7)

            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping well {well.name} (UWI: {well.uwi}) for crossplot: {e}")

        ax.set_xlabel(x_curve)
        ax.set_ylabel(y_curve)
        ax.set_title(f"Crossplot of {y_curve} vs. {x_curve}\nInterval: {top_name} to {base_name}")
        ax.legend()
        ax.grid(True)
        
        # If we used a color scale, add a colorbar
        if color_by_curve and 'scatter' in locals():
            cbar = fig.colorbar(scatter, ax=ax)
            cbar.set_label(color_by_curve)
            
        plt.show()

    def __repr__(self):
        return f"Project(Name: '{self.name}', Wells: {len(self.wells)})"
