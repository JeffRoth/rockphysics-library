import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml
import os
from typing import Optional, Callable
from ..core import LogData # Use relative import

def plot_logs(log_data: LogData, min_val_display, max_val_display, *tracks):
    """
    Plots an arbitrary number of well logs from a single LogData object.

    Args:
        log_data (LogData): The LogData object containing the well logs.
        min_val_display (float or 'auto'): Minimum value of the y-axis (depth or time) for display.
                                            'auto' starts at the first valid index of the data.
        max_val_display (float or 'auto'): Maximum value of the y-axis (depth or time) for display.
                                            'auto' ends at the last valid index of the data.
        *tracks (str): Comma-separated list of log curve names to display.
            
    EXAMPLE USAGE:
        plot_logs(my_log_data, 'auto', 'auto', 'CALI', 'GR', 'RESDEP')
        plot_logs(my_time_log_data, 0, 500, 'GR_time', 'RHOB_time', 'RC_TIME')
    """

    dataframe = log_data.data # Access the internal DataFrame

    # Configuration for log display (colors, scales, etc.)
    default_log_color = 'blue'
    log_line_width = 0.7
    track_title_size = 8 
    tick_label_size = 7  
    y_axis_label_size = 9 
    vsh_fill_cutoff = 0.5 # Default VSH fill cutoff
    
    log_dict = {}
    
    try:
        import rockphysics
        package_root = os.path.dirname(os.path.dirname(rockphysics.__file__)) 
        config_path_attempt1 = os.path.join(package_root, "config.yaml")

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        config_path_attempt2 = os.path.join(current_file_dir, "..", "..", "config.yaml") 
        config_path_attempt3 = os.path.join(current_file_dir, "..", "config.yaml") 

        config_path = None
        if os.path.exists(config_path_attempt1):
            config_path = config_path_attempt1
        elif os.path.exists(config_path_attempt2):
            config_path = config_path_attempt2
        elif os.path.exists(config_path_attempt3):
            config_path = config_path_attempt3
        
        if config_path:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            log_dict = config.get("log_display_settings", {})
            vsh_fill_cutoff = log_dict.get("VSH", {}).get("fill_cutoff", 0.5) # Get VSH specific or global
            if "VSH" not in log_dict: # If VSH section doesn't exist, check for global
                 vsh_fill_cutoff = config.get("defaults", {}).get("vsh_fill_cutoff", 0.5)
            print(f"Loaded display settings from: {config_path}")
        else:
            print(f"Warning: Configuration file 'config.yaml' not found. Using default plotting parameters.")
            
    except ImportError:
        print("Warning: 'rockphysics' package not found for robust config path detection. Trying relative paths for 'config.yaml'.")
    except FileNotFoundError:
        print(f"Warning: Configuration file 'config.yaml' not found. Using default plotting parameters.")
    except Exception as e:
        print(f"Warning: Error loading 'config.yaml': {e}. Using default plotting parameters.")


    num_tracks = len(tracks)
    if num_tracks == 0:
        print("No tracks specified for plotting.")
        return
        
    fig, axes = plt.subplots(1, num_tracks, figsize=(num_tracks * 2.0, 10), 
                            sharey=True)
    if num_tracks == 1: 
        axes = [axes]
    
    # Determine y-axis limits
    if dataframe.empty:
        min_y = 0
        max_y = 100 
    else:
        min_y = dataframe.index.min()
        max_y = dataframe.index.max()

    if min_val_display == 'auto':
        min_val_display = min_y
    if max_val_display == 'auto':
        max_val_display = max_y
    
    # Determine y-axis label based on LogData domain
    y_label = "Index" 
    y_unit = ""
    if hasattr(log_data, 'domain'):
        if log_data.domain == "depth":
            y_label = "Depth"
            if dataframe.index.name and '(' in dataframe.index.name and ')' in dataframe.index.name:
                y_unit = dataframe.index.name[dataframe.index.name.find('(')+1:dataframe.index.name.find(')')]
            else:
                y_unit = "m" 
            y_label = f"{y_label} ({y_unit})"
        elif log_data.domain == "time":
            y_label = "Time"
            if dataframe.index.name and '(' in dataframe.index.name and ')' in dataframe.index.name:
                y_unit = dataframe.index.name[dataframe.index.name.find('(')+1:dataframe.index.name.find(')')]
            else:
                y_unit = "ms" 
            y_label = f"{y_label} ({y_unit})"
    elif dataframe.index.name: 
         y_label = dataframe.index.name

    # plot each track in turn
    for i, track_name in enumerate(tracks):
        ax = axes[i] 
        if track_name not in dataframe.columns:
            print(f"Warning: Track '{track_name}' not found in LogData. Skipping.")
            ax.text(0.5, 0.5, f"Track '{track_name}'\nnot found", ha='center', va='center', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            if i == 0: 
                 ax.set_ylabel(y_label, fontsize=y_axis_label_size)
            continue

        log_series = dataframe[track_name].copy() # Use a copy to avoid SettingWithCopyWarning on fillna
        
        # Get log-specific display settings from config or use defaults
        log_info = log_dict.get(track_name.upper(), {}) 
        log_color = log_info.get('color', default_log_color)
        min_log_val_cfg = log_info.get('min_value')
        max_log_val_cfg = log_info.get('max_value')
        log_scale = log_info.get('scale', 'linear').lower() 
        plot_style = log_info.get('plot_style', 'line').lower()

        # Determine min/max for the curve, preferring config values
        current_min_log = log_series.min() if pd.isna(min_log_val_cfg) else min_log_val_cfg
        current_max_log = log_series.max() if pd.isna(max_log_val_cfg) else max_log_val_cfg
        
        # Handle empty or single-point series, or if min/max are still NaN
        if pd.isna(current_min_log) or pd.isna(current_max_log) or current_min_log == current_max_log:
            valid_log_series = log_series.dropna()
            if not valid_log_series.empty:
                current_min_log = valid_log_series.min()
                current_max_log = valid_log_series.max()
                if current_min_log == current_max_log: 
                    current_min_log = current_min_log - abs(current_min_log * 0.1) if current_min_log != 0 else -0.5
                    current_max_log = current_max_log + abs(current_max_log * 0.1) if current_max_log != 0 else 0.5
            else: # Series is all NaN or empty
                current_min_log = 0
                current_max_log = 1
            
            if current_min_log == current_max_log: # Still equal (e.g. both zero after adjustment)
                current_min_log -= 0.5
                current_max_log += 0.5
        
        # For spike plots, ensure limits are symmetrical around 0 if not explicitly set otherwise
        if plot_style == 'spike' and (pd.isna(min_log_val_cfg) or pd.isna(max_log_val_cfg)):
            max_abs_val = np.nanmax(np.abs(log_series.dropna()))
            if pd.isna(max_abs_val) or max_abs_val == 0:
                max_abs_val = 0.1 # Default small range for all-zero or all-NaN RC
            current_min_log = -max_abs_val
            current_max_log = max_abs_val


        # Plotting the curve based on plot_style
        if plot_style == 'spike':
            # For stem plot, NaNs should be handled by the function itself (not plotted)
            # However, ensure 'bottom' is correctly interpreted.
            # `bottom=0` means stems go from/to x=0 for horizontal orientation.
            (markers, stemlines, baseline) = ax.stem(
                dataframe.index, log_series.fillna(0), # Fill NaN with 0 for stem to draw to baseline
                orientation='horizontal',
                bottom=0, # This is the reference for the x-values of the stems
                linefmt=None,
                markerfmt=" ", # No markers at the tip of spikes
                basefmt='k-'
            )
            # plt.setp(baseline, color='black', linewidth=0.5, linestyle='-') # Style the zero line
            plt.setp(stemlines, color=log_color, linewidth=log_line_width)

        elif log_scale == 'log':
            ax.semilogx(log_series, dataframe.index, linewidth=log_line_width, color=log_color)
        else: # Default to linear line plot
            ax.plot(log_series, dataframe.index, linewidth=log_line_width, color=log_color)
        
        ax.set_ylim(max_val_display, min_val_display) # Inverted y-axis
        
        # X-axis (track) styling
        ax.spines["top"].set_edgecolor(log_color)
        ax.spines["top"].set_position(("axes", 1.02))
        ax.set_xlabel(track_name, fontsize=track_title_size, color=log_color)
        ax.tick_params(axis='x', labelsize=tick_label_size, colors=log_color)
        ax.tick_params(axis='y', labelsize=tick_label_size) 
        
        ax.set_xlim(current_min_log, current_max_log)
        
        log_xticks_cfg = log_info.get('xticks')
        if log_xticks_cfg:
            ax.set_xticks(log_xticks_cfg)
        elif plot_style == 'spike': # Auto-ticks for spike plots, ensuring 0 is included
            ax.set_xticks(np.linspace(current_min_log, current_max_log, 3 if current_min_log * current_max_log < 0 else 2))


        ax.grid(which='major', color='lightgrey', linestyle='-')
        ax.xaxis.set_ticks_position("top")
        ax.xaxis.set_label_position("top")

        # Special fills (only for line plots, not for spike plots)
        if plot_style == 'line':
            if 'VSH' in track_name.upper() or 'VCLAY' in track_name.upper(): 
                fill_min_vsh = current_min_log 
                ax.fill_betweenx(
                    dataframe.index,
                    log_series,
                    1, 
                    where=log_series < vsh_fill_cutoff, 
                    facecolor='yellow',
                    interpolate=True
                )
                ax.fill_betweenx(
                    dataframe.index,
                    log_series,
                    1,
                    where=log_series >= vsh_fill_cutoff, 
                    facecolor='grey',
                    interpolate=True
                )

            if 'FLAG' in track_name.upper(): 
                ax.fill_betweenx(
                    dataframe.index,
                    current_min_log,
                    log_series, 
                    where=log_series > 0, 
                    facecolor='red',
                    interpolate=False,
                    alpha=0.3
                )
                
            if 'SYNTHETIC' in track_name.upper(): 
                ax.fill_betweenx(
                    dataframe.index,
                    0,
                    log_series, 
                    where=log_series > 0, 
                    facecolor='black',
                    interpolate=False
                )

        # Set y-axis label only for the first track
        if i == 0:
            ax.set_ylabel(y_label, fontsize=y_axis_label_size)
        else: 
            ax.tick_params(axis='y', labelleft=False)


    fig.suptitle(f"Log Plot (Index: {log_data.data.index.name})", fontsize=12, y=0.98) 
    plt.tight_layout(rect=[0, 0, 1, 0.96]) 
    plt.show()