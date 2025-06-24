# app.py
import streamlit as st
import pandas as pd
import lasio
import io
import yaml
from pathlib import Path
from typing import Tuple, List, Dict

# --- New Imports for Interactive Plotting & Components ---
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components

# --- Import your library's components ---
from rockphysics.core.well import Well
from rockphysics.core import petrophysics as pp
from rockphysics.utils.nomenclature import LogNomenclature

# --- Page Configuration ---
st.set_page_config(
    page_title="Rock Physics Interpreter",
    layout="wide"
)

# --- NEW: Color Name to Hex Code Mapping ---
COLOR_MAP = {
    'black': '#000000', 'red': '#FF0000', 'green': '#008000',
    'blue': '#0000FF', 'purple': '#800080', 'yellow': '#FFFF00',
    'grey': '#808080', 'gray': '#808080',
}

# --- Helper function to load plot configuration ---
@st.cache_data
def load_plot_config():
    """Loads the plot configuration from the YAML file."""
    try:
        config_path = Path("rockphysics/resources/plot_config.yaml")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.warning(f"Could not load plot_config.yaml: {e}. Using default styles.")
        return {}

# --- PLOTTING FUNCTION using Plotly ---
def plot_logs_with_plotly(
    logs_df: pd.DataFrame, 
    tracks: List[List[str]],
    style_info: Dict[str, Dict],
    nomenclature: LogNomenclature
) -> Tuple[go.Figure, int]:
    """
    Creates an interactive multi-track log plot using Plotly, with custom styling.
    This version supports special fills for VSHALE logs.
    """
    num_tracks = len(tracks)
    if num_tracks == 0:
        return None, 0

    track_width_px = 250
    y_axis_width_px = 80
    total_width = (num_tracks * track_width_px) + y_axis_width_px

    fig = make_subplots(
        rows=1, cols=num_tracks, shared_yaxes=True, horizontal_spacing=0.03
    )

    layout_updates = {}
    traces_to_link = []
    
    # Loop through each track group to add traces
    for i, track_group in enumerate(tracks):
        # --- NEW: Check for VSHALE fill ---
        log_type = nomenclature.get_log_type(track_group[0]) if track_group else ""
        is_vsh_track = log_type in ['VOLUME_SHALE', 'VOLUME_CLAY'] and len(track_group) == 1

        if is_vsh_track:
            track_name = track_group[0]
            curve_style = style_info.get(track_name, {})
            line_color = curve_style.get('color', '#000000')
            sand_color = curve_style.get('sand_fill_color', '#FFFF00')
            shale_color = curve_style.get('shale_fill_color', '#808080')
            
            # Add shale fill (from VSH curve to right edge of the track, assuming range is 0-1)
            fig.add_trace(go.Scatter(x=logs_df[track_name], y=logs_df.index, fill='tozerox',
                                     mode='none', fillcolor=shale_color, name='Shale', showlegend=False), row=1, col=i+1)
            # Add sand fill (from left edge to VSH curve)
            fig.add_trace(go.Scatter(x=[0]*len(logs_df.index), y=logs_df.index, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False), row=1, col=i+1)
            fig.add_trace(go.Scatter(x=logs_df[track_name], y=logs_df.index, fill='tonexty', # Correct fill mode for this direction
                                     mode='none', fillcolor=sand_color, name='Sand', showlegend=False), row=1, col=i+1)
            # Add the VSH line on top
            fig.add_trace(go.Scatter(x=logs_df[track_name], y=logs_df.index, mode='lines',
                                     name=track_name, line=dict(width=1.5, color=line_color)), row=1, col=i + 1)
        else:
            # Original logic for non-VSH tracks or tracks with multiple curves
            for j, track_name in enumerate(track_group):
                if track_name not in logs_df.columns: continue
                curve_style = style_info.get(track_name, {})
                line_color = curve_style.get('color', '#1f77b4')
                fig.add_trace(go.Scatter(x=logs_df[track_name], y=logs_df.index, mode='lines',
                                         name=track_name, line=dict(width=1.5, color=line_color)), row=1, col=i + 1)
                if j > 0:
                    traces_to_link.append({'trace_index': len(fig.data) - 1, 'track_index': i})

    # --- Second Pass for multi-axis tracks (unchanged) ---
    overlay_axis_counter = 0
    for link_info in traces_to_link:
        trace_index, track_index = link_info['trace_index'], link_info['track_index']
        track_name = fig.data[trace_index].name
        curve_style = style_info.get(track_name, {})
        overlay_axis_num = num_tracks + overlay_axis_counter + 1
        layout_key = f'xaxis{overlay_axis_num}'
        layout_updates[layout_key] = {'overlaying': f'x{track_index + 1}', 'side': 'top', 'showgrid': False,
                                      'title': {'text': track_name, 'font': {'color': curve_style.get('color', '#d62728')}},
                                      'range': curve_style.get('range'), 'autorange': False if curve_style.get('range') else True}
        fig.data[trace_index].xaxis = f'x{overlay_axis_num}'
        overlay_axis_counter += 1

    if layout_updates: fig.update_layout(layout_updates)
    
    # Style primary axes after all overlays are configured
    for i, track_group in enumerate(tracks):
        if track_group:
            primary_name = track_group[0]
            primary_style = style_info.get(primary_name, {})
            primary_range = primary_style.get('range')
            fig.update_xaxes(title_text=primary_name, range=primary_range, row=1, col=i + 1)

    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', mirror=True, ticks='outside')
    for i in range(1, num_tracks + 1):
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black', mirror=True, row=1, col=i, ticks='outside')

    fig.update_layout(
        title_text="Interactive Log Plot", yaxis_title=logs_df.index.name or "Depth",
        yaxis_autorange='reversed', height=800, width=total_width, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white", margin=dict(l=50, r=20, t=100, b=20),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig, total_width


st.title("Interactive Well Log Analysis")
st.write("Upload a LAS file to begin analysis and visualization.")

plot_config = load_plot_config()
nomenclature_handler = LogNomenclature()

if 'well' not in st.session_state: st.session_state['well'] = None
if 'last_uploaded_filename' not in st.session_state: st.session_state['last_uploaded_filename'] = None
if 'message' not in st.session_state: st.session_state['message'] = None

with st.sidebar:
    st.header("1. Load Data")
    uploaded_file = st.file_uploader("Choose a LAS file", type="las")
    if uploaded_file and uploaded_file.name != st.session_state.last_uploaded_filename:
        try:
            st.session_state.last_uploaded_filename = uploaded_file.name
            st.session_state['well'] = Well(lasio.read(io.StringIO(uploaded_file.getvalue().decode('utf-8'))))
            st.session_state.message = f"Success: Loaded well **{st.session_state['well'].name}**"
            st.rerun()
        except Exception as e:
            st.error(f"Error loading LAS file: {e}")
            st.session_state.well = None
            st.session_state.last_uploaded_filename = None

if st.session_state.message:
    st.success(st.session_state.message)
    st.session_state.message = None

if st.session_state['well'] is not None:
    well = st.session_state['well']
    all_curves = well.get_log_names()

    st.header("Well Information")
    c1, c2, c3 = st.columns(3)
    c1.metric("Well Name", well.name); c2.metric("UWI", well.uwi); c3.metric("Curves", len(all_curves))
    st.dataframe(well.logs.head())

    # --- RESTORED: Petrophysical Calculations Section ---
    with st.expander("Petrophysical Calculations", expanded=True):
        
        # --- Vshale from GR ---
        with st.container(border=True):
            st.subheader("Volume of Shale (GR)")
            c1, c2 = st.columns([2,1])
            gr_log_name = c1.selectbox("GR Curve", options=all_curves, key="gr_log_vsh", index=all_curves.index("GR") if "GR" in all_curves else 0)
            if c2.button("Calculate Vshale (GR)", use_container_width=True):
                gr_clean = st.session_state.get('gr_clean_vsh', 20.0)
                gr_shale = st.session_state.get('gr_shale_vsh', 120.0)
                new_curve = pp.vshale_from_GR(well.get_log(gr_log_name), gr_clean, gr_shale)
                well.add_log(new_curve.name, new_curve)
                st.session_state.message = f"Calculated and added '{new_curve.name}'."
                st.rerun()
            c1, c2 = st.columns(2)
            c1.number_input("GR Clean", value=20.0, key="gr_clean_vsh")
            c2.number_input("GR Shale", value=120.0, key="gr_shale_vsh")
        
        st.markdown("---")

        # --- Density Porosity ---
        with st.container(border=True):
            st.subheader("Density Porosity")
            c1, c2 = st.columns([2,1])
            rhob_log_name = c1.selectbox("Density Curve", options=all_curves, key="rhob_log_phi", index=all_curves.index("RHOB") if "RHOB" in all_curves else 0)
            if c2.button("Calculate Density Porosity", use_container_width=True):
                matrix_density = st.session_state.get('matrix_density_phi', 2.65)
                fluid_density = st.session_state.get('fluid_density_phi', 1.0)
                new_curve = pp.density_porosity(well.get_log(rhob_log_name), matrix_density, fluid_density)
                well.add_log(new_curve.name, new_curve)
                st.session_state.message = f"Calculated and added '{new_curve.name}'."
                st.rerun()
            c1, c2 = st.columns(2)
            c1.number_input("Matrix Density", value=2.65, format="%.2f", key="matrix_density_phi")
            c2.number_input("Fluid Density", value=1.0, format="%.2f", key="fluid_density_phi")
            
        st.markdown("---")

        # --- Water Saturation (Archie) ---
        with st.container(border=True):
            st.subheader("Water Saturation (Archie)")
            c1, c2, c3 = st.columns([2, 2, 1])
            phi_log_name = c1.selectbox("Porosity Curve", options=all_curves, key="phi_log_sw", index=all_curves.index("Porosity_Density") if "Porosity_Density" in all_curves else 0)
            rt_log_name = c2.selectbox("Resistivity Curve", options=all_curves, key="rt_log_sw", index=all_curves.index("RT") if "RT" in all_curves else 0)
            if c3.button("Calculate Sw (Archie)", use_container_width=True):
                rw = st.session_state.get('rw_sw', 0.05)
                a = st.session_state.get('a_sw', 0.81)
                m = st.session_state.get('m_sw', 2.0)
                n = st.session_state.get('n_sw', 2.0)
                new_curve = pp.archie_saturation(well.get_log(phi_log_name), well.get_log(rt_log_name), rw, a, m, n)
                new_curve.name = "SW_Archie" # Name the output curve
                well.add_log(new_curve.name, new_curve)
                st.session_state.message = f"Calculated and added '{new_curve.name}'."
                st.rerun()
            c1, c2, c3, c4 = st.columns(4)
            c1.number_input("Rw", value=0.05, format="%.3f", key="rw_sw")
            c2.number_input("a", value=0.81, format="%.2f", key="a_sw")
            c3.number_input("m", value=2.0, format="%.1f", key="m_sw")
            c4.number_input("n", value=2.0, format="%.1f", key="n_sw")

    st.header("Log Plot Configuration")
    curves_to_plot_grouped = []
    style_info = {}
    
    with st.expander("Configure Plot Tracks", expanded=True):
        num_tracks = st.number_input("Number of Tracks", min_value=1, max_value=10, value=3)
        track_cols = st.columns(num_tracks)
        for i in range(num_tracks):
            with track_cols[i]:
                selection = st.multiselect(f"Track {i+1} (max 2)", options=all_curves, key=f"track_{i+1}", max_selections=2)
                if selection: curves_to_plot_grouped.append(selection)

    if curves_to_plot_grouped:
        st.subheader("Track Styling")
        style_cols = st.columns(len(curves_to_plot_grouped))
        for i, track_group in enumerate(style_cols):
            with track_group:
                if i < len(curves_to_plot_grouped):
                    st.markdown(f"**Track {i+1} Styling**")
                    for curve in curves_to_plot_grouped[i]:
                        with st.container(border=True):
                            st.markdown(f"**{curve}**")
                            log_type = nomenclature_handler.get_log_type(curve)
                            type_defaults = plot_config.get('log_display_settings', {}).get(log_type, {})
                            
                            valid_data = well.logs[curve].dropna()
                            default_min = float(type_defaults.get('min_value', 0.0 if valid_data.empty else valid_data.quantile(0.01)))
                            default_max = float(type_defaults.get('max_value', 1.0 if valid_data.empty else valid_data.quantile(0.99)))
                            default_color_name = type_defaults.get('color', 'blue')
                            default_hex_color = COLOR_MAP.get(default_color_name.lower(), '#1f77b4')

                            c1, c2 = st.columns(2)
                            min_val = c1.number_input("Min", value=default_min, key=f"{curve}_min", format="%.2f")
                            max_val = c2.number_input("Max", value=default_max, key=f"{curve}_max", format="%.2f")
                            color_val = st.color_picker(f"Color", value=default_hex_color, key=f"{curve}_color")
                            style_info[curve] = {'range': (min_val, max_val), 'color': color_val}

                            # --- NEW: UI for VSH Fill Colors ---
                            if log_type in ['VOLUME_SHALE', 'VOLUME_CLAY']:
                                st.markdown("_Shale Fill Styling_")
                                c3, c4 = st.columns(2)
                                sand_color_name = type_defaults.get('vsh_sand_fill_color', 'yellow')
                                shale_color_name = type_defaults.get('vsh_shale_fill_color', 'grey')
                                style_info[curve]['sand_fill_color'] = c3.color_picker("Sand Color", value=COLOR_MAP.get(sand_color_name, '#FFFF00'), key=f"{curve}_sand_color")
                                style_info[curve]['shale_fill_color'] = c4.color_picker("Shale Color", value=COLOR_MAP.get(shale_color_name, '#808080'), key=f"{curve}_shale_color")

    if curves_to_plot_grouped:
        try:
            fig, plot_width = plot_logs_with_plotly(well.logs, curves_to_plot_grouped, style_info, nomenclature_handler)
            if fig:
                plot_html = fig.to_html(include_plotlyjs='cdn')
                components.html(plot_html, height=fig.layout.height+50, width=plot_width)
            else:
                st.warning("No curves selected to plot.")
        except Exception as e:
            st.error(f"An error occurred during plotting: {e}")
else:
    st.info("Please upload a LAS file in the sidebar to get started.")

