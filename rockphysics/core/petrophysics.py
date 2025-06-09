import pandas as pd
from typing import Union

def vshale_from_GR(gr_log: pd.Series, gr_clean: float, gr_shale: float) -> pd.Series:
    """
    Calculate the volume of shale (VSH) from the Gamma Ray (GR) log
    using a linear interpolation between clean sand and pure shale cutoffs.

    Reference: Schlumberger. (1989 and newer editions). Log Interpretation Principles/Applications

    Args:
        gr_log (pd.Series): Gamma Ray log.
        gr_clean (float): GR value for clean sand (0% VCLAY).
        gr_shale (float): GR value for pure shale (100% VCLAY).

    Returns:
        pd.Series: Volume of shale (VSH) log.
    """
    return (gr_log - gr_clean) / (gr_shale - gr_clean)


def vshale_from_SP(sp_log: pd.Series, sp_clean: float, sp_shale: float) -> pd.Series:
    """
    Calculate the volume of shale (VSH) from the Spontaneous Potential (SP) log
    using a linear interpolation between clean sand and pure shale cutoffs.

    Args:
        sp_log (pd.Series): Spontaneous Potential log.
        sp_clean (float): SP value for clean sand (0% VCLAY).
        sp_shale (float): SP value for pure shale (100% VCLAY).

    Returns:
        pd.Series: Volume of shale (VSH) log.
    """
    return (sp_shale - sp_log) / (sp_shale - sp_clean)


def density_porosity(
    bulk_density: pd.Series,
    matrix_density: float = 2.65,
    fluid_density: float = 1.0
    ) -> pd.Series:
    """
    Calculate porosity from bulk density.

    Reference: Schlumberger. (1989). Log Interpretation Principles/Applications.

    Args:
        bulk_density (pd.Series): Bulk density log
        matrix_density (float): Density of the rock matrix.
            Defaults to 2.65 g/cm^3.
        fluid_density (float): Density of the pore fluid.
            Defaults to 1.0 g/cm^3.

    Returns:
        pd.Series: Porosity log

    Raises:
        ValueError: If matrix density equals fluid density.
    """

    if (matrix_density - fluid_density) == 0:
        raise ValueError("Matrix density cannot equal fluid density.")

    porosity = ((matrix_density - bulk_density) / (matrix_density - fluid_density))
    return porosity.clip(lower=0, upper=1)  # Ensure porosity is within [0, 1]


def sonic_porosity_wyllie(
    delta_t: pd.Series,
    delta_t_matrix: float = 55.5,
    delta_t_fluid: float = 189.0
    ) -> pd.Series:
    """
    Calculate porosity from sonic transit time (delta_t)
    using the Wyllie time-average equation.

    Reference: Wyllie, M. R. J., Gregory, A. R., & Gardner, L. W. (1956).
    Elastic wave velocities in heterogeneous and porous media. Geophysics, 21(1), 41-70

    Args:
        delta_t (pd.Series): Sonic transit time log, with units
            attached (e.g., us/ft).
        delta_t_matrix (float): Sonic transit time of the
            rock matrix. Defaults to 55.5 us/ft (sandstone). Other common values
            are 47.5 us/ft (limestone) and 43.5 us/ft (dolomite).
        delta_t_fluid (float): Sonic transit time of the
            pore fluid. Defaults to 189.0 us/ft (water). Typical values
            range from 189 us/ft to 204 us/ft for freshwater.

    Returns:
        pd.Series: Porosity log (dimensionless).

    Raises:
        ValueError: If delta_t_matrix equals delta_t_fluid.
    """

    if (delta_t_matrix - delta_t_fluid) == 0:
        raise ValueError("Matrix density cannot equal fluid density.")

    porosity = ((delta_t - delta_t_matrix) / (delta_t_fluid - delta_t_matrix))
    return porosity.clip(lower=0, upper=1)  # Ensure porosity is within [0, 1]


def sonic_porosity_rhg(
    delta_t: pd.Series,
    delta_t_matrix: float = 55.5,
    c: float = 0.67
    ) -> pd.Series:
    """    Calculate porosity from sonic transit time (delta_t)
    using the RHG (Haymer-Hunt-Gardner) equation.
    
    Args:
        delta_t (pd.Series): Sonic transit time log, with units
            attached (e.g., us/ft).
        delta_t_matrix (float): Sonic transit time of the
            rock matrix. Defaults to 55.5 us/ft (sandstone). Other common values
            are 47.5 us/ft (limestone) and 43.5 us/ft (dolomite).
        c (float): Constant for the RHG equation, typically around 0.67.
    Returns:
        pd.Series: Porosity log (dimensionless).
    Raises:
        ValueError: If delta_t_matrix is zero.
    """
    if delta_t_matrix == 0:
        raise ValueError("Matrix sonic transit time cannot be zero.")
    
    # Calculate porosity using the RHG equation
    porosity = c * (delta_t - delta_t_matrix) / delta_t
    return porosity.clip(lower=0, upper=1)  # Ensure porosity is within [0, 1]


def vclay_from_neutron_density(
    nphi: pd.Series,
    rhob: pd.Series,
    nphi_clean: float,
    rhob_clean: float,
    nphi_clay: float,
    rhob_clay: float,
    method: str = "linear"
) -> pd.Series:
    """
    Calculate volume of clay (Vclay) using the neutron-density crossplot method.

    Args:
        nphi (pd.Series): Neutron porosity (NPHI) log.
        rhob (pd.Series): Bulk density (RHOB) log.
        nphi_clean (float): NPHI reading for clean lithology.
        rhob_clean (float): RHOB reading for clean lithology.
        nphi_clay (float): NPHI reading for pure clay.
        rhob_clay (float): RHOB reading for pure clay.
        method (str, optional): Method for calculation. 
            Currently supports "linear". Defaults to "linear".

    Returns:
        pd.Series: Volume of clay (Vclay) log.

    Raises:
        ValueError: If method is not supported.
    """

    if method == "linear":
        # Calculate Vclay from Neutron
        vclay_nphi = (nphi - nphi_clean) / (nphi_clay - nphi_clean)

        # Calculate Vclay from Density
        vclay_rhob = (rhob_clay - rhob) / (rhob_clay - rhob_clean)

        # Combine NPHI and RHOB Vclay (average)
        vclay = (vclay_nphi + vclay_rhob) / 2  # Simple average, other methods possible

        # Ensure Vclay is within valid range [0, 1]
        vclay = vclay.clip(lower=0, upper=1)

        return vclay

    else:
        raise ValueError(f"Method '{method}' not supported.")
    

def archie_saturation(
    phi: Union[float, pd.Series],
    rt: Union[float, pd.Series],
    rw: float,
    a: float = 0.81,
    m: float = 2.0,
    n: float = 2.0,
 
) -> Union[float, pd.Series]:
    """
    Calculate the water saturation using Archie's equation.

    Reference: Archie, G. E. (1942). The electrical resistivity log
    as an aid in determining some reservoir characteristics.

    Parameters
    ----------
    phi: Union[float, pd.Series]
        Porosity (fraction).
    rt: float
        Resistivity of the formation (ohm-meter).
    rw: float
        Resistivity of water (ohm-meter).
    a: float
        Archie constant (dimensionless).
    m: float
        Cementation exponent (dimensionless).
    n: float
        Saturation exponent (dimensionless).

    Returns
    -------
    Sw: Union[float, pd.Series]
        Water saturation (fraction).

    Raises
    ------
    ValueError
        If porosity is zero or resistivity values are invalid.
    """
    if isinstance(phi, pd.Series) and (phi.min() <= 0 or phi.max() >= 1):
        raise ValueError("Porosity values must be between 0 and 1.")
    elif isinstance(phi, float) and (phi <= 0 or phi >= 1):
        raise ValueError("Porosity values must be between 0 and 1.")

    if rw <= 0 or rt <= 0:
        raise ValueError("Resistivity values must be positive.")

    F = a / phi ** m  # Formation factor
    
    Sw = (F * rw) / rt 
    return Sw
