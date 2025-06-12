import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml
import os
from typing import Optional, Callable, List
from ..core.well import Well
# from ..core import LogData # Use relative import

def plot_logs(log_data: pd.DataFrame, min_val_display, max_val_display, *tracks):
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

    # dataframe = log_data.data # Access the internal DataFrame
    dataframe = log_data

    # Attempt to import and instantiate LogNomenclature for log type styling
    log_nomenclature_instance = None # This will hold the LogNomenclature instance
    try:
        from ..utils import nomenclature as nomenclature_py_module # Import the .py file as a module object

        if hasattr(nomenclature_py_module, 'LogNomenclature'):
            NomenclatureClass = getattr(nomenclature_py_module, 'LogNomenclature')
            if callable(NomenclatureClass):
                try:
                    instance = NomenclatureClass() # Instantiate
                    if hasattr(instance, 'get_log_type') and callable(instance.get_log_type):
                        log_nomenclature_instance = instance # Store the usable instance
                        print("LogNomenclature instance created successfully. Will use it for type-based styling.")
                    else:
                        print("Warning: LogNomenclature class instantiated, but its 'get_log_type' method is missing or not callable. Proceeding without type-based styling.")
                except Exception as e_init:
                    print(f"Warning: Error initializing LogNomenclature class: {e_init}. Proceeding without type-based styling.")
            else:
                print("Warning: 'LogNomenclature' found in nomenclature module, but it's not a callable class. Proceeding without type-based styling.")
        else:
            print("Warning: Nomenclature module loaded, but 'LogNomenclature' class not found within it. Proceeding without type-based styling.")

    except ImportError:
        print("Warning: Nomenclature module (rockphysics.utils.nomenclature) not found. "
              "Plotting will rely solely on 'plot_config.yaml' mnemonic settings and internal defaults.")
    except Exception as e:
        print(f"Warning: General error during nomenclature setup: {e}. "
              "Plotting will rely solely on 'plot_config.yaml' mnemonic settings and internal defaults.")

    # Configuration for log display (colors, scales, etc.)
    track_title_size = 8 
    tick_label_size = 7  
    y_axis_label_size = 9 

    # These will be primary fallbacks, ideally overridden by plot_config.yaml "defaults"
    default_vsh_fill_cutoff = 0.5
    default_vsh_sand_fill_color = 'yellow'
    default_vsh_shale_fill_color = 'grey'
    default_synthetic_fill_color = 'black'
    default_flag_fill_color = 'red'
    default_flag_fill_alpha = 0.3
    default_log_color = 'blue'
    default_log_line_width = 0.7

    log_type_display_settings = {}
    default_display_settings = {}
    config_defaults = {}
    
    try:
        import rockphysics
        package_root = os.path.dirname(os.path.dirname(rockphysics.__file__)) 
        config_path_attempt1 = os.path.join(package_root, "resources/plot_config.yaml")

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        config_path_attempt2 = os.path.join(current_file_dir, "..", "..", "/resources/plot_config.yaml") 
        config_path_attempt3 = os.path.join(current_file_dir, "..", "resources/plot_config.yaml") 

        config_path = None
        if os.path.exists(config_path_attempt1):
            config_path = config_path_attempt1
        elif os.path.exists(config_path_attempt2):
            config_path = config_path_attempt2
        elif os.path.exists(config_path_attempt3):
            config_path = config_path_attempt3
        
        if config_path:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
            log_type_display_settings = config_data.get("log_display_settings", {})
            default_display_settings = config_data.get("defaults", {})
            config_defaults = config_data.get("defaults", {})
            print(f"Loaded display settings from: {config_path}")
        else:
            print(f"Warning: Configuration file 'plot_config.yaml' not found. Using default plotting parameters.")
            
    except ImportError:
        print("Warning: 'rockphysics' package not found for robust config path detection. Trying relative paths for 'config.yaml'.")
    except FileNotFoundError:
        print(f"Warning: Configuration file 'plot_config.yaml' not found. Using default plotting parameters.")
    except Exception as e:
        print(f"Warning: Error loading 'plot_config.yaml': {e}. Using default plotting parameters.")

    # Apply global defaults from config file, falling back to hardcoded defaults
    default_log_color = config_defaults.get('default_log_color', default_log_color)
    log_line_width = config_defaults.get('log_line_width', default_log_line_width)
    track_title_size = config_defaults.get('track_title_size', track_title_size)
    tick_label_size = config_defaults.get('tick_label_size', tick_label_size)
    y_axis_label_size = config_defaults.get('y_axis_label_size', y_axis_label_size)
    default_vsh_fill_cutoff = config_defaults.get('vsh_fill_cutoff', default_vsh_fill_cutoff)
    default_vsh_sand_fill_color = config_defaults.get('vsh_sand_fill_color', default_vsh_sand_fill_color)
    default_vsh_shale_fill_color = config_defaults.get('vsh_shale_fill_color', default_vsh_shale_fill_color)
    default_synthetic_fill_color = config_defaults.get('synthetic_fill_color', default_synthetic_fill_color)
    default_flag_fill_color = config_defaults.get('flag_fill_color', default_flag_fill_color)
    default_flag_fill_alpha = config_defaults.get('flag_fill_alpha', default_flag_fill_alpha)

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
    
    # Determine y-axis label based on LogData domain (depth or time)
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
        

        # Build current_log_info: Layering global defaults, type-based, then mnemonic-specific
        current_log_info = {
            'color': default_log_color,
            'scale': 'linear',
            'plot_style': 'line',
            'min_value': None,
            'max_value': None,
            'xticks': None,
            'fill_cutoff': default_vsh_fill_cutoff, # For VSH/VCLAY
            'vsh_sand_fill_color': default_vsh_sand_fill_color,
            'vsh_shale_fill_color': default_vsh_shale_fill_color,
            'synthetic_fill_color': default_synthetic_fill_color,
            'flag_fill_color': default_flag_fill_color,
            'flag_fill_alpha': default_flag_fill_alpha,
        }

        current_log_info.update(default_display_settings) # Start with global defaults

        if log_nomenclature_instance:
            try:
                log_type = log_nomenclature_instance.get_log_type(track_name)

                if log_type:
                    type_settings = log_type_display_settings.get(log_type.upper(), {})
                    current_log_info.update(type_settings)
            except Exception as e_nom:
                print(f"Warning: Error getting log type for '{track_name}' from nomenclature module: {e_nom}")

        # Extract final settings for the current track
        log_color = current_log_info['color']
        min_log_val_cfg = current_log_info.get('min_value')
        max_log_val_cfg = current_log_info.get('max_value')
        log_scale = current_log_info.get('scale', 'linear').lower()
        plot_style = current_log_info.get('plot_style', 'line').lower()

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
        
        # log_xticks_cfg = log_info.get('xticks')
        log_xticks_cfg = current_log_info.get('xticks')
        if log_xticks_cfg:
            ax.set_xticks(log_xticks_cfg)
        elif plot_style == 'spike': # Auto-ticks for spike plots, ensuring 0 is included
            ax.set_xticks(np.linspace(current_min_log, current_max_log, 3 if current_min_log * current_max_log < 0 else 2))


        ax.grid(which='major', color='lightgrey', linestyle='-')
        ax.xaxis.set_ticks_position("top")
        ax.xaxis.set_label_position("top")

        # Special fills (only for line plots, not for spike plots)
        if plot_style == 'line':
            # if 'VSH' in track_name.upper() or 'VCLAY' in track_name.upper(): 
            if log_type == 'VOLUME_SHALE' or log_type == 'VOLUME_CLAY':
                # fill_min_vsh = current_min_log 
                track_vsh_fill_cutoff = current_log_info.get('fill_cutoff', default_vsh_fill_cutoff)
                sand_color = current_log_info.get('vsh_sand_fill_color', default_vsh_sand_fill_color)
                shale_color = current_log_info.get('vsh_shale_fill_color', default_vsh_shale_fill_color)
                ax.fill_betweenx(
                    dataframe.index,
                    log_series,
                    1, 
                    # where=log_series < vsh_fill_cutoff, 
                    # facecolor='yellow',
                    where=log_series < track_vsh_fill_cutoff,
                    facecolor=sand_color,
                    interpolate=True
                )
                ax.fill_betweenx(
                    dataframe.index,
                    log_series,
                    1,
                    # where=log_series >= vsh_fill_cutoff, 
                    # facecolor='grey',
                    where=log_series >= track_vsh_fill_cutoff,
                    facecolor=shale_color,
                    interpolate=True
                )

            # if 'FLAG' in track_name.upper():
            if log_type == 'FLAG':
                flag_color = current_log_info.get('flag_fill_color', default_flag_fill_color)
                flag_alpha = current_log_info.get('flag_fill_alpha', default_flag_fill_alpha)
                ax.fill_betweenx(
                    dataframe.index,
                    current_min_log,
                    log_series, 
                    where=log_series > 0, 
                    # facecolor='red',
                    facecolor=flag_color,
                    interpolate=False,
                    # alpha=0.3
                    alpha=flag_alpha
                )

            if log_type == 'FACIES':
                unique_facies_values = sorted(log_series.dropna().unique())
                num_unique_facies = len(unique_facies_values)

                if num_unique_facies == 0:
                    print(f"Warning: No valid facies values found in track '{track_name}'. Skipping facies fill.")
                else:
                    # Generate a color map for the unique facies values
                    if num_unique_facies <= 10:
                        # Use a fixed set of colors for up to 10 unique facies
                        cmap = plt.cm.get_cmap('tab10', num_unique_facies)
                    elif num_unique_facies <= 20:
                        # Use a fixed set of colors for up to 20 unique facies
                        cmap = plt.cm.get_cmap('tab20', num_unique_facies)
                    else:
                        # Use a viridis colormap for more than 20 unique facies
                        cmap = plt.cm.viridis
                    # Create a mapping from facies value to color
                    facies_color_map = {facies_value: cmap(i % cmap.N) for i, facies_value in enumerate(unique_facies_values)}
                
                    for facies_val, color_val in facies_color_map.items():
                        ax.fill_betweenx(
                            dataframe.index,
                            0,  # Fill from the left edge of the track
                            log_series,  # Fill to the log
                            where=(log_series == facies_val),
                            facecolor=color_val,
                            interpolate=False, # Crucial for discrete facies codes
                            # label=f'Facies {facies_val}' # For potential legend
                        )

            # if 'SYNTHETIC' in track_name.upper(): 
            if log_type == 'SYNTHETIC':
                synth_color = current_log_info.get('synthetic_fill_color', default_synthetic_fill_color)
                ax.fill_betweenx(
                    dataframe.index,
                    0,
                    log_series, 
                    where=log_series > 0, 
                    # facecolor='black',
                    facecolor=synth_color,
                    interpolate=False
                )

            if log_type == 'WATER_SATURATION':
                ax.fill_betweenx(
                    dataframe.index,
                    0,  # Fill from the left edge of the track
                    log_series, # Fill to the log
                    facecolor='blue',
                    interpolate=False
                )


        # Set y-axis label only for the first track
        if i == 0:
            ax.set_ylabel(y_label, fontsize=y_axis_label_size)
        else: 
            ax.tick_params(axis='y', labelleft=False)


    fig.suptitle(f"Log Plot (Index: {log_data.index.name})", fontsize=12, y=0.98) 
    plt.tight_layout(rect=[0, 0, 1, 0.96]) 
    plt.show()


def crossplot(log_data: pd.DataFrame, x_var, y_var, color, depth_top, depth_bottom):
    """
    Plots a crossplot of two logs.

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

    # dataframe = log_data.data # Access the internal DataFrame
    dataframe = log_data

    # Attempt to import and instantiate LogNomenclature for log type styling
    log_nomenclature_instance = None # This will hold the LogNomenclature instance
    try:
        from ..utils import nomenclature as nomenclature_py_module # Import the .py file as a module object

        if hasattr(nomenclature_py_module, 'LogNomenclature'):
            NomenclatureClass = getattr(nomenclature_py_module, 'LogNomenclature')
            if callable(NomenclatureClass):
                try:
                    instance = NomenclatureClass() # Instantiate
                    if hasattr(instance, 'get_log_type') and callable(instance.get_log_type):
                        log_nomenclature_instance = instance # Store the usable instance
                        print("LogNomenclature instance created successfully. Will use it for type-based styling.")
                    else:
                        print("Warning: LogNomenclature class instantiated, but its 'get_log_type' method is missing or not callable. Proceeding without type-based styling.")
                except Exception as e_init:
                    print(f"Warning: Error initializing LogNomenclature class: {e_init}. Proceeding without type-based styling.")
            else:
                print("Warning: 'LogNomenclature' found in nomenclature module, but it's not a callable class. Proceeding without type-based styling.")
        else:
            print("Warning: Nomenclature module loaded, but 'LogNomenclature' class not found within it. Proceeding without type-based styling.")

    except ImportError:
        print("Warning: Nomenclature module (rockphysics.utils.nomenclature) not found. "
              "Plotting will rely solely on 'plot_config.yaml' mnemonic settings and internal defaults.")
    except Exception as e:
        print(f"Warning: General error during nomenclature setup: {e}. "
              "Plotting will rely solely on 'plot_config.yaml' mnemonic settings and internal defaults.")

    # Configuration for log display (colors, scales, etc.)
    track_title_size = 8 
    tick_label_size = 7  
    y_axis_label_size = 9 

    # These will be primary fallbacks, ideally overridden by plot_config.yaml "defaults"
    default_vsh_fill_cutoff = 0.5
    default_vsh_sand_fill_color = 'yellow'
    default_vsh_shale_fill_color = 'grey'
    default_synthetic_fill_color = 'black'
    default_flag_fill_color = 'red'
    default_flag_fill_alpha = 0.3
    default_log_color = 'blue'
    default_log_line_width = 0.7

    log_type_display_settings = {}
    default_display_settings = {}
    config_defaults = {}
    
    try:
        import rockphysics
        package_root = os.path.dirname(os.path.dirname(rockphysics.__file__)) 
        config_path_attempt1 = os.path.join(package_root, "resources/plot_config.yaml")

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        config_path_attempt2 = os.path.join(current_file_dir, "..", "..", "/resources/plot_config.yaml") 
        config_path_attempt3 = os.path.join(current_file_dir, "..", "resources/plot_config.yaml") 

        config_path = None
        if os.path.exists(config_path_attempt1):
            config_path = config_path_attempt1
        elif os.path.exists(config_path_attempt2):
            config_path = config_path_attempt2
        elif os.path.exists(config_path_attempt3):
            config_path = config_path_attempt3
        
        if config_path:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
            log_type_display_settings = config_data.get("log_display_settings", {})
            default_display_settings = config_data.get("defaults", {})
            config_defaults = config_data.get("defaults", {})
            print(f"Loaded display settings from: {config_path}")
        else:
            print(f"Warning: Configuration file 'plot_config.yaml' not found. Using default plotting parameters.")
            
    except ImportError:
        print("Warning: 'rockphysics' package not found for robust config path detection. Trying relative paths for 'config.yaml'.")
    except FileNotFoundError:
        print(f"Warning: Configuration file 'plot_config.yaml' not found. Using default plotting parameters.")
    except Exception as e:
        print(f"Warning: Error loading 'plot_config.yaml': {e}. Using default plotting parameters.")

    # Apply global defaults from config file, falling back to hardcoded defaults
    default_log_color = config_defaults.get('default_log_color', default_log_color)
    log_line_width = config_defaults.get('log_line_width', default_log_line_width)
    track_title_size = config_defaults.get('track_title_size', track_title_size)
    tick_label_size = config_defaults.get('tick_label_size', tick_label_size)
    y_axis_label_size = config_defaults.get('y_axis_label_size', y_axis_label_size)
    default_vsh_fill_cutoff = config_defaults.get('vsh_fill_cutoff', default_vsh_fill_cutoff)
    default_vsh_sand_fill_color = config_defaults.get('vsh_sand_fill_color', default_vsh_sand_fill_color)
    default_vsh_shale_fill_color = config_defaults.get('vsh_shale_fill_color', default_vsh_shale_fill_color)
    default_synthetic_fill_color = config_defaults.get('synthetic_fill_color', default_synthetic_fill_color)
    default_flag_fill_color = config_defaults.get('flag_fill_color', default_flag_fill_color)
    default_flag_fill_alpha = config_defaults.get('flag_fill_alpha', default_flag_fill_alpha)

    # filter dataframe by depth range
    df_filtered = dataframe[(dataframe.index >= depth_top) & (dataframe.index <= depth_bottom)]
    if df_filtered.empty:
        print(f"No data available between depths {depth_top} and {depth_bottom}.")
        return

    plt.scatter(x=x_var, y=y_var, data=df_filtered, c=color)
    plt.xlabel(x_var)
    plt.ylabel(y_var)
    plt.title(f"Crossplot: {y_var} vs {x_var}", fontsize=12, y=0.98)
    plt.colorbar(label=color)  # Add colorbar for the color variable
    plt.show()