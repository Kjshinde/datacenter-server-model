# datacenter-server-model
This repo contains branches for a AI-datacenter simulation in MATLAB and python to calculate energy cost and server configuration.
# 🖥️ datacenter-server-model

> **A multi-technology simulation framework for modeling server rack power consumption, thermal behavior, and compute performance in data center environments.**

[![MATLAB](https://img.shields.io/badge/MATLAB-Simulink-blue?logo=mathworks&logoColor=white)](#matlab--simulink-branch)
[![Python](https://img.shields.io/badge/Python-3.9+-yellow?logo=python&logoColor=white)](#python-branch)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Course](https://img.shields.io/badge/Course-EEE%20498%2F591-purple)](#course-context)

---

## 📋 Overview

This repository provides a **physics-based simulation model** for estimating the power, thermal, and performance characteristics of data center server racks. The simulation models individual processor components (CPUs and GPUs) and scales up to rack-level analysis, enabling:

- ⚡ **Power Estimation** — Active and leakage power based on processor utilization, core count, voltage, and frequency
- 🌡️ **Thermal Equilibrium** — Junction temperature (Tj) solving via sweep and bisection methods to find steady-state operating temperature
- ⏱️ **Time-to-Completion** — Compute time estimation based on instruction counts, core scaling, and frequency
- 🔄 **DVFS Modeling** — Dynamic Voltage and Frequency Scaling with multi-level operating point selection
- ❄️ **Cooling Analysis** — Air vs. water cooling thermal resistance modeling
- 💰 **Financial Analysis** — Data center operational cost and net profit calculations for retrofitted server configurations

## 🏗️ Repository Structure

This repository uses a **branch-per-technology** strategy. The simulation is implemented in two independent technology stacks, each on its own branch:

```
datacenter-server-model/
├── main                  ← You are here (overview + documentation)
├── matlab-simulink       ← MATLAB/Simulink implementation
└── python                ← Python implementation
```

| Branch | Technology | Description |
|--------|-----------|-------------|
| [`matlab-simulink`](#matlab--simulink-branch) | MATLAB R2024a+ / Simulink | Block-diagram simulation using Simulink models (`.slx`) with MATLAB callback scripts. Includes mask parameterization and CSV-based configuration. |
| [`python`](#python-branch) | Python 3.9+ | Standalone Python implementation with Excel-based data loading, thermal equilibrium solving, leakage power modeling, and automated sweep simulations. |

## 🔬 Simulation Model

### Core Concepts

The server model simulates a **3-phase compute workload** on a configurable server rack:

```
┌─────────────────────────────────────────────────────────────┐
│                       SERVER RACK                           │
│                                                             │
│  ┌──────────┐  ┌──────────┐           ┌──────────┐         │
│  │  CPU #1  │  │  CPU #2  │    ...    │  CPU #N  │         │
│  └──────────┘  └──────────┘           └──────────┘         │
│  ┌──────────┐  ┌──────────┐           ┌──────────┐         │
│  │  GPU #1  │  │  GPU #2  │    ...    │  GPU #M  │         │
│  └──────────┘  └──────────┘           └──────────┘         │
│                                                             │
│  Phases:  1. Init  ──▶  2. Compute  ──▶  3. Result          │
│                                                             │
│  Outputs: Power (W) │ Temperature (°C) │ Time (s) │ Cost ($)│
└─────────────────────────────────────────────────────────────┘
```

### Workload Phases

Each compute job is broken into three sequential phases, each with independently configurable:
- **Core count** — Number of active parallel cores (software threads)
- **Utilization** — Fraction of active core capacity in use
- **Instruction count** — Total instructions to execute

| Phase | Description | Typical Dominant Processor |
|-------|-------------|--------------------------|
| **Init** | Initialization, data loading, preprocessing | CPU |
| **Compute** | Main computation kernel (inference, training, HPC) | GPU |
| **Result** | Aggregation, post-processing, output | CPU |

### Power Model

#### Active Power
```
P_active = C_sw × V² × f × (Load / Load_TDP) × (Active_Cores / Total_Cores) × num_chips
```

Where:
- `C_sw` — Switching capacitance (processor spec)
- `V` — Operating voltage (from DVFS table or nominal)
- `f` — Operating frequency (Hz, DVFS-selected)
- `Load` — Current utilization (0–1)
- `Load_TDP` — Utilization at TDP rating

#### Leakage Power (Python branch)
Temperature-dependent leakage power scaled from TDP:
- Derived from `ACT_pwr_split` (active vs. leakage fraction)
- Scales with `(V_operating / V_spec)²`
- Temperature-dependent scaling between `TDP_Tj` and `Tj_max`

#### Thermal Equilibrium (Python branch)
Steady-state Tj found where chip power equals cooling capacity:
```
P_total(Tj) = P_active + P_leakage(Tj) = (Tj - T_ambient) / θ_ja
```

### Supported Processors

| Type | Model | Cores | Max Frequency | TDP |
|------|-------|-------|--------------|-----|
| CPU | Intel Xeon 6774P | 64 | 2.5 GHz | 350 W |
| CPU | Intel Xeon 6716P-B | — | — | — |
| CPU | Intel Xeon 6978P | — | — | — |
| CPU | Intel Xeon 6543P-B | — | — | — |
| GPU | NVIDIA B100A | — | — | — |
| GPU | NVIDIA B200W | — | 1.9 GHz | 1400 W |

> Full specs for all models are available in the SDC Financial Model spreadsheet and can be dumped via the Python simulator's debug mode.

## 🚀 Quick Start

### MATLAB/Simulink

```bash
git checkout matlab-simulink
```
> Open `processor_ks.slx` in Simulink. See the [MATLAB branch README](../../tree/matlab-simulink#readme) for detailed setup.

### Python

```bash
git checkout python
pip install -r requirements.txt
python simulator.py
```
> See the [Python branch README](../../tree/python#readme) for the full interactive CLI guide.

## 🔄 Branch Comparison

| Feature | MATLAB/Simulink | Python |
|---------|----------------|--------|
| **Data Source** | CSV files + Simulink mask GUI | Excel spreadsheet (single source of truth) |
| **Power Model** | Active power | Active + Leakage + Thermal equilibrium |
| **Tj Solving** | Linear projection | Bisection + sweep numerical solvers |
| **DVFS** | CSV-based profiles | Built-in DVFS table with level/utilization selection |
| **Architecture** | Simulink blocks + MATLAB callbacks | Python dataclasses + modular functions |
| **Interface** | Simulink GUI (visual) | Interactive CLI |
| **Cooling** | Not parameterized | Air vs. water cooling (θ_ja) |
| **Sweep** | Manual | Automated with CSV export |
| **License** | MATLAB license required | Free (Python + pandas + openpyxl) |
| **Best For** | Visual block-diagram modeling, Simulink ecosystem | Scripted analysis, automation, parameter sweeps |

## 📚 Course Context

This project was developed as part of **EEE 498/591 — Data Center Systems Engineering** coursework. The simulation addresses real-world scenarios including:

- Multi-customer workload profiling (AI inference, HPC, training)
- Server rack retrofitting and financial viability analysis
- Power and thermal envelope compliance
- DVFS optimization strategies
- Air vs. water cooling trade-offs

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch from the appropriate technology branch
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description of changes

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <i>Built with 🔧 MATLAB/Simulink and 🐍 Python</i>
</p>
