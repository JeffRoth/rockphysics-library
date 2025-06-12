# rock-physics: A Python Library for Rock Physics Analysis

rock-physics is a Python library designed to provide tools and utilities for common rock physics calculations, well log analysis, and basic seismic modeling workflows.

## Core Features

* **Well Log Data Handling:**
    * Load LAS (Log ASCII Standard) files into structured `Well` object.
    * Easy access to log curves and metadata.
* **Petrophysical Calculations:**
    * **Porosity:** Density porosity, Sonic porosity (Wyllie & Raymer-Hunt-Gardner).
    * **Volume of Shale ($V_{shale}$):** Linear method from Gamma Ray.
    * **Water Saturation ($S_w$):** Archie's equation (references for Simandoux and other shaly sand models considered for future expansion).
    * (Future: Other petrophysical parameters and models).
* **Elastic Properties:**
    * Calculate P-wave ($V_P$) and S-wave ($V_S$) velocities from elastic moduli and density.
    * Calculate elastic moduli (Bulk, Shear) from $V_P, V_S$, and density.
    * Acoustic Impedance ($AI$) calculation.
    * **Castagna's Mudrock Line:** Estimate $V_S$ in shales from $V_P$.
* **Seismic Utilities:**
    * **Time-Depth Conversion:** Convert depth-indexed logs to the time domain using checkshot data (CSV input, linear interpolation).
    * **Reflectivity Series:** Calculate reflection coefficients from acoustic impedance logs (depth or time).
    * **Wavelet Generation:** Create Ricker wavelets.
    * **Synthetic Seismograms:** Convolve reflectivity series with a wavelet.
* **Visualization:**
    * Flexible log plotting capabilities to display multiple tracks with configurable appearance (colors, scales, fill-effects for VSH, spike plots for RC).

## Library Structure Overview

The library is organized into several key modules:

```
rockphysics_library/
├── rock-physics/                     # Main library package
│   ├── init.py
│   ├── core/                         # Core data objects and calculations
│   │   ├── init.py
│   │   ├── petrophysics.py           # Porosity, Vshale, Sw calculations
│   │   ├── seismic.py                # TD conversion, reflectivity, wavelets, synthetics
│   │   └── well.py                   # Well class
│   ├── io/                           # Input/Output operations
│   │   ├── init.py
│   │   ├── tops_reader.py            # Reads TOPS files into Well objects
│   │   └── well_io.py                # Reads LAS files into Well objects and saves them to las files
│   ├── models/                       # Specific rock physics models
│   │   ├── init.py
│   │   ├── elastic.py                # Elastic calculations
│   │   └── fluid.py                  # Fluid calculations
│   ├── resources/                    # Configuration files and data
│   │   ├── log_mnemonic_aliases.yaml # log mnemonics for determining log types
│   │   ├── plot_config.yaml          # configuration for plotting
│   │   └── units.yaml                # units
│   ├── utils/                        # General utility functions
│   │   ├── init.py
│   │   ├── general_utils.py          # General utility functions (e.g., unit conversions)
│   │   └── nomenclature.py           # Defines LogNomenclature class for classifying log types
│   └── visualization/                # Plotting utilities
│       ├── init.py
│       └── plotting.py               # Log plotting functions
├── examples/                         # (To be added) Jupyter notebooks and scripts
├── tests/                            # (To be added) Unit tests
└── README.md
```

## Installation

Currently, the library can be used by cloning this repository:

bash:  
`git clone <your-repository-url>`  
`cd rockphysics_library`

Ensure the rockphysics_library directory (or the directory containing the rockphysics package) is in your PYTHONPATH, or install it locally using pip:

`pip install .`

## Dependencies

Python (3.7+)  
NumPy  
Pandas  
SciPy (for interpolation and signal processing)  
Matplotlib (for plotting)  
Lasio (for reading LAS files)  
PyYAML (for loading configuration files)

You can install these dependencies using pip:

`pip install numpy pandas scipy matplotlib lasio pyyaml`

