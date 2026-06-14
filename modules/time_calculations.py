# In: modules/time_calculations.py

from .dataclasses import ProcessorLoad, ProcessorConfig
# --- [REMOVED] No longer imports from loaders ---
# from .loaders import select_dvfs_frequency_by_level

def _normalize_util(x: float) -> float:
    """
    Normalize utilization to [0,1]. Accepts either fraction (0..1)
    or percent-style (0..100).
    """
    if x is None:
        return 0.0
    try:
        x = float(x)
    except Exception:
        return 0.0
    # If given as percentage (e.g., 80), convert to 0.8
    if x > 1.0:
        x = x / 100.0
    # Clamp
    if x < 0.0:
        x = 0.0
    if x > 1.0:
        x = 1.0
    return x

# --- [NEW] Helper to read pre-set frequency (copied from power_calculations.py) ---
def _get_frequency(conf) -> float:
    """
    Get effective frequency in Hz, preferring DVFS-selected value.
    Falls back to Fmax_cpu/Fmax_gpu if not set.
    """
    sel_freq = getattr(conf, "selected_freq", None)
    if sel_freq:
        # print(f"  [Get_Freq] Using selected_freq: {sel_freq/1e9:.2f} GHz")
        return sel_freq
        
    fallback_freq = getattr(conf, "Fmax_cpu", getattr(conf, "Fmax_gpu", 0.0))
    # print(f"  [Get_Freq] No selected_freq. Using Fmax fallback: {fallback_freq/1e9:.2f} GHz")
    return fallback_freq

# --- [MODIFIED] Updated function signature (no DVFS levels) ---
def calculate_total_time(num_cpu: float, num_gpu: float,
                         processor_load: ProcessorLoad,
                         processor_conf: ProcessorConfig
                         ) -> tuple[float, str, dict]:
    """
    Calculate total execution time using PRE-SELECTED DVFS frequencies
    found in the processor_conf object.
    
    Returns:
        tuple: (total_time, bottleneck, time_breakdown)
            - total_time: Total execution time in seconds
            - bottleneck: String describing the bottleneck
            - time_breakdown: Dictionary with detailed time breakdown by phase
    """
    TOPS_TO_OPS = 1e12

    # print("\n=== DEBUG: calculate_total_time ===")

    # --- [REMOVED] Utilization-based selection ---
    # ...

    # --- [REMOVED] Select DVFS frequencies by chosen level ---
    # cpu_freq = select_dvfs_frequency_by_level(processor_conf.cpu_conf, cpu_dvfs_level)
    # gpu_freq = select_dvfs_frequency_by_level(processor_config.gpu_conf, gpu_dvfs_level)

    # --- [NEW] Get pre-selected frequencies from config ---
    cpu_freq = _get_frequency(processor_conf.cpu_conf)
    gpu_freq = _get_frequency(processor_conf.gpu_conf)

    # print(f"Selected CPU freq: {cpu_freq/1e9:.2f} GHz")
    # print(f"Selected GPU freq: {gpu_freq/1e9:.2f} GHz")

    # --- CPU Phase Times ---
    total_cpu_cores = num_cpu * processor_conf.cpu_conf.HD_cores
    eff_cpu_init = min(processor_load.cpu_load.init_core, total_cpu_cores)
    eff_cpu_main = min(processor_load.cpu_load.comp_core, total_cpu_cores)
    eff_cpu_result = min(processor_load.cpu_load.result_core, total_cpu_cores)

    Multi_inst_cpu_scale = processor_load.cpu_load.Main_inst_scale if processor_load.cpu_load.Main_inst_scale else 1.0

    cpu_time_init = processor_load.cpu_load.init_inst / (eff_cpu_init * cpu_freq) if (eff_cpu_init and cpu_freq) else 0.0
    cpu_time_main = processor_load.cpu_load.comp_inst / (eff_cpu_main * cpu_freq * Multi_inst_cpu_scale) if (eff_cpu_main and cpu_freq and Multi_inst_cpu_scale) else 0.0
    cpu_time_result = processor_load.cpu_load.result_inst / (eff_cpu_result * cpu_freq) if (eff_cpu_result and cpu_freq) else 0.0

    # --- GPU Phase Times ---
    total_gpu_cores = num_gpu * processor_conf.gpu_conf.HD_cores
    eff_gpu_init = min(processor_load.gpu_load.init_core, total_gpu_cores)
    eff_gpu_main = min(processor_load.gpu_load.comp_core, total_gpu_cores)
    eff_gpu_result = min(processor_load.gpu_load.result_core, total_gpu_cores)

    Multi_inst_gpu_scale = processor_load.gpu_load.Main_inst_scale if processor_load.gpu_load.Main_inst_scale else 1.0

    gpu_time_init = processor_load.gpu_load.init_inst / (eff_gpu_init * gpu_freq) if (eff_gpu_init and gpu_freq) else 0.0
    gpu_time_main = (processor_load.gpu_load.comp_inst * TOPS_TO_OPS) / (eff_gpu_main * gpu_freq * Multi_inst_gpu_scale) if (eff_gpu_main and gpu_freq and Multi_inst_gpu_scale) else 0.0
    gpu_time_result = processor_load.gpu_load.result_inst / (eff_gpu_result * gpu_freq) if (eff_gpu_result and gpu_freq) else 0.0

    # --- Combine Phases (parallel CPU/GPU) ---
    time_init = max(cpu_time_init, gpu_time_init)
    time_main = max(cpu_time_main, gpu_time_main)
    time_result = max(cpu_time_result, gpu_time_result)

    total_time = time_init + time_main + time_result

    if time_main == cpu_time_main and time_main > gpu_time_main:
        bottleneck = "CPU-Limited (Main Phase)"
    elif time_main == gpu_time_main and time_main > cpu_time_main:
        bottleneck = "GPU-Limited (Main Phase)"
    else:
        bottleneck = "Balanced"

    # --- Create detailed time breakdown ---
    time_breakdown = {
        'cpu_times': {
            'init': cpu_time_init,
            'main': cpu_time_main,
            'result': cpu_time_result
        },
        'gpu_times': {
            'init': gpu_time_init,
            'main': gpu_time_main,
            'result': gpu_time_result
        },
        'phase_times': {
            'init': time_init,
            'main': time_main,
            'result': time_result
        }
    }

    # print("\n--- Phase Summary ---")
    # print(f"Init: {time_init:.6e}s, Main: {time_main:.6e}s, Result: {time_result:.6e}s")
    # print(f"Total Time: {total_time:.6e}s, Bottleneck: {bottleneck}")
    # print("=====================================\n")

    return total_time, bottleneck, time_breakdown