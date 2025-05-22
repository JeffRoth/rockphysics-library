import pint
import pandas as pd
from typing import Union

ureg = pint.UnitRegistry()

def psi_to_mpa(pressure_psi: Union[float, pint.Quantity]) -> pint.Quantity:
    """
    Convert pressure from psi to MPa.

    Args:
        pressure_psi (Union[float, pint.Quantity]): Pressure value in psi.
            Can be a float (assumed to be in psi) or a pint Quantity.

    Returns:
        pint.Quantity: Pressure value in MPa.
    """
    if not isinstance(pressure_psi, pint.Quantity):
        pressure_quantity_psi = pressure_psi * ureg.psi
    else:
        pressure_quantity_psi = pressure_psi
    return pressure_quantity_psi.to(ureg.MPa)


def mpa_to_psi(pressure_mpa: Union[float, pint.Quantity]) -> pint.Quantity:
    """
    Convert pressure from MPa to psi.

    Args:
        pressure_mpa (Union[float, pint.Quantity]): Pressure value in MPa.
            Can be a float (assumed to be in MPa) or a pint Quantity.

    Returns:
        pint.Quantity: Pressure value in psi.
    """
    if not isinstance(pressure_mpa, pint.Quantity):
        pressure_quantity_mpa = pressure_mpa * ureg.MPa
    else:
        pressure_quantity_mpa = pressure_mpa
    return pressure_quantity_mpa.to(ureg.psi)


def psi_to_kpa(pressure_psi: Union[float, pint.Quantity]) -> pint.Quantity:
    """
    Convert pressure from psi to kPa.

    Args:
        pressure_psi (Union[float, pint.Quantity]): Pressure value in psi.
            Can be a float (assumed to be in psi) or a pint Quantity.

    Returns:
        pint.Quantity: Pressure value in kPa.
    """
    if not isinstance(pressure_psi, pint.Quantity):
        pressure_quantity_psi = pressure_psi * ureg.psi
    else:
        pressure_quantity_psi = pressure_psi
    return pressure_quantity_psi.to(ureg.kPa)


def kpa_to_psi(pressure_kpa: Union[float, pint.Quantity]) -> pint.Quantity:
    """
    Convert pressure from kPa to psi.

    Args:
        pressure_kpa (Union[float, pint.Quantity]): Pressure value in kPa.
            Can be a float (assumed to be in kPa) or a pint Quantity.

    Returns:
        pint.Quantity: Pressure value in psi.
    """
    if not isinstance(pressure_kpa, pint.Quantity):
        pressure_quantity_kpa = pressure_kpa * ureg.kPa
    else:
        pressure_quantity_kpa = pressure_kpa
    return pressure_quantity_kpa.to(ureg.psi)


def celsius_to_fahrenheit(celsius: Union[float, pint.Quantity]) -> pint.Quantity:
    """
    Convert temperature from Celsius to Fahrenheit.

    Args:
        celsius (Union[float, pint.Quantity]): Temperature value in Celsius.
            Can be a float (assumed to be in Celsius) or a pint Quantity.

    Returns:
        pint.Quantity: Temperature value in Fahrenheit.
    """
    if not isinstance(celsius, pint.Quantity):
        temperature_quantity_celsius = celsius * ureg.degC
    else:
        temperature_quantity_celsius = celsius
    return temperature_quantity_celsius.to(ureg.degF)


def fahrenheit_to_celsius(fahrenheit: Union[float, pint.Quantity]) -> pint.Quantity:
    """
    Convert temperature from Fahrenheit to Celsius.

    Args:
        fahrenheit (Union[float, pint.Quantity]): Temperature value in Fahrenheit.
            Can be a float (assumed to be in Fahrenheit) or a pint Quantity.

    Returns:
        pint.Quantity: Temperature value in Celsius.
    """
    if not isinstance(fahrenheit, pint.Quantity):
        temperature_quantity_fahrenheit = fahrenheit * ureg.degF
    else:
        temperature_quantity_fahrenheit = fahrenheit
    return temperature_quantity_fahrenheit.to(ureg.degC)


def validate_log_data(log_data: pd.DataFrame, required_curves: list) -> None:
    """
    Validate the log data to ensure all required curves are present.

    Args:
        log_data (pd.DataFrame): The log data DataFrame.
        required_curves (list): List of required curve names.

    Raises:
        ValueError: If any required curve is missing.
    """
    missing_curves = [curve for curve in required_curves if curve not in log_data.columns]
    if missing_curves:
        raise ValueError(f"Missing required curves: {', '.join(missing_curves)}")
    

def vp_from_dt(dt_log: pd.Series) -> pd.Series:
    """
    Calculate P-wave velocity from a sonic log.

    Args:
        dt_log (pd.Series): Sonic log data.

    Returns:
        pd.Series: P-wave velocity log.
    """
    return 1 / ( dt_log * 3.28084e-6 )

def vs_from_dts(dts_log: pd.Series) -> pd.Series:
    """
    Calculate S-wave velocity from a sonic log.

    Args:
        dts_log (pd.Series): Sonic log data.

    Returns:
        pd.Series: S-wave velocity log.
    """
    return 1 / ( dts_log * 3.28084e-6 )