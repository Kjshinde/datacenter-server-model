# 🖥️ datacenter-server-model — MATLAB/Simulink Branch

> **Simulink block-diagram implementation of the server rack power, thermal, and performance simulation model.**

[![MATLAB](https://img.shields.io/badge/MATLAB-R2024a+-blue?logo=mathworks&logoColor=white)](#prerequisites)
[![Simulink](https://img.shields.io/badge/Simulink-Required-orange?logo=mathworks&logoColor=white)](#prerequisites)

---

## 📋 Branch Overview

This branch contains the **MATLAB/Simulink** implementation of the data center server simulation model. It uses Simulink block diagrams with masked subsystems for a visual, interactive modeling experience with parameterized processor configurations and compute workloads.

> 🔗 See the [main branch README](../../tree/main#readme) for the overall project description and simulation theory.

## 📂 File Structure

```
matlab-simulink/
│
├── processor_ks.slx                  # Main Simulink model (block diagram)
├── processor_ks.slx.original         # Backup of the original model
├── processor_ks.slxc                  # Simulink cache file
│
├── load_callback.m                   # Mask callback: save/load compute load profiles
├── load_dvfs_callback.m              # Mask callback: load/save DVFS table profiles
├── proc_config_load_store.m          # Mask callback: load/save processor configuration
├── save_cpu_estimate_callback.m      # Mask callback: load/save CPU estimation parameters
│
├── bus_object_structure.mat          # Bus object definitions (processor config/load structs)
├── bus_object_structure_v2.mat       # Updated bus object definitions (v2)
│
├── server_rack_model.prj            # MATLAB project file
│
├── Working_power_Tj_logic.txt        # Reference: power & junction temperature formulas
├── Working_time_core_scaling.txt     # Reference: time-to-completion & core scaling formulas
├── correty_formula_for_single_compute_load.png  # Reference diagram
│
├── test_assignment_4.m               # Standalone test script (EEE 498/591 Assignment 4)
│
├── data-conf-cvs/                    # CSV configuration profiles
│   ├── compute_load_csv/             #   └── Compute workload profiles
│   ├── conpute_configs_csv/          #   └── Processor hardware configurations
│   └── dvfs_csv/                     #   └── DVFS voltage/frequency profiles
│
├── resources/                        # Simulink project resources
└── slprj/                            # Simulink build artifacts
```

## 🔧 Prerequisites

| Requirement | Version |
|------------|---------|
| **MATLAB** | R2024a or later |
| **Simulink** | Required (included with MATLAB) |
| **Simscape** | Optional (for extended thermal modeling) |

## 🚀 Getting Started

### 1. Clone and Switch Branch

```bash
git clone https://github.com/Kjshinde/datacenter-server-model.git
cd datacenter-server-model
git checkout matlab-simulink
```

### 2. Open in MATLAB

```matlab
% Navigate to the project directory
cd('path/to/datacenter-server-model')

% Load bus object definitions into workspace
load('bus_object_structure_v2.mat')

% Open the Simulink model
open_system('processor_ks')
```

### 3. Configure the Simulation

The Simulink model uses **masked subsystems** for easy configuration. Double-click any processor block to set:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `HD_cores` | Number of hardware cores per chip | 64 (CPU), 16896 (GPU) |
| `TDP` | Thermal Design Power (Watts) | 350 (CPU), 700 (GPU) |
| `Max_freq` | Maximum operating frequency (Hz) | 2.5e9 (CPU), 1.9e9 (GPU) |
| `V_cpu` / `V_gpu` | Supply voltage (V) | 1.0 |
| `Switching_cap` | Switching capacitance | Device-specific |
| `Tj_max` | Maximum junction temperature (°C) | 100 |
| `TDP_Tj` | Junction temp at TDP (°C) | 85 |

### 4. Load Profiles from CSV

Each masked subsystem has **Load** and **Save** buttons that use the callback classes to import/export configurations from CSV files:

```matlab
% Alternatively, load a profile programmatically
T = readtable('data-conf-cvs/compute_load_csv/customerA.csv');
```

### 5. Run the Simulation

Click the **Run** button in Simulink, or from the MATLAB command window:

```matlab
sim('processor_ks')
```

## 🧩 Architecture

### Simulink Model (`processor_ks.slx`)

The block diagram implements the full server rack simulation:

```
┌─────────────────────────────────────────────────────────┐
│                    processor_ks.slx                      │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                    │
│  │  Processor    │    │  Compute     │                    │
│  │  Config Block │───▶│  Load Block  │                    │
│  │  (Masked)     │    │  (Masked)    │                    │
│  └──────────────┘    └──────┬───────┘                    │
│                             │                            │
│              ┌──────────────┼──────────────┐             │
│              ▼              ▼              ▼             │
│     ┌──────────────┐ ┌──────────┐ ┌──────────────┐      │
│     │ Power & Tj   │ │ Time-to- │ │    DVFS      │      │
│     │ Calculator   │ │ Complete │ │  Controller  │      │
│     └──────────────┘ └──────────┘ └──────────────┘      │
│              │              │              │             │
│              ▼              ▼              ▼             │
│     ┌────────────────────────────────────────────┐      │
│     │          Outputs: Power | Temp | Time       │      │
│     └────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### Callback Classes

| Class | File | Purpose |
|-------|------|---------|
| `load_callback` | `load_callback.m` | Save/load compute load parameters (core count, utilization, instructions) |
| `load_dvfs_callback` | `load_dvfs_callback.m` | Load/save DVFS voltage-frequency profiles from CSV |
| `proc_config_load_store` | `proc_config_load_store.m` | Load/save processor hardware configurations |
| `save_cpu_estimate_callback` | `save_cpu_estimate_callback.m` | Load/save CPU power estimation parameters |

### Bus Object Structure

The model uses MATLAB **Bus Objects** to pass structured data between Simulink blocks:

```
processor_conf                    processor_load
├── cpu_conf                      ├── cpu_load
│   ├── HD_cores                  │   ├── init_uti
│   ├── TDP                      │   ├── init_core
│   ├── ACT_pwr_split             │   ├── comp_uti
│   ├── TDP_Tj                   │   ├── comp_core
│   ├── Tj_max                   │   ├── result_uti
│   ├── Switching_cap             │   ├── result_core
│   ├── V_cpu                    │   └── Main_inst_scale
│   ├── Max_freq                 │
│   └── TDP_high_load            └── gpu_load
│                                     ├── init_uti
└── gpu_conf                          ├── init_core
    ├── HD_cores                      ├── comp_uti
    ├── TDP                           ├── comp_core
    ├── ACT_pwr_split                 ├── result_uti
    ├── TDP_Tj                        ├── result_core
    ├── Tj_max                        └── Main_inst_scale
    ├── Switching_cap
    ├── V_gpu
    ├── Max_freq
    └── TDP_high_load
```

### CSV Configuration System

Profiles are stored in `data-conf-cvs/` and organized by type:

| Directory | Content | Format |
|-----------|---------|--------|
| `compute_load_csv/` | Workload profiles (core count, utilization, instructions per phase) | `Parameter, Value` |
| `conpute_configs_csv/` | Processor hardware specs (cores, TDP, frequency, voltage) | `Parameter, Value` |
| `dvfs_csv/` | DVFS operating point tables (voltage-frequency pairs) | `Parameter, Value` |

## 🧪 Testing

A standalone test script is included for validating the simulation logic without Simulink:

```matlab
% Run the assignment test script
run('test_assignment_4.m')
```

This script:
- Configures Intel Xeon 6774P (CPU) and NVIDIA B100 (GPU)
- Simulates three customer workloads (A, B, C) with varying instruction counts
- Calculates power, time-to-completion, and financial metrics

## 📝 Notes

- The `.slxc` file is a Simulink cache — safe to delete and regenerate.
- `Working_power_Tj_logic.txt` and `Working_time_core_scaling.txt` contain the reference formulas used inside the Simulink function blocks.
- The model assumes **single-cycle instruction execution** for time estimation.

## 🔗 Related

- [Main branch](../../tree/main#readme) — Project overview and simulation theory
- [Python branch](../../tree/python#readme) — Python implementation of the same model

---

<p align="center">
  <i>Built with 🔧 MATLAB/Simulink</i>
</p>
