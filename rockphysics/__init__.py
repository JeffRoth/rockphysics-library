"""
This is the rockphysics library, providing tools for rock physics 
calculations and analysis of well log data.
"""

from .core import LogData
from .core.seismic import (
    load_checkshot_data, create_depth_time_interpolators, resample_log_to_time_domain,
    convert_well_logs_to_time_domain, calculate_reflectivity_series,
    generate_ricker_wavelet, convolve_traces
)
from .utils.nomenclature import LogNomenclature
from .io import load_las_file, save_las_file
from .models.elastic import (
    dry_modulus, gassmann, bulk_modulus, shear_modulus, voigt_average, 
    reuss_average, greenberg_castagna, hill_average, p_wave_velocity, s_wave_velocity,
    acoustic_impedance
)
from .models.fluid import (
    water_density, oil_density, gas_density,
    water_bulk_modulus, oil_bulk_modulus, gas_bulk_modulus
)
from .core.petrophysics import (
    density_porosity, sonic_porosity,
    vshale_from_GR, vclay_from_neutron_density,
    archie_saturation
)
from .utils.general_utils import (
    psi_to_mpa, mpa_to_psi, psi_to_kpa, kpa_to_psi, 
    celsius_to_fahrenheit, fahrenheit_to_celsius, 
    validate_log_data, vp_from_dt, vs_from_dts
)
from .visualization.plotting import plot_logs
from .visualization.interactive import interactive_vclay_crossplot, calculate_vclay_neutron_density_xplot

__all__ = [
    "LogData",
    "LogNomenclature",
    "load_checkshot_data",
    "create_depth_time_interpolators",
    "resample_log_to_time_domain",
    "convert_well_logs_to_time_domain",
    "calculate_reflectivity_series",
    "generate_ricker_wavelet",
    "convolve_traces",
    "load_las_file",
    "save_las_file",
    "dry_modulus",
    "gassmann",
    "bulk_modulus",
    "shear_modulus",
    "voigt_average",
    "reuss_average",
    "hill_average",
    "p_wave_velocity",
    "s_wave_velocity",
    "acoustic_impedance",
    "greenberg_castagna",
    "water_density",
    "oil_density",
    "gas_density",
    "water_bulk_modulus",
    "oil_bulk_modulus",
    "gas_bulk_modulus",
    "density_porosity",
    "sonic_porosity",
    "archie_saturation",
    "psi_to_mpa",
    "mpa_to_psi",
    "psi_to_kpa",
    "kpa_to_psi",
    "celsius_to_fahrenheit",
    "fahrenheit_to_celsius",
    "validate_log_data",
    "vp_from_dt",
    "vs_from_dts",
    "vshale_from_GR",
    "vclay_from_neutron_density",
    "plot_logs",
    "interactive_vclay_crossplot",
    "calculate_vclay_neutron_density_xplot"
]

__version__ = "0.1.0"