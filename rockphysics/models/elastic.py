import pandas as pd


def reuss_average(f1: float, M1: float, M2: float) -> float:
    """
    Calculate the Reuss average (lower bound) of the elastic modulus
    for a mixture of two components.

    Args:
        f1 (float): Volume fraction of the first component.
        M1 (float): Elastic modulus of the first component.
        M2 (float): Elastic modulus of the second component.

    Returns:
        float: Reuss average of the elastic modulus.
    """
    f2 = 1 - f1  # Calculate volume fraction of the second component
    return 1 / (f1 / M1 + f2 / M2)


def voigt_average(f1: float, M1: float, M2: float) -> float:
    """
    Calculate the Reuss average (lower bound) of the elastic modulus
    for a mixture of two components.

    Args:
        f1 (float): Volume fraction of the first component.
        M1 (float): Elastic modulus of the first component.
        M2 (float): Elastic modulus of the second component.

    Returns:
        float: Reuss average of the elastic modulus.
    """
    f2 = 1 - f1  # Calculate volume fraction of the second component
    return f1*M1 + f2*M2


def hill_average(voigt: float, reuss: float) -> float:
    """
    Calculate the Hill average of the bulk and shear moduli.

    Args:
        voigt (float): Voigt average of the bulk and shear moduli.
        reuss (float): Reuss average of the bulk and shear moduli.

    Returns:
        float: Hill average of the bulk and shear moduli.
    """
    return (voigt + reuss) / 2


def greenberg_castagna(vp: pd.Series, vshale: pd.Series) -> pd.Series:
    """
    Predicts shear wave velocity (Vs) from compressional wave velocity (Vp)
    using the Greenberg and Castagna relation, accounting for sand-shale mixtures.

    Args:
        vp (pd.Series): Compressional wave velocity (Vp) log in m/s.
        vshale (pd.Series): Volume of shale (VSH) log.

    Returns:
        pd.Series: Predicted shear wave velocity (Vs) log.
    """
    vs_sand= 0.80416*vp - 0.85588
    vs_shale= 0.76969*vp - 0.86735

    vs_arith= (1-vshale)*vs_sand+ vshale*vs_shale
    vs_harm=( (1-vshale)/vs_sand +vshale/vs_shale )**-1
    vs= 0.5*(vs_arith+vs_harm)
    return vs


def bulk_modulus(
    p_velocity: pd.Series,
    s_velocity: pd.Series,
    density: pd.Series
) -> pd.Series:
    """
    Calculate the bulk and shear moduli from P-wave and S-wave velocities.

    Args:
        p_velocity (pd.Series): P-wave velocity in m/s
        s_velocity (pd.Series): S-wave velocity in m/s.
        density (pd.Series): Density of the rock in kg/m^3.

    Returns:
        pd.Series: Bulk modulus of the rock.
    """
    p_velocity = p_velocity
    s_velocity = s_velocity

    bulk_modulus = density * (p_velocity ** 2 - 4/3 * s_velocity ** 2)
    return bulk_modulus


def shear_modulus(
    s_velocity: pd.Series,
    density: pd.Series
) -> pd.Series:
    """
    Calculate the shear modulus from S-wave velocities.

    Args:
        p_velocity (pd.Series): P-wave velocity in m/s
        s_velocity (pd.Series): S-wave velocity in m/s.
        density (pd.Series): Density of the rock in kg/m^3.

    Returns:
        pd.Series: Bulk modulus of the rock.
    """
    s_velocity = s_velocity

    shear_modulus = density * s_velocity ** 2
    return shear_modulus


def dry_modulus(
    k_sat: pd.Series,
    k_fluid: float,
    k_mineral: float,
    phi: pd.Series
) -> pd.Series: 
    """
    Calculate the dry bulk modulus of the rock using Gassmann's equation.

    Args:
        k_sat (pd.Series): Bulk modulus of the rock saturated with fluid.
        k_fluid (float): Bulk modulus of the fluid.
        k_mineral (float): Bulk modulus of the mineral matrix.
        phi (pd.Series): Porosity (fraction).

    Returns:
        pd.Series: Dry bulk modulus of the rock.
    """
    return (
        k_sat * (( phi * k_mineral / k_fluid ) + 1 - phi ) - k_mineral
    ) / (
        ( phi * k_mineral / k_fluid) + (k_sat / k_mineral ) - 1 - phi
    )

def gassmann(
    k_dry: pd.Series,
    k_fluid: float,
    k_mineral: float,
    phi: pd.Series,
) -> pd.Series:
    """
    Performs Gassmann's fluid substitution to calculate the bulk modulus
    of the rock saturated with fluid 2.

    Args:
        k_dry (pd.Series): Bulk modulus of the dry rock.
        k_fluid (float): Bulk modulus of fluid.
        k_mineral (float): Bulk modulus of the mineral matrix.
        phi (pd.Series): Porosity (fraction).

    Returns:
        pd.Series: Bulk modulus of the rock saturated with fluid 2.
    """
    return (
        k_dry
        + (
            (1 - (k_dry / k_mineral))**2
    ) / (
        (phi / k_fluid) + ((1 - phi) / k_mineral) - (k_dry / k_mineral**2)
    ))


def p_wave_velocity(
    bulk_modulus: pd.Series,
    shear_modulus: pd.Series,
    density: pd.Series
) -> pd.Series:
    """
    Calculate the P-wave and S-wave velocities from bulk and shear moduli.

    Args:
        bulk_modulus (pd.Series): Bulk modulus of the rock.
        shear_modulus (pd.Series): Shear modulus of the rock.
        density (pd.Series): Density of the rock in kg/m^3.

    Returns:
        pd.Series: P-wave and S-wave velocities of the rock.
    """
    p_velocity = ((bulk_modulus + 4/3 * shear_modulus) / density) ** 0.5

    return p_velocity


def s_wave_velocity(
    shear_modulus: pd.Series,
    density: pd.Series
) -> pd.Series:
    """
    Calculate the P-wave and S-wave velocities from bulk and shear moduli.

    Args:
        bulk_modulus (pd.Series): Bulk modulus of the rock.
        shear_modulus (pd.Series): Shear modulus of the rock.
        density (pd.Series): Density of the rock in kg/m^3.

    Returns:
        pd.Series: P-wave and S-wave velocities of the rock.
    """
    s_velocity = (shear_modulus / density) ** 0.5

    return s_velocity


def acoustic_impedance(
    p_velocity: pd.Series,
    density: pd.Series
) -> pd.Series:
    """
    Calculate the acoustic impedance from P-wave velocity and density.

    Args:
        p_velocity (pd.Series): P-wave velocity in m/s.
        density (pd.Series): Density of the rock in kg/m^3.

    Returns:
        pd.Series: Acoustic impedance of the rock.
    """
    return p_velocity * density


