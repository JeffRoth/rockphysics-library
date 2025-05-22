import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display
# If calculate_vclay_neutron_density_xplot was intended to be from log_analysis:
# from ..utils.log_analysis import calculate_vclay_neutron_density


def interactive_vclay_crossplot(depth: pd.Series, nphi: pd.Series, rhob: pd.Series):
    """
    Creates an interactive neutron-density crossplot for Vclay estimation.

    Args:
        nphi (pd.Series): Neutron porosity (NPHI) log.
        rhob (pd.Series): Bulk density (RHOB) log.
    """

    # Initial end-point values (adjust as needed)
    depth_min = depth.min()
    depth_max = depth.max()

    nphi_clean1_init = 0
    rhob_clean1_init = 2.65
    nphi_clean2_init = 0.4
    rhob_clean2_init = 2.0
    nphi_clay_init = 0.45
    rhob_clay_init = 2.6

    depth_top_widget = widgets.FloatSlider(value=depth_min, min=depth_min, max=depth_max, step=0.1, description="Depth Top")
    depth_base_widget = widgets.FloatSlider(value=depth_max, min=depth_min, max=depth_max, step=0.1, description="Depth Base")

    nphi_clean1_widget = widgets.FloatSlider(value=nphi_clean1_init, min=-0.1, max=0.65, step=0.01, description="NPHI_clean1")
    rhob_clean1_widget = widgets.FloatSlider(value=rhob_clean1_init, min=2.0, max=3.25, step=0.01, description="RHOB_clean1")
    nphi_clean2_widget = widgets.FloatSlider(value=nphi_clean2_init, min=-0.1, max=0.65, step=0.01, description="NPHI_clean2")
    rhob_clean2_widget = widgets.FloatSlider(value=rhob_clean2_init, min=2.0, max=3.25, step=0.01, description="RHOB_clean2")
    nphi_clay_widget = widgets.FloatSlider(value=nphi_clay_init, min=0.3, max=0.65, step=0.01, description="NPHI_clay")
    rhob_clay_widget = widgets.FloatSlider(value=rhob_clay_init, min=2.0, max=3.25, step=0.01, description="RHOB_clay")

    def update_plot(depth_top, depth_base, nphi_clean1, rhob_clean1, nphi_clean2, rhob_clean2, nphi_clay, rhob_clay):
        # Filter data by depth range
        mask = (depth >= depth_top) & (depth <= depth_base)
        depth_filtered = depth[mask]
        nphi_filtered = nphi[mask]
        rhob_filtered = rhob[mask]

        vclay = calculate_vclay_neutron_density_xplot(nphi_filtered, rhob_filtered, nphi_clean1, rhob_clean1, nphi_clay, rhob_clay)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8), gridspec_kw={'width_ratios': [2, 1]})

        # Crossplot (ax1)
        ax1.scatter(nphi_filtered, rhob_filtered, s=10)
        ax1.set_xlabel("NPHI (p.u.)")
        ax1.set_ylabel("RHOB (g/cm3)")
        ax1.set_title("Neutron-Density Crossplot (Depth Filtered)")
        ax1.plot([nphi_clean1, nphi_clay], [rhob_clean1, rhob_clay], 'r-', label='Sandstone1-Clay Line')
        ax1.plot([nphi_clean1, nphi_clean2], [rhob_clean1, rhob_clean2], 'b-', label='Sandstone1-Sandstone2 Line')
        ax1.legend()
        ax1.grid(True)
        ax1.invert_yaxis()

        # VCLAY Track (ax2)
        ax2.plot(vclay, depth_filtered)
        ax2.set_xlabel("VCLAY")
        ax2.set_ylabel("Depth")
        ax2.set_title("VCLAY Track")
        ax2.set_ylim(depth_base, depth_top)  # Invert y-axis for depth
        ax2.grid(True)

        plt.show()

    display(widgets.interactive(
        update_plot,
        depth_top=depth_top_widget,
        depth_base=depth_base_widget,
        nphi_clean1=nphi_clean1_widget,
        rhob_clean1=rhob_clean1_widget,
        nphi_clean2=nphi_clean2_widget,
        rhob_clean2=rhob_clean2_widget,
        nphi_clay=nphi_clay_widget,
        rhob_clay=rhob_clay_widget,
    ))

def calculate_vclay_neutron_density_xplot(nphi, rhob, nphi_clean, rhob_clean, nphi_clay, rhob_clay):
    vclay_nphi = (nphi - nphi_clean) / (nphi_clay - nphi_clean)
    vclay_rhob = (rhob_clay - rhob) / (rhob_clay - rhob_clean)
    vclay = (vclay_nphi + vclay_rhob) / 2
    vclay = vclay.clip(lower=0, upper=1)
    return vclay