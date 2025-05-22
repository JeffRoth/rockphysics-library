import pint

ureg = pint.UnitRegistry() # Ensure ureg is defined if not already

def water_density(temperature, salinity):
    """
    Calculate the density of water based on temperature and salinity
    using the UNESCO International Equation of State of Seawater (EOS-80).

    This function uses a simplified approximation of the EOS-80 equation.
    For higher accuracy, consider using a dedicated oceanographic library.

    Args:
        temperature (float): Temperature in degrees Celsius.
        salinity (float): Salinity in parts per thousand (ppt).

    Returns:
        pint.Quantity: Density of water in g/cm^3.
    """
    # Assuming temperature in Celsius, salinity in ppt
    # Simplified EOS-80 approximation (replace with full EOS-80 for accuracy)
    density = (
        999.842594
        + 6.793952e-2 * temperature
        - 9.095290e-3 * temperature ** 2
        + 1.001685e-4 * temperature ** 3
        - 1.120083e-6 * temperature ** 4
        + 6.536332e-9 * temperature ** 5
        + 8.24493e-1 * salinity
        - 4.0899e-3 * temperature * salinity
        + 7.6438e-5 * temperature ** 2 * salinity
        - 8.2467e-7 * temperature ** 3 * salinity
        + 5.3875e-9 * temperature ** 4 * salinity
        - 5.72466e-3 * salinity ** (3 / 2)
        + 1.0227e-4 * temperature * salinity ** (3 / 2)
        - 1.6546e-6 * temperature ** 2 * salinity ** (3 / 2)
        + 4.8314e-4 * salinity ** 2
    )

    return density_val * ureg.kg / ureg.meter**3 # Example unit, adjust as per original intent (g/cm^3)


def water_bulk_modulus(temperature, salinity, pressure=1.01325):
    """
    Calculate the bulk modulus of water based on temperature, salinity, and pressure.

    This function uses a simplified approximation. For higher accuracy,
    consider using a dedicated oceanographic library.

    Args:
        temperature (float): Temperature in degrees Celsius.
        salinity (float): Salinity in parts per thousand (ppt).
        pressure (pint.Quantity, optional): Pressure in bar. 
            Defaults to 1.01325 bar (atmospheric pressure).

    Returns:
        pint.Quantity: Bulk modulus of water in GPa.
    """
    # Assuming temperature in Celsius, salinity in ppt, pressure in bar
    # Simplified approximation (replace with a more accurate model)
    bulk_modulus_val = (
        2.2
        + 0.1 * temperature
        - 0.001 * salinity
        + 0.00004 * pressure
    )
    return bulk_modulus_val * ureg.GPa


def oil_density(api_gravity, temperature):
    """
    Calculate the density of oil based on API gravity and temperature.

    This function uses a simplified approximation. For higher accuracy,
    consider using a dedicated petroleum engineering library.

    Args:
        api_gravity (float): API gravity of the oil.
        temperature (float): Temperature in degrees Celsius.

    Returns:
        pint.Quantity: Density of oil in g/cm^3.
    """
    # Assuming temperature in Celsius
    # Simplified approximation (replace with a more accurate correlation)
    density_val = (
        141.5 / (api_gravity + 131.5) - 0.0006 * temperature
    )
    return density_val * ureg.gram / ureg.centimeter**3


def oil_bulk_modulus(api_gravity, temperature, pressure=1.01325):
    """
    Calculate the bulk modulus of oil based on API gravity, temperature, and pressure.

    This function uses a simplified approximation. For higher accuracy,
    consider using a dedicated petroleum engineering library.

    Args:
        api_gravity (float): API gravity of the oil.
        temperature (float): Temperature in degrees Celsius.
        pressure (pint.Quantity, optional): Pressure in bar. 
            Defaults to 1.01325 bar (atmospheric pressure).

    Returns:
        pint.Quantity: Bulk modulus of oil in GPa.
    """
    # Assuming temperature in Celsius, pressure in bar
    # Simplified approximation (replace with a more accurate correlation)
    bulk_modulus_val = (
        1.2
        + 0.005 * api_gravity
        - 0.0001 * temperature
        + 0.00001 * pressure
    )
    return bulk_modulus_val * ureg.GPa


def gas_density(gas_gravity, pressure, temperature):
    """
    Calculate the density of gas based on gas gravity, pressure, and temperature
    using the ideal gas law.

    Args:
        gas_gravity (float): Gas gravity (relative to air).
        pressure (float): Pressure in bar.
        temperature (float): Temperature in degrees Celsius.

    Returns:
        pint.Quantity: Density of gas in g/cm^3.
    """
    # Assuming pressure in bar, temperature in Celsius
    # Ideal gas law calculation
    R = 8.3145  # Ideal gas constant
    M = gas_gravity * 28.97  # Molar mass of gas
    temperature_kelvin = temperature + 273.15 # Convert Celsius to Kelvin
    pressure_pascal = pressure * 1e5 # Convert bar to Pascal
    density_val = (pressure_pascal * M) / (R * temperature_kelvin) # kg/m^3
    return (density_val / 1000) * ureg.gram / ureg.centimeter**3 # Convert to g/cm^3


def gas_bulk_modulus(gas_gravity, pressure, temperature):
    """
    Calculate the bulk modulus of gas based on gas gravity, pressure, and temperature.

    This function uses a simplified approximation. For higher accuracy,
    consider using an appropriate equation of state (e.g., Peng-Robinson).

    Args:
        gas_gravity (float): Gas gravity (relative to air).
        pressure (float): Pressure in bar.
        temperature (float): Temperature in degrees Celsius.

    Returns:
        pint.Quantity: Bulk modulus of gas in GPa.
    """
    # Assuming pressure in bar, temperature in Celsius
    # Simplified approximation (replace with a more accurate model)
    bulk_modulus_val = (
        0.8
        + 0.001 * pressure
        - 0.0001 * temperature
    )
    return bulk_modulus_val * ureg.GPa