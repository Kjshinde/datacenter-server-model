# 🖥️ datacenter-server-model — Python Branch

> **Standalone Python implementation of the server rack power, thermal equilibrium, and performance simulation model.**

[![Python](https://img.shields.io/badge/Python-3.9+-yellow?logo=python&logoColor=white)](#prerequisites)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Engine-blue?logo=pandas&logoColor=white)](#prerequisites)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../../blob/main/LICENSE)

---

## 📋 Branch Overview

This branch contains the **Python** implementation of the data center server simulation model. It provides a lightweight, license-free alternative to the [MATLAB/Simulink branch](../../tree/matlab-simulink#readme), implementing the same physics-based models with additional capabilities including **thermal equilibrium solving**, **DVFS-aware power modeling**, and **leakage power estimation with temperature-dependent scaling**.

All processor configurations and workload data are loaded directly from the **SDC Financial Model Excel spreadsheet**, making it easy to stay in sync with course data.

> 🔗 See the [main branch README](../../tree/main#readme) for the overall project description and simulation theory.

## 📂 Project Structure

```
python/
│
├── simulator.py                          # Main entry point — interactive CLI simulator
├── debug_excel.py                        # Utility to verify Excel data loading
│
├── modules/                              # Core simulation engine
│   ├── __init.py__                       # Package init
│   ├── dataclasses.py                    # Data models (CPUConfig, GPUConfig, ProcessorLoad, etc.)
│   ├── loaders.py                        # Excel data loader + DVFS frequency selection
│   ├── calculations.py                   # Wrapper — re-exports from time & power modules
│   ├── power_calculations.py             # Active power, leakage power, Tj-aware total power
│   ├── time_calculations.py              # Time-to-completion with core scaling & DVFS
│   └── equilibrium_solver.py             # Steady-state Tj solver (sweep + bisection)
│
├── data/                                 # Input data files
│   ├── SDC_Financial_Model rev6.xlsx     # Base financial model spreadsheet
│   ├── SDC_Financial_Model rev6(2).xlsx  # Updated spreadsheet (primary data source)
│   ├── SDC_Financial_Model_test.xlsx     # Test spreadsheet
│   └── SDC_Financial_Model_test_3.xlsx   # Additional test data
│
├── sweep_results/                        # Pre-computed simulation sweep outputs
│   ├── 6774p_1_B200W_8_air.csv          # Xeon 6774P × 1 + B200W × 8 (air cooled)
│   ├── 6774p_1_B200W_8_water.csv        # Xeon 6774P × 1 + B200W × 8 (water cooled)
│   ├── 6774p_2_B200W_8_air.csv          # Xeon 6774P × 2 + B200W × 8 (air cooled)
│   ├── 6774p_2_B200W_8_water.csv        # Xeon 6774P × 2 + B200W × 8 (water cooled)
│   ├── 6543P-B_2_B100A_8_air.csv        # Xeon 6543P-B × 2 + B100A × 8 (air cooled)
│   ├── 6716P-B_1_B200W_8_air.csv        # Xeon 6716P-B × 1 + B200W × 8 (air cooled)
│   ├── 6716P-B_1_B200W_8_water.csv      # Xeon 6716P-B × 1 + B200W × 8 (water cooled)
│   ├── 6716P-B_1_B200W_8_water_custA.csv
│   ├── 6978P_1_B200W_8_water.csv        # Xeon 6978P × 1 + B200W × 8 (water cooled)
│   └── 6978P_8_B200W_8_water.csv        # Xeon 6978P × 8 + B200W × 8 (water cooled)
│
├── simulation_sweep_results.csv          # Aggregated sweep results
├── gpu_leakage_explanation.md            # Technical note on GPU leakage power calculation
├── model_usage.md                        # Excel row-mapping reference for parameters
├── requirements.txt                      # Python dependencies
├── package.json                          # npm metadata (for Git integration)
└── .gitignore
```

## 🔧 Prerequisites

| Requirement | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Runtime |
| **pandas** | Latest | DataFrame operations, Excel reading |
| **numpy** | Latest | Numerical computations |
| **openpyxl** | Latest | Excel `.xlsx` file parsing engine |

## 🚀 Getting Started

### 1. Clone and Switch Branch

```bash
git clone https://github.com/Kjshinde/datacenter-server-model.git
cd datacenter-server-model
git checkout python
```

### 2. Set Up Environment

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Simulator

```bash
python simulator.py
```

The simulator launches an **interactive CLI** that guides you through:

1. **Debug Mode** — Option to dump all loaded processor configs and DVFS tables for verification
2. **CPU Selection** — Choose from available CPU models (e.g., Xeon 6774P, 6716P-B, 6978P, 6543P-B)
3. **GPU Selection** — Choose from available GPU models (e.g., B100A, B200W)
4. **Chip Count** — Specify number of CPUs and GPUs per server
5. **Workload Selection** — Pick a customer workload profile (Customer A, B, C, etc.)
6. **DVFS Level** — Select operating frequency level (F1–F5)
7. **Cooling Type** — Choose air or water cooling
8. **Simulation** — Runs power, thermal, and time calculations

## 🧩 Architecture

### Module Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                        simulator.py                               │
│                     (Interactive CLI)                              │
│                                                                   │
│  ┌─────────────┐   ┌──────────────────┐   ┌───────────────────┐  │
│  │   loaders    │──▶│   dataclasses     │◀──│   calculations    │  │
│  │             │   │                  │   │   (wrapper)        │  │
│  │ • Excel I/O  │   │ • CPUConfig      │   │                   │  │
│  │ • DVFS select│   │ • GPUConfig      │   │  ┌─────────────┐  │  │
│  │ • Model list │   │ • ProcessorConfig│   │  │  power_calc  │  │  │
│  └─────────────┘   │ • CPULoad        │   │  │  • Active    │  │  │
│                    │ • GPULoad        │   │  │  • Leakage   │  │  │
│                    │ • ProcessorLoad  │   │  │  • DVFS-aware│  │  │
│                    └──────────────────┘   │  └──────┬──────┘  │  │
│                                           │         │         │  │
│                                           │  ┌──────▼──────┐  │  │
│                                           │  │ equilibrium │  │  │
│                                           │  │  _solver    │  │  │
│                                           │  │ • Bisection │  │  │
│                                           │  │ • Sweep     │  │  │
│                                           │  └─────────────┘  │  │
│                                           │                   │  │
│                                           │  ┌─────────────┐  │  │
│                                           │  │  time_calc   │  │  │
│                                           │  │ • Core scale │  │  │
│                                           │  │ • DVFS freq  │  │  │
│                                           │  └─────────────┘  │  │
│                                           └───────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

### Data Models (`dataclasses.py`)

Python `@dataclass` definitions that mirror the MATLAB bus objects:

```python
@dataclass
class CPUConfig:
    HD_cores: float          # Max hardware cores per chip
    Fmax_cpu: float          # Maximum frequency (Hz)
    TDP: float               # Thermal Design Power (W)
    ACT_pwr_split: float     # Active power split ratio
    TDP_Tj: float            # Junction temp at TDP (°C)
    Tj_max: float            # Max junction temperature (°C)
    Switching_cap: float     # Switching capacitance
    V_cpu: float             # Nominal voltage (V)
    V_spec: float            # Reference voltage for leakage scaling (V)
    TDP_high_load: float     # Utilization at TDP rating
    dvfs_table: dict         # DVFS voltage-frequency lookup table
    selected_freq: float     # Currently selected DVFS frequency (Hz)
```

Similar structures exist for `GPUConfig`, `CPULoad`, `GPULoad`, `ProcessorConfig`, and `ProcessorLoad`.

### Data Loading (`loaders.py`)

All processor configurations are loaded directly from the **SDC Financial Model Excel spreadsheet**:

```python
EXCEL_FILE_PATH = 'data/SDC_Financial_Model rev6(2).xlsx'
```

The loader reads specific rows from CPU/GPU sheets to extract:
- Hardware specs (cores, TDP, frequencies, voltages)
- DVFS tables (multi-level frequency-voltage pairs)
- Customer workload profiles (instruction counts, utilization, core requirements)

Key functions:
| Function | Description |
|----------|-------------|
| `load_processor_config(cpu_model, gpu_model)` | Returns a `ProcessorConfig` with full CPU + GPU specs |
| `load_processor_load(workload_name)` | Returns a `ProcessorLoad` with 3-phase workload data |
| `get_available_models(device_type)` | Lists all CPU or GPU models in the spreadsheet |
| `select_dvfs_frequency(conf, utilization)` | Auto-selects DVFS level from utilization (0–1) |
| `select_dvfs_frequency_by_level(conf, level)` | Selects DVFS level by name (e.g., `'F3'`) |

### Power Model (`power_calculations.py`)

Implements a comprehensive power model with three components:

#### 1. Active Power
```
P_active = C_sw × V² × f_GHz × (Load / Load_TDP) × (Active_Cores / Total_Cores) × num_chips
```

- Uses **DVFS-selected voltage** (not nominal) via `_closest_voltage_for_selected()`
- Calculated per-phase (init, compute, result) and aggregated

#### 2. Leakage Power
Temperature-dependent leakage power scaled from the TDP specification:
- Uses `ACT_pwr_split` to determine leakage fraction of TDP
- Scales with voltage ratio (`V_operating / V_spec`)²
- Scales with temperature using piecewise linear model between `TDP_Tj` and `Tj_max`

#### 3. Total Power with Thermal Equilibrium
Uses the **equilibrium solver** to find the steady-state junction temperature where:
```
P_total(Tj) = P_active(constant) + P_leakage(Tj)  =  (Tj - T_ambient) / θ_ja
```

### Equilibrium Solver (`equilibrium_solver.py`)

Two methods to find the steady-state junction temperature:

| Method | Description | Use Case |
|--------|-------------|----------|
| `solve_tj_sweep()` | Sweeps temperature from `T_hi` to `T_lo` in fixed steps, finds minimum mismatch | Mirrors spreadsheet logic, good for visualization |
| `solve_tj_bisection()` | Root-finding on `residual(T) = P_model(T) - P_cooling(T)` | Precise numerical solution |

### Time Model (`time_calculations.py`)

Computes time-to-completion for each workload phase:

```python
time_phase = instructions / (effective_cores × frequency_Hz)
```

Where:
- `effective_cores = min(software_threads, hardware_cores × num_chips)`
- Frequency is the **DVFS-selected** frequency (not Fmax)
- `Main_inst_scale` factor applied to the main compute phase
- Utilization normalized to `[0, 1]` range (accepts both fraction and percentage inputs)

## 📊 Sweep Results

Pre-computed simulation results are stored in `sweep_results/` for various server configurations:

| Configuration | Cooling | File |
|--------------|---------|------|
| 1× Xeon 6774P + 8× B200W | Air | `6774p_1_B200W_8_air.csv` |
| 1× Xeon 6774P + 8× B200W | Water | `6774p_1_B200W_8_water.csv` |
| 2× Xeon 6774P + 8× B200W | Air | `6774p_2_B200W_8_air.csv` |
| 2× Xeon 6774P + 8× B200W | Water | `6774p_2_B200W_8_water.csv` |
| 2× Xeon 6543P-B + 8× B100A | Air | `6543P-B_2_B100A_8_air.csv` |
| 1× Xeon 6716P-B + 8× B200W | Air | `6716P-B_1_B200W_8_air.csv` |
| 1× Xeon 6716P-B + 8× B200W | Water | `6716P-B_1_B200W_8_water.csv` |
| 1× Xeon 6978P + 8× B200W | Water | `6978P_1_B200W_8_water.csv` |
| 8× Xeon 6978P + 8× B200W | Water | `6978P_8_B200W_8_water.csv` |

These files contain per-DVFS-level results including power breakdowns, junction temperatures, and execution times.

## 🔍 Debug Mode

Running the simulator with **Debug Mode = Yes** dumps all loaded data for verification:

```
=== DEBUG MODE: DUMPING ALL DATA USING LOADER ===

ALL CPU MODELS (4 models)
──────────────────────────────────────
CPU MODEL: Xeon 6774P
  HD_cores          = 64
  Fmax_cpu          = 2500000000.0 Hz (2.50 GHz)
  TDP               = 350.0 W
  Tj_max            = 100°C
  Switching_cap     = 1.2e-09
  V_cpu             = 1.0 V
  DVFS Table (5 entries):
    F1: Freq=0.50 GHz, Voltage=0.65 V
    F2: Freq=1.00 GHz, Voltage=0.75 V
    F3: Freq=1.50 GHz, Voltage=0.85 V
    F4: Freq=2.00 GHz, Voltage=0.95 V
    F5: Freq=2.50 GHz, Voltage=1.00 V
```

## 🔄 Comparison with MATLAB Branch

| Feature | MATLAB/Simulink | Python |
|---------|----------------|--------|
| **Data Source** | CSV files + manual mask params | Excel spreadsheet (`.xlsx`) — single source of truth |
| **Power Model** | Active power only | Active + Leakage + Thermal equilibrium |
| **Tj Solving** | Linear projection | Bisection + sweep solvers |
| **DVFS** | CSV-based profiles | Built-in DVFS table from Excel with level selection |
| **Architecture** | Simulink blocks + callbacks | Python dataclasses + modular functions |
| **Interface** | Simulink GUI | Interactive CLI |
| **License** | MATLAB license required | Free (Python + pandas + openpyxl) |
| **Cooling** | Not parameterized | Air vs. water cooling support |
| **Sweep** | Manual | Automated with CSV export |

## 📝 Notes

- The `__init.py__` filename has a typo (should be `__init__.py`) — the module still works due to explicit imports.
- `package.json` exists for Git integration metadata, not for Node.js usage.
- The `__pycache__/` directory is committed — consider adding it to `.gitignore`.
- The model assumes **single-cycle instruction execution** for time estimation.
- See `gpu_leakage_explanation.md` for a detailed walkthrough of how GPU leakage power is calculated at different temperatures.

## 🔗 Related

- [Main branch](../../tree/main#readme) — Project overview and simulation theory
- [MATLAB/Simulink branch](../../tree/matlab-simulink#readme) — Simulink implementation

---

<p align="center">
  <i>Built with 🐍 Python + 📊 Pandas</i>
</p>
