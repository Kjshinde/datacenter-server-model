# In: modules/power_calculations.py

from .dataclasses import ProcessorLoad, ProcessorConfig
# --- [NEW] Import solver and internal helpers ---
from .equilibrium_solver import solve_tj_bisection, solve_tj_sweep
# (Helpers _active_power and _leakage_power are already in this file)


# Debug flag for power calculations (silences verbose prints when False)
DEBUG_POWERCALC = False


# Debug flag for power calculations (silences verbose prints when False)
DEBUG_POWERCALC = False

def dprint(*args, **kwargs):
    if DEBUG_POWERCALC:
        print(*args, **kwargs)
# --- helpers --------------------------------------------------------------
# _closest_voltage_for_selected, _get_frequency... (all unchanged)
# ...
def _closest_voltage_for_selected(conf) -> float:
    """
    Return the voltage associated with the selected DVFS frequency,
    using the closest frequency match in conf.dvfs_table.
    Falls back to V_cpu/V_gpu if not available.
    """
    sel = getattr(conf, "selected_freq", None)
    dvfs = getattr(conf, "dvfs_table", None)
    dprint(f"  [V_Select] Finding voltage for selected_freq: {sel}")
    dprint(f"  [V_Select] DVFS Table: {dvfs}")
    
    if sel and dvfs:
        best = None
        best_diff = float("inf")
        for k, v in dvfs.items():
            f = float(v.get("freq", 0.0))
            if f <= 0:
                continue
            diff = abs(f - sel)
            dprint(f"  [V_Select] ...Checking {k}: Freq={f}, Diff={diff}")
            if diff < best_diff:
                best_diff = diff
                best = v
                dprint(f"  [V_Select] ...New best: {k}")
        
        if best and "voltage" in best:
            dprint(f"  [V_Select] Found best voltage: {float(best['voltage'])}")
            return float(best["voltage"])
            
    # fallback
    fallback_v = getattr(conf, "V_cpu", getattr(conf, "V_gpu", 0.0))
    dprint(f"  [V_Select] No DVFS match. Falling back to V_cpu/V_gpu: {fallback_v}")
    return fallback_v

def _get_frequency(conf) -> float:
    """
    Get effective frequency in Hz, preferring DVFS-selected value.
    Falls back to Fmax_cpu/Fmax_gpu if not set.
    """
    sel_freq = getattr(conf, "selected_freq", None)
    if sel_freq:
        dprint(f"  [Get_Freq] Using selected_freq: {sel_freq/1e9:.2f} GHz")
        return sel_freq
        
    fallback_freq = getattr(conf, "Fmax_cpu", getattr(conf, "Fmax_gpu", 0.0))
    dprint(f"  [Get_Freq] No selected_freq. Using Fmax fallback: {fallback_freq/1e9:.2f} GHz")
    return fallback_freq

def _active_power(conf, load, num_chip: float) -> dict:
    """
    Phase-wise active power for CPU or GPU given its conf and load.
    Returns dict with keys: 'init', 'main', 'result'.
    """
    dprint(f"\n  --- [_active_power] ---")
    dprint(f"  [_active_power] Inputs: conf_type={conf.__class__.__name__}, load_type={load.__class__.__name__}, num_chip={num_chip}")
    freq_hz = _get_frequency(conf)
    if not freq_hz:
        dprint(f"  [_active_power] Freq is 0. Returning all 0s.")
        return {'init': 0.0, 'main': 0.0, 'result': 0.0}

    freq_ghz = freq_hz * 1e-9
    V = _closest_voltage_for_selected(conf)
    
    dprint(f"  [_active_power] Freq: {freq_ghz:.2f} GHz ({freq_hz} Hz)")
    dprint(f"  [_active_power] Voltage: {V:.4f} V")
    dprint(f"  [_active_power] Switching_cap: {conf.Switching_cap}")
    dprint(f"  [_active_power] V^2 * F_ghz: {(V ** 2) * freq_ghz}")

    if not V or not conf.HD_cores or not conf.TDP_high_load:
        print(f"  [_active_power] ERROR: V, HD_cores, or TDP_high_load is 0. Returning 0s.")
        dprint(f"  V={V}, HD_cores={conf.HD_cores}, TDP_high_load={conf.TDP_high_load}")
        return {'init': 0.0, 'main': 0.0, 'result': 0.0}

    cap_inter = conf.Switching_cap * (V ** 2) * freq_ghz
    total_cores = num_chip * conf.HD_cores
    
    dprint(f"  [_active_power] cap_inter (C * V^2 * F_ghz): {cap_inter}")
    dprint(f"  [_active_power] total_cores (num_chip * HD_cores): {num_chip} * {conf.HD_cores} = {total_cores}")

    out = {}
    for phase, core_attr, uti_attr in [
        ('init', 'init_core', 'init_uti'),
        ('main', 'comp_core', 'comp_uti'),
        ('result', 'result_core', 'result_uti'),
    ]:
        dprint(f"    -- Phase: {phase} --")
        cores_requested = getattr(load, core_attr)
        cores = min(cores_requested, total_cores) if total_cores else 0.0
        chip_equiv = (cores / conf.HD_cores) if conf.HD_cores else 0.0
        uti = getattr(load, uti_attr)
        
        dprint(f"    cores_requested: {cores_requested}")
        dprint(f"    cores_used (min(req, total)): {cores}")
        dprint(f"    chip_equiv (cores_used / HD_cores): {cores} / {conf.HD_cores} = {chip_equiv}")
        dprint(f"    uti_raw (from sheet): {uti}")

        # Normalize percent-like values (>1) to 0..1 for power scaling:
        if uti is None:
            uti_norm = 0.0
        else:
            try:
                uti_val = float(uti)
                uti_norm = uti_val/100.0 if uti_val > 1.0 else uti_val
            except Exception:
                uti_norm = 0.0
        
        dprint(f"    uti_norm (uti / 100 or as-is): {uti_norm}")
        dprint(f"    TDP_high_load: {conf.TDP_high_load}")
        
        calc = cap_inter * (uti_norm / conf.TDP_high_load) * chip_equiv if (conf.TDP_high_load and chip_equiv) else 0.0
        dprint(f"    calc = {cap_inter} * ({uti_norm} / {conf.TDP_high_load}) * {chip_equiv}")
        dprint(f"    out['{phase}'] = {calc}")
        out[phase] = calc
        
    dprint(f"  [_active_power] Final 'out': {out}")
    dprint(f"  --- [end _active_power] ---\n")
    return out

def _leakage_power(conf, num_chip: float, proj_T: float, ambient_c=20.0) -> float:
    """
    Leakage power for CPU or GPU with temperature interpolation and voltage scaling.
    """
    dprint(f"\n  --- [_leakage_power] ---")
    dprint(f"  [_leakage_power] Inputs: conf_type={conf.__class__.__name__}, num_chip={num_chip}, proj_T={proj_T}")
    dprint(f"  [_leakage_power] Conf: TDP={conf.TDP}, ACT_pwr_split={conf.ACT_pwr_split}")
    base = conf.TDP * (1 - conf.ACT_pwr_split)
    dprint(f"  [_leakage_power] base (TDP * (1 - split)): {base}")

    # slopes around TDP_Tj
    dprint(f"  [_leakage_power] Conf: Tj_max={conf.Tj_max}, TDP_Tj={conf.TDP_Tj}")
    dT_high = (conf.Tj_max - conf.TDP_Tj)
    slope_high = (base / dT_high) if dT_high > 0 else 0.0
    dprint(f"  [_leakage_power] dT_high={dT_high}, slope_high={slope_high}")

    dT_low = (conf.TDP_Tj - ambient_c) # T_min = 20C
    slope_low = (0.5 * base / dT_low) if dT_low > 0 else 0.0
    dprint(f"  [_leakage_power] dT_low={dT_low}, slope_low={slope_low}")

    if proj_T > conf.TDP_Tj:
        dprint(f"  [_leakage_power] (Using HIGH slope logic: {proj_T} > {conf.TDP_Tj})")
        leak = base + ((proj_T - conf.TDP_Tj) * slope_high)
    else:
        dprint(f"  [_leakage_power] (Using LOW slope logic: {proj_T} <= {conf.TDP_Tj})")
        leak = base + ((proj_T - conf.TDP_Tj) * slope_low)
    
    dprint(f"  [_leakage_power] leak (temp-scaled, 1 chip): {leak}")

    V = _closest_voltage_for_selected(conf)
    vscale = (V / conf.V_spec) if getattr(conf, 'V_spec', 0) not in (None, 0) else 1.0
    
    dprint(f"  [_leakage_power] V_selected={V}, V_spec={conf.V_spec}, vscale={vscale}")

    final_leakage = num_chip * (leak * vscale)
    dprint(f"  [_leakage_power] final_leakage (num_chip * leak * vscale): {final_leakage}")
    dprint(f"  --- [end _leakage_power] ---\n")
    return final_leakage
# ...

# --- public API -----------------------------------------------------------

# --- [MODIFIED] New signature, added thermal params ---
def calculate_power(server_overhead: float, num_cpu: float, num_gpu: float, 
                    processor_load: ProcessorLoad, processor_conf: ProcessorConfig, 
                    T_AMBIENT_C: float,
                    THETA_JA_CPU_C_PER_W: float,
                    THETA_JA_GPU_C_PER_W: float,
                    cpu_model_name: str,
                    gpu_model_name: str,
                    fixed_cpu_tj: float = None,  # NEW: Optional fixed CPU Tj
                    fixed_gpu_tj: float = None   # NEW: Optional fixed GPU Tj
                    ) -> dict:
    """
    Calculate maximum total server power across phases, DVFS-aware.
    
    If fixed_cpu_tj/fixed_gpu_tj are provided, uses those temperatures directly.
    Otherwise, solves for equilibrium temperature.
    """
    
    dprint(f"\n--- [calculate_power] Initiating Power Calculation ---")
    dprint(f"  Using CPU Configuration: {cpu_model_name}")
    dprint(f"  Using GPU Configuration: {gpu_model_name}")
    dprint(f"  Using CPU Load: {processor_load.cpu_load.__class__.__name__}")
    dprint(f"  Using GPU Load: {processor_load.gpu_load.__class__.__name__}")
    
    # Get active power for all phases
    cpu_active = _active_power(processor_conf.cpu_conf, processor_load.cpu_load, num_cpu)
    gpu_active = _active_power(processor_conf.gpu_conf, processor_load.gpu_load, num_gpu)

    # --- Get Tj_max for status checks ---
    try:
        tj_max_cpu = float(getattr(processor_conf.cpu_conf, "Tj_max", 95.0))
    except Exception:
        tj_max_cpu = 95.0
    try:
        tj_max_gpu = float(getattr(processor_conf.gpu_conf, "Tj_max", 95.0))
    except Exception:
        tj_max_gpu = 95.0

    # --- TEMPERATURE MODE: Fixed vs Equilibrium ---
    if fixed_cpu_tj is not None and fixed_gpu_tj is not None:
        # FIXED TEMPERATURE MODE
        dprint(f"  [FIXED Tj MODE] Using user-specified temperatures")
        dprint(f"    CPU Tj = {fixed_cpu_tj}°C, GPU Tj = {fixed_gpu_tj}°C")
        
        proj_cpu_T = fixed_cpu_tj
        proj_gpu_T = fixed_gpu_tj
        
        # Set status based on whether fixed temps exceed Tj_max
        cpu_status = "fixed_tj"
        gpu_status = "fixed_tj"
        if proj_cpu_T > tj_max_cpu:
            cpu_status = "fixed_tj_above_limit"
        if proj_gpu_T > tj_max_gpu:
            gpu_status = "fixed_tj_above_limit"
    else:
        # EQUILIBRIUM TEMPERATURE MODE (original behavior)
        dprint(f"  [EQUILIBRIUM MODE] Solving for thermal equilibrium")
        
        # Define power function for a SINGLE CPU for equilibrium calculation
        def P_cpu_total_single(Tc):
            active_power_single = (max(cpu_active.values()) / num_cpu) if num_cpu > 0 else 0
            leakage_power_single = _leakage_power(processor_conf.cpu_conf, 1, Tc)
            return active_power_single + leakage_power_single

        # Define power function for a SINGLE GPU for equilibrium calculation
        def P_gpu_total_single(Tg):
            active_power_single = (max(gpu_active.values()) / num_gpu) if num_gpu > 0 else 0
            leakage_power_single = _leakage_power(processor_conf.gpu_conf, 1, Tg)
            return active_power_single + leakage_power_single

        # DEBUG PRINTS FOR CPU EQUILIBRIUM CALCULATION
        dprint("\n--- DEBUG: CPU Equilibrium Calculation (Single CPU) ---")
        dprint(f"  T_AMBIENT_C: {T_AMBIENT_C}")
        dprint(f"  THETA_JA_CPU_C_PER_W: {THETA_JA_CPU_C_PER_W}")
        dprint(f"  CPU Active Power (main, single): {cpu_active['main'] / num_cpu if num_cpu > 0 else 0:.2f}W")
        
        def ptheta_cpu(T):
            return (T - T_AMBIENT_C) / THETA_JA_CPU_C_PER_W

        for T_test in range(20, 40, 1):
            leakage = _leakage_power(processor_conf.cpu_conf, 1, float(T_test))
            p_total = (cpu_active['main'] / num_cpu if num_cpu > 0 else 0) + leakage
            p_theta = ptheta_cpu(float(T_test))
            residual_val = p_theta - p_total
            dprint(f"  T={T_test}°C: P_total={p_total:.2f}W, P_theta={p_theta:.2f}W, Residual={residual_val:.2f}")
        dprint("------------------------------------------\n")

        # DEBUG PRINTS FOR SINGLE GPU EQUILIBRIUM CALCULATION
        dprint("\n--- DEBUG: Single GPU Equilibrium Calculation ---")
        dprint(f"  GPU Config: {gpu_model_name}")
        dprint(f"  T_AMBIENT_C: {T_AMBIENT_C}")
        dprint(f"  THETA_JA_GPU_C_PER_W: {THETA_JA_GPU_C_PER_W}")
        
        def ptheta_gpu(T):
            return (T - T_AMBIENT_C) / THETA_JA_GPU_C_PER_W

        for T_test in range(20, 40, 1):
            active_p_single = gpu_active['main'] / num_gpu if num_gpu > 0 else 0
            leakage_p_single = _leakage_power(processor_conf.gpu_conf, 1, float(T_test))
            p_total = active_p_single + leakage_p_single
            p_theta = ptheta_gpu(float(T_test))
            residual_val = p_theta - p_total
            dprint(f"  T={T_test}°C: P_total_single={p_total:.2f}W, P_theta={p_theta:.2f}W, Residual={residual_val:.2f}")
        dprint("------------------------------------------\n")

        # Solve for equilibrium temperatures
        proj_cpu_T, _, _ = solve_tj_sweep(P_cpu_total_single, THETA_JA_CPU_C_PER_W, T_AMBIENT_C, T_hi=tj_max_cpu, T_lo=T_AMBIENT_C, step=1.0)
        proj_gpu_T, _, _ = solve_tj_sweep(P_gpu_total_single, THETA_JA_GPU_C_PER_W, T_AMBIENT_C, T_hi=tj_max_gpu, T_lo=T_AMBIENT_C, step=1.0)
        
        # Status & clamp (sheet-style)
        def _cooling(T, theta): return (T - T_AMBIENT_C) / theta
        gpu_status = "ok"
        cpu_status = "ok"
        
        # Residual at Tj_max to detect runaway
        if _cooling(tj_max_gpu, THETA_JA_GPU_C_PER_W) - P_gpu_total_single(tj_max_gpu) < 0:
            gpu_status = "thermal_runaway"
        if _cooling(tj_max_cpu, THETA_JA_CPU_C_PER_W) - P_cpu_total_single(tj_max_cpu) < 0:
            cpu_status = "thermal_runaway"
        
        # Hard cap
        if proj_gpu_T > tj_max_gpu:
            proj_gpu_T = tj_max_gpu
            if gpu_status == "ok":
                gpu_status = "above_limit_clamped"
        if proj_cpu_T > tj_max_cpu:
            proj_cpu_T = tj_max_cpu
            if cpu_status == "ok":
                cpu_status = "above_limit_clamped"
    
    dprint(f"Final Tj → CPU: {proj_cpu_T:.2f} °C, GPU: {proj_gpu_T:.2f} °C")


    # --- 2. CALCULATE MAX POWER USING SOLVED TEMPERATURES ---
    dprint(f"\n--- [calculate_power] ---")
    
    # CPU
    # cpu_active is already calculated
    cpu_leak = _leakage_power(processor_conf.cpu_conf, num_cpu, proj_cpu_T)
    # dprint(f"  [calculate_power] cpu_active: {cpu_active}")
    # dprint(f"  [calculate_power] cpu_leak: {cpu_leak}")

    # GPU
    # gpu_active is already calculated
    gpu_leak = _leakage_power(processor_conf.gpu_conf, num_gpu, proj_gpu_T)
    # dprint(f"  [calculate_power] gpu_active: {gpu_active}")
    # dprint(f"  [calculate_power] gpu_leak: {gpu_leak}")

    # Phase totals (include overhead)
    total_init = server_overhead + cpu_leak + gpu_leak + cpu_active['init'] + gpu_active['init']
    total_main = server_overhead + cpu_leak + gpu_leak + cpu_active['main'] + gpu_active['main']
    total_result = server_overhead + cpu_leak + gpu_leak + cpu_active['result'] + gpu_active['result']
    
    # dprint(f"  [calculate_power] total_init: {total_init}")
    # dprint(f"  [calculate_power] total_main: {total_main}")
    # dprint(f"  [calculate_power] total_result: {total_result}")

    max_power = max(total_init, total_main, total_result)
    # dprint(f"  [calculate_power] max_power: {max_power}")
    # dprint(f"--- [end calculate_power] ---\n")

    dprint("\n--- Power Calculation (DVFS-aware) ---")
    dprint(f"CPU freq: {_get_frequency(processor_conf.cpu_conf)/1e9:.2f} GHz, GPU freq: {_get_frequency(processor_conf.gpu_conf)/1e9:.2f} GHz")
    dprint(f"CPU active (main): {cpu_active['main']:.2f} W, GPU active (main): {gpu_active['main']:.2f} W")
    dprint(f"Total server max power: {max_power:.2f} W")
    dprint("=====================================\n")

    return {"max_power": max_power,
        "gpu_status": gpu_status,
        "cpu_status": cpu_status,
        "cpu_temp": proj_cpu_T,
        "gpu_temp": proj_gpu_T,
        "cpu_leak": cpu_leak,
        "gpu_leak": gpu_leak,
        "cpu_active": cpu_active,
        "gpu_active": gpu_active,
        "total_power_by_phase": {
            "init": total_init,
            "main": total_main,
            "result": total_result,
        }
    }