"""
This is the rockphysics library, providing tools for rock physics 
calculations and analysis of well log data.
"""

from .core import Well, TimeDomainAccessor, Project
from .core.seismic import (
    load_checkshot_data, create_depth_time_interpolators, resample_log_to_time,
    convert_well_to_time, calculate_reflectivity,
    generate_ricker_wavelet, create_synthetic
)
from .utils.nomenclature import LogNomenclature
from .io import load_tops, save_well_to_las, load_well_from_las
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
    density_porosity, sonic_porosity_wyllie, sonic_porosity_rhg,
    vshale_from_GR, vshale_from_SP, vclay_from_neutron_density, archie_saturation
)
from .utils.general_utils import (
    psi_to_mpa, mpa_to_psi, psi_to_kpa, kpa_to_psi, 
    celsius_to_fahrenheit, fahrenheit_to_celsius, 
    validate_log_data, vp_from_dt, vs_from_dts
)
from .geomechanics.porepressure import (
    calculate_pore_pressure_eaton
)
from .visualization.plotting import plot_logs, crossplot
from .visualization.interactive import interactive_vclay_crossplot, calculate_vclay_neutron_density_xplot

__all__ = [
    "Project",
    "Well",
    "TimeDomainAccessor",
    "LogNomenclature",
    "load_checkshot_data",
    "create_depth_time_interpolators",
    "resample_log_to_time",
    "convert_well_to_time",
    "calculate_reflectivity",
    "generate_ricker_wavelet",
    "create_synthetic",
    "load_tops",
    "load_well_from_las",
    "save_well_to_las",
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
    "sonic_porosity_wyllie",
    "sonic_porosity_rhg",
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
    "vshale_from_SP",
    "vclay_from_neutron_density",
    "archie_saturation",
    "calculate_pore_pressure_eaton",
    "plot_logs",
    "crossplot",
    "interactive_vclay_crossplot",
    "calculate_vclay_neutron_density_xplot"
]

__version__ = "0.1.0"