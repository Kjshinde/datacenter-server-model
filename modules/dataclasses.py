# In: modules/dataclasses.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class CPUConfig:
    HD_cores: float
    Fmax_cpu: float
    TDP: float
    ACT_pwr_split: float
    TDP_Tj: float
    Tj_max: float
    Switching_cap: float
    V_cpu: float
    V_spec: float
    TDP_high_load: float
    dvfs_table: Optional[dict] = None
    selected_freq: Optional[float] = None

@dataclass
class GPUConfig:
    HD_cores: float
    Fmax_gpu: float
    TDP: float
    ACT_pwr_split: float
    TDP_Tj: float
    Tj_max: float
    Switching_cap: float
    V_gpu: float
    V_spec: float
    TDP_high_load: float
    dvfs_table: Optional[dict] = None
    selected_freq: Optional[float] = None

@dataclass
class CPULoad:
    init_core: float
    comp_core: float
    result_core: float
    init_inst: float
    comp_inst: float
    result_inst: float
    Main_inst_scale: float
    init_uti: float
    comp_uti: float
    result_uti: float

@dataclass
class GPULoad:
    init_core: float
    comp_core: float
    result_core: float
    init_inst: float
    comp_inst: float
    result_inst: float
    Main_inst_scale: float
    init_uti: float
    comp_uti: float
    result_uti: float

@dataclass
class ProcessorConfig:
    """Holds all static hardware specifications."""
    cpu_conf: CPUConfig
    gpu_conf: GPUConfig

@dataclass
class ProcessorLoad:
    """Holds all workload-specific parameters."""
    cpu_load: CPULoad
    gpu_load: GPULoad