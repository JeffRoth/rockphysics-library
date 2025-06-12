# rockphysics/geomechanics/porepressure.py
"""
Pore Pressure Calculation Module

This module provides functions for pore pressure prediction using
various industry-standard methods.
"""
import pandas as pd
import numpy as np

# This module is now fully decoupled from the Well class.

def calculate_pore_pressure_eaton(
    rhob_log: pd.Series,
    indicator_log: pd.Series,
    nct_a: float,
    nct_b: float,
    indicator_type: str = 'resistivity',
    eaton_exp: float = 1.2,
    hydrostatic_grad_mpa_m: float = 0.00981
) -> pd.DataFrame:
    """
    Calculates pore pressure using Eaton's method from log Series.

    This method can use either a resistivity or sonic log as the disequilibrium
    compaction indicator.

    Args:
        rhob_log (pd.Series): Bulk density log, indexed by depth.
        indicator_log (pd.Series): The indicator log (e.g., Resistivity or Sonic),
                                   indexed by depth. Must have the same index as rhob_log.
        nct_a (float): Intercept for the Normal Compaction Trend (NCT) line.
                       For resistivity: log10(Rt) = a + b*Depth
                       For sonic: DT = a + b*Depth
        nct_b (float): Slope for the Normal Compaction Trend line.
        indicator_type (str): Type of indicator log. Either 'resistivity' or 'sonic'.
                              Defaults to 'resistivity'.
        eaton_exp (float): Eaton's exponent. Defaults to 1.2 for resistivity
                           and 3.0 for sonic.
        hydrostatic_grad_mpa_m (float): Hydrostatic pressure gradient in MPa/m. 
                                        Defaults to 0.00981 (for water).

    Returns:
        pd.DataFrame: A DataFrame containing overburden pressure (OBP_MPa), hydrostatic
                      pressure (HP_MPa), and the calculated pore pressure (PP_MPa).
    """
    if not rhob_log.index.equals(indicator_log.index):
        raise ValueError("Input logs 'rhob_log' and 'indicator_log' must have the same index.")
            
    depth = rhob_log.index.to_series()
    
    # 1. Calculate Hydrostatic Pressure
    hp_mpa = depth * hydrostatic_grad_mpa_m
    
    # 2. Calculate Overburden Pressure by integrating density
    # rhob is assumed to be in g/cc
    pressure_step = rhob_log * 0.00981 * depth.diff()
    obp_mpa = pressure_step.cumsum().fillna(0)
    
    # 3. Calculate pressure ratio based on indicator type
    if indicator_type.lower() == 'resistivity':
        log10_rt_nct = nct_a + nct_b * depth
        indicator_nct = 10 ** log10_rt_nct
        ratio = indicator_nct / indicator_log.replace(0, 0.001)
    elif indicator_type.lower() == 'sonic':
        indicator_nct = nct_a + nct_b * depth
        ratio = indicator_log.replace(0, 0.001) / indicator_nct
    else:
        raise ValueError(f"Invalid indicator_type '{indicator_type}'. Choose 'resistivity' or 'sonic'.")

    # 4. Eaton's Method using pressure gradients for stability
    obp_grad = (obp_mpa / depth).replace([np.inf, -np.inf], 0)
    pp_grad = obp_grad - (obp_grad - hydrostatic_grad_mpa_m) * (ratio ** -eaton_exp)
    pp_mpa = pp_grad * depth

    # Clean up potential numerical issues
    pp_mpa.iloc[0] = hp_mpa.iloc[0] if not hp_mpa.empty else 0
    pp_mpa.replace([np.inf, -np.inf], np.nan, inplace=True)
    pp_mpa.fillna(hp_mpa, inplace=True)

    return pd.DataFrame({
        'OBP_MPa': obp_mpa,
        'HP_MPa': hp_mpa,
        'PP_MPa': pp_mpa
    }, index=depth)

