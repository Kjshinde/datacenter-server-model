import pandas as pd
from .dataclasses import (
    CPUConfig, GPUConfig, ProcessorConfig,
    CPULoad, GPULoad, ProcessorLoad
)
import sys

# Path to your main data file
EXCEL_FILE_PATH = 'data/SDC_Financial_Model rev6(2).xlsx'

# ---------------------------------------------------------------------------
# DVFS selection helper
# ---------------------------------------------------------------------------
def select_dvfs_frequency(conf, utilization: float) -> float:
    """
    Select DVFS operating frequency (Hz) based on utilization ratio (0–1).
    Uses the conf.dvfs_table if present, otherwise falls back to Fmax_*.
    Stores the selected frequency into conf.selected_freq.
    """
    # Basic sanity on utilization
    if utilization is None:
        utilization = 0.0
    if utilization < 0.0:
        utilization = 0.0
    if utilization > 1.0:
        utilization = 1.0

    # If no DVFS table, fallback to Fmax
    dvfs = getattr(conf, "dvfs_table", None)
    if not dvfs:
        selected = getattr(conf, "Fmax_cpu", None) or getattr(conf, "Fmax_gpu", None) or 0.0
        conf.selected_freq = selected
        return selected

    # Build & sort levels by frequency
    freq_levels = []
    for k, v in dvfs.items():
        f = float(v.get("freq", 0.0))
        if f > 0:
            freq_levels.append((f, k))
    if not freq_levels:
        selected = getattr(conf, "Fmax_cpu", None) or getattr(conf, "Fmax_gpu", None) or 0.0
        conf.selected_freq = selected
        return selected

    freq_levels.sort(key=lambda x: x[0])

       # Simple heuristic: map utilization linearly to the level index
    idx = int(round(utilization * (len(freq_levels) - 1)))
    idx = max(0, min(idx, len(freq_levels) - 1))
    selected = freq_levels[idx][0]

    # --- Always enforce a valid fallback ---
    if not selected or selected == 0:
        selected = getattr(conf, "Fmax_cpu", None) or getattr(conf, "Fmax_gpu", None) or 0.0

    # If still 0, enforce Fmax directly
    if selected == 0 and hasattr(conf, "Fmax_cpu"):
        selected = conf.Fmax_cpu
    elif selected == 0 and hasattr(conf, "Fmax_gpu"):
        selected = conf.Fmax_gpu

    conf.selected_freq = selected
    return selected

def select_dvfs_frequency_by_level(conf, level: str) -> float:
    """
    Select DVFS operating frequency (Hz) based on a chosen level key (e.g., 'F3').
    Uses the conf.dvfs_table. Falls back to Fmax_* if key is invalid.
    Stores the selected frequency into conf.selected_freq.
    """
    
    # --- Get Fmax as a reliable fallback ---
    fallback_freq = getattr(conf, "Fmax_cpu", None) or getattr(conf, "Fmax_gpu", None) or 0.0
    
    # If still 0, enforce Fmax directly
    if fallback_freq == 0 and hasattr(conf, "Fmax_cpu"):
        fallback_freq = conf.Fmax_cpu
    elif fallback_freq == 0 and hasattr(conf, "Fmax_gpu"):
        fallback_freq = conf.Fmax_gpu

    # --- Try to find the level in the DVFS table ---
    dvfs = getattr(conf, "dvfs_table", None)
    selected = fallback_freq # Start with fallback
    
    if dvfs and level in dvfs:
        try:
            # Get the frequency from the table entry (it's already in Hz)
            selected = float(dvfs[level].get("freq", fallback_freq))
            # Divide by 1e9 (back to GHz) just for the print statement
            # print(f"  [DVFS Select] Found level '{level}', Freq={selected/1e9:.2f} GHz")
        except (TypeError, ValueError):
#             print(f"  [DVFS Select] Warning: Invalid 'freq' data for level {level}. Using fallback {fallback_freq/1e9:.2f} GHz.")
            selected = fallback_freq
    elif dvfs:
        # print(f"  [DVFS Select] Warning: DVFS level '{level}' not found in dvfs_table. Using fallback {fallback_freq/1e9:.2f} GHz.")
        pass # Silently use fallback
    else:
        # print(f"  [DVFS Select] Warning: No dvfs_table found. Using fallback {fallback_freq/1e9:.2f} GHz.")
        pass # Silently use fallback
    
    # --- Always enforce a valid fallback ---
    if not selected or selected == 0:
        selected = fallback_freq

    conf.selected_freq = selected
    return selected

# ---------------------------------------------------------------------------
# Helper to get available models
# ---------------------------------------------------------------------------
def get_available_models(sheet_name: str) -> list:
    """
    Returns a list of available model names from the specified sheet.
    """
    try:
        df = pd.read_excel(
            EXCEL_FILE_PATH,
            sheet_name=sheet_name,
            header=3,
            index_col=0
        )
        # The columns are the model names
        # Filter out any Unnamed columns just in case
        models = [col for col in df.columns if not str(col).startswith('Unnamed')]
        return models
    except Exception as e:
        print(f"❌ ERROR: Failed to read '{sheet_name}' sheet from {EXCEL_FILE_PATH}.")
        raise e

# ---------------------------------------------------------------------------
# Processor Config Loader (with DVFS integration)
# ---------------------------------------------------------------------------
def load_processor_config(cpu_model: str, gpu_model: str) -> ProcessorConfig:
    """
    Loads hardware configuration for a chosen CPU and GPU model,
    including DVFS tables and static specs.
    """
    # print(f"--- 1. Loading Processor Config for CPU: {cpu_model}, GPU: {gpu_model} ---")
    # print(f"Using Excel file: {EXCEL_FILE_PATH}")

    # --- CPU Configuration ---------------------------------------------------
    try:
        cpu_df = pd.read_excel(
            EXCEL_FILE_PATH,
            sheet_name='CPU',
            header=3,         # Row with Model Names
            index_col=0       # Column with Parameter Names
        )
    except Exception as e:
        print(f"❌ ERROR: Failed to read 'CPU' sheet from {EXCEL_FILE_PATH}.")
#         print(f"Make sure 'header=3' has model names and 'index_col=0' has parameter names.")
        raise e

    # --- [FIX] Handle potential duplicate row names (index) ---
    if cpu_df.index.has_duplicates:
        # print("  [Warning] Duplicate row names (index) found in 'CPU' sheet. Keeping first instance.")
        cpu_df = cpu_df[~cpu_df.index.duplicated(keep='first')]

    # print("\n--- 2. Reading CPU Config Values ---")

    try:
        v_cpu = float(cpu_df.loc['V3', cpu_model])
        # print(f"  [CPU] V3 (Nominal Voltage): {v_cpu}")

        hd_cores = float(cpu_df.loc['MaxCores', cpu_model])
        # print(f"  [CPU] MaxCores: {hd_cores}")
        
        # --- [FIX] Auto-detect frequency unit (GHz vs MHz) ---
        fmax_cpu_raw = float(cpu_df.loc['MaxFrequency', cpu_model])
        # If value is > 100, assume it's in MHz, otherwise GHz
        if fmax_cpu_raw > 100:
            fmax_cpu_ghz = fmax_cpu_raw / 1000  # MHz → GHz
            # print(f"  [CPU] MaxFrequency: {fmax_cpu_raw} MHz = {fmax_cpu_ghz} GHz")
        else:
            fmax_cpu_ghz = fmax_cpu_raw  # Already in GHz
            # print(f"  [CPU] MaxFrequency: {fmax_cpu_ghz} GHz")
        
        tdp = float(cpu_df.loc['TDP', cpu_model])
        # print(f"  [CPU] TDP: {tdp}")
        
        tj_max = float(cpu_df.loc['Tjmax', cpu_model])
        # print(f"  [CPU] Tjmax: {tj_max}")
        
        act_pwr_split = float(cpu_df.loc['Active Power split @ Load', cpu_model])
        # print(f"  [CPU] Active Power split @ Load: {act_pwr_split}")
        
        tdp_tj_raw = str(cpu_df.loc['Tjunction for TDP', cpu_model])
        # print(f"  [CPU] Tjunction for TDP (Raw): {tdp_tj_raw}")
        tdp_tj = float(tdp_tj_raw.replace('C', ''))
        
        switching_cap = float(cpu_df.loc['Switching Cap @ High_Load', cpu_model])
        # print(f"  [CPU] Switching Cap @ High_Load: {switching_cap}")
        
        tdp_high_load = float(cpu_df.loc['High_Load for TDP', cpu_model])
        # print(f"  [CPU] High_Load for TDP: {tdp_high_load}")

    except KeyError as e:
        print(f"❌ ERROR: Missing a required parameter in 'CPU' sheet index: {e}")
#         print("Please check your Excel file for the correct row name.")
        raise e
    except TypeError as e:
        print(f"❌ ERROR: {e}")
#         print("This error can be caused by duplicate row names (e.g., 'TDP') in your Excel sheet.")
        raise e

    # --- Parse CPU DVFS table safely ---
    # print("\n--- 3. Reading CPU DVFS Table (Hardcoded F0-F3) ---")
    cpu_dvfs_table = {}
    for i in range(0, 4):  # This will check i = 0, 1, 2, 3
        f_key, v_key = f'F{i}', f'V{i}'
        # print(f"  [CPU DVFS] Checking {f_key}/{v_key}...")
        
        if f_key in cpu_df.index and v_key in cpu_df.index:
            f_val = cpu_df.loc[f_key, cpu_model]
            v_val = cpu_df.loc[v_key, cpu_model]
            
            if pd.notna(f_val) and pd.notna(v_val):
                try:
                    # --- [FIX] Auto-detect frequency unit  (GHz vs MHz) ---
                    f_raw = float(f_val)
                    if f_raw > 100:
                        freq_ghz = f_raw / 1000  # MHz → GHz
                    else:
                        freq_ghz = f_raw  # Already in GHz
                    freq_hz = freq_ghz * 1e9  # GHz → Hz
                    voltage = float(v_val)
                    # print(f"    → Found: F={freq_ghz} GHz, V={v_val} V")
                    cpu_dvfs_table[f_key] = {'freq': freq_hz, 'voltage': voltage}
                except (TypeError, ValueError):
                    # print(f"    -> Invalid (non-numeric) data for {f_key}/{v_key}. Skipping.")
                    pass
            else:
                # print(f"    -> Found NaN/blank data for {f_key}/{v_key}. Skipping.")
                pass
        else:
            # print(f"    -> Keys {f_key}/{v_key} not found. Skipping.")
            pass
    
    # print(f"  [CPU DVFS] Final Table: {cpu_dvfs_table}")

    # --- [FIX] Convert Fmax from GHz to Hz ---
    fmax_hz = fmax_cpu_ghz * 1e9
    
    if not cpu_dvfs_table:
        # print("  [Warning] No valid DVFS entries. Falling back to Fmax.")
        cpu_dvfs_table['Fmax'] = {'freq': fmax_hz, 'voltage': v_cpu}

    cpu_conf = CPUConfig(
        HD_cores=hd_cores,
        Fmax_cpu=fmax_hz,
        TDP=tdp,
        Tj_max=tj_max,
        ACT_pwr_split=act_pwr_split,
        TDP_Tj=tdp_tj,
        Switching_cap=switching_cap,
        TDP_high_load=tdp_high_load,
        V_cpu=v_cpu,
        V_spec=v_cpu,
        dvfs_table=cpu_dvfs_table
    )

    # --- GPU Configuration ---------------------------------------------------
    try:
        gpu_df = pd.read_excel(
            EXCEL_FILE_PATH,
            sheet_name='GPU',
            header=3,         # Row with Model Names
            index_col=0       # Column with Parameter Names
        )
    except Exception as e:
        print(f"❌ ERROR: Failed to read 'GPU' sheet from {EXCEL_FILE_PATH}.")
#         print(f"Make sure 'header=3' has model names and 'index_col=0' has parameter names.")
        raise e

    # --- [FIX] Handle potential duplicate row names (index) ---
    if gpu_df.index.has_duplicates:
        # print("  [Warning] Duplicate row names (index) found in 'GPU' sheet. Keeping first instance.")
        gpu_df = gpu_df[~gpu_df.index.duplicated(keep='first')]

    # print("\n--- 4. Reading GPU Config Values ---")

    try:
        v_gpu = float(gpu_df.loc['V3', gpu_model])
        # print(f"  [GPU] V3 (Nominal Voltage): {v_gpu}")

        hd_cores_gpu = float(gpu_df.loc['MaxCores', gpu_model])
        # print(f"  [GPU] MaxCores: {hd_cores_gpu}")
        
        # --- [FIX] Auto-detect frequency unit (GHz vs MHz) ---
        fmax_gpu_raw = float(gpu_df.loc['MaxFrequency', gpu_model])
        # If value is > 100, assume it's in MHz, otherwise GHz
        if fmax_gpu_raw > 100:
            fmax_gpu_ghz = fmax_gpu_raw / 1000  # MHz → GHz
            # print(f"  [GPU] MaxFrequency: {fmax_gpu_raw} MHz = {fmax_gpu_ghz} GHz")
        else:
            fmax_gpu_ghz = fmax_gpu_raw  # Already in GHz
            # print(f"  [GPU] MaxFrequency: {fmax_gpu_ghz} GHz")
        
        tdp_gpu = float(gpu_df.loc['TDP', gpu_model])
        # print(f"  [GPU] TDP: {tdp_gpu}")
        
        tj_max_gpu = float(gpu_df.loc['Tjmax', gpu_model])
        # print(f"  [GPU] Tjmax: {tj_max_gpu}")
        
        act_pwr_split_gpu = float(gpu_df.loc['Active Power split @ Load', gpu_model])
        # print(f"  [GPU] Active Power split @ Load: {act_pwr_split_gpu}")
        
        tdp_tj_raw_gpu = str(gpu_df.loc['Tjunction for TDP', gpu_model])
        # print(f"  [GPU] Tjunction for TDP (Raw): {tdp_tj_raw_gpu}")
        tdp_tj_gpu = float(tdp_tj_raw_gpu.replace('C', ''))
        
        switching_cap_gpu = float(gpu_df.loc['Switching Cap @ High_Load', gpu_model])
        # print(f"  [GPU] Switching Cap @ High_Load: {switching_cap_gpu}")
        
        tdp_high_load_gpu = float(gpu_df.loc['High_Load for TDP', gpu_model])
        # print(f"  [GPU] High_Load for TDP: {tdp_high_load_gpu}")
        
    except KeyError as e:
        print(f"❌ ERROR: Missing a required parameter in 'GPU' sheet index: {e}")
#         print("Please check your Excel file for the correct row name.")
        raise e
    except TypeError as e:
        print(f"❌ ERROR: {e}")
#         print("This error can be caused by duplicate row names (e.g., 'TDP') in your Excel sheet.")
        raise e

    # --- Parse GPU DVFS table safely ---
    # --- [FIX] Changed to hardcoded loop F0-F3 to match your sheet ---
    # print("\n--- 5. Reading GPU DVFS Table (Hardcoded F0-F3) ---")
    gpu_dvfs_table = {}
    for i in range(0, 4):  # This will check i = 0, 1, 2, 3
        f_key, v_key = f'F{i}', f'V{i}'
        # print(f"  [GPU DVFS] Checking {f_key}/{v_key}...")
        
        if f_key in gpu_df.index and v_key in gpu_df.index:
            f_val = gpu_df.loc[f_key, gpu_model]
            v_val = gpu_df.loc[v_key, gpu_model]
            
            if pd.notna(f_val) and pd.notna(v_val):
                try:
                    # --- [FIX] Auto-detect frequency unit (GHz vs MHz) ---
                    f_raw = float(f_val)
                    if f_raw > 100:
                        freq_ghz = f_raw / 1000  # MHz → GHz
                    else:
                        freq_ghz = f_raw  # Already in GHz
                    freq_hz = freq_ghz * 1e9  # GHz → Hz
                    voltage = float(v_val)
                    # print(f"    → Found: F={freq_ghz} GHz, V={v_val} V")
                    gpu_dvfs_table[f_key] = {'freq': freq_hz, 'voltage': voltage}
                except (TypeError, ValueError):
                    # print(f"    -> Invalid (non-numeric) data for {f_key}/{v_key}. Skipping.")
                    pass
            else:
                # print(f"    -> Found NaN/blank data for {f_key}/{v_key}. Skipping.")
                pass
        else:
            # print(f"    -> Keys {f_key}/{v_key} not found. Skipping.")
            pass
            
    # print(f"  [GPU DVFS] Final Table: {gpu_dvfs_table}")

    # --- [FIX] Convert Fmax from GHz to Hz ---
    fmax_hz_gpu = fmax_gpu_ghz * 1e9

    if not gpu_dvfs_table:
        # print("  [Warning] No valid DVFS entries. Falling back to Fmax.")
        gpu_dvfs_table['Fmax'] = {'freq': fmax_hz_gpu, 'voltage': v_gpu}
    
    gpu_conf = GPUConfig(
        HD_cores=hd_cores_gpu,
        Fmax_gpu=fmax_hz_gpu,
        TDP=tdp_gpu,
        Tj_max=tj_max_gpu,
        ACT_pwr_split=act_pwr_split_gpu,
        TDP_Tj=tdp_tj_gpu,
        Switching_cap=switching_cap_gpu,
        TDP_high_load=tdp_high_load_gpu,
        V_gpu=v_gpu,
        V_spec=v_gpu,
        dvfs_table=gpu_dvfs_table
    )

    # print("--- Finished Loading Processor Config ---")
    return ProcessorConfig(cpu_conf=cpu_conf, gpu_conf=gpu_conf)

# ---------------------------------------------------------------------------
# Processor Load Loader
# ---------------------------------------------------------------------------
def load_processor_load(cpu_load_col: str, gpu_load_col: str) -> ProcessorLoad:
    """
    Loads workload parameters for a given workload column pair
    from the Excel 'Load' sheet.
    """
    # print(f"\n--- 1. Loading Processor Load for CPU: {cpu_load_col}, GPU: {gpu_load_col} ---")
    
    try:
        df = pd.read_excel(
            EXCEL_FILE_PATH,
            sheet_name='Load',
            header=3,
            index_col=0
        ).T
    except Exception as e:
        print(f"❌ ERROR: Failed to read 'Load' sheet from {EXCEL_FILE_PATH}.")
        raise e

    try:
        cpu_load_data = df.loc[cpu_load_col]
        gpu_load_data = df.loc[gpu_load_col]
    except KeyError as e:
        print(f"❌ ERROR: Invalid workload column name: {e}")
#         print(f"Check 'cpu_load_col' ({cpu_load_col}) and 'gpu_load_col' ({gpu_load_col}) exist in the 'Load' sheet.")
        raise e
    
    # print(f"  [Load] Reading from CPU column: {cpu_load_col}")
    # print(f"  [Load] Reading from GPU column: {gpu_load_col}")
    
    # --- CPU Load ---
    # print("\n--- 2. Reading CPU Load Values ---")
    try:
        init_core = float(cpu_load_data['Init_Parallel'])
        # print(f"  [CPU Load] Init_Parallel: {init_core}")
        
        comp_core = float(cpu_load_data['Main_Parallel'])
        # print(f"  [CPU Load] Main_Parallel: {comp_core}")
        
        result_core = float(cpu_load_data['Result_Parallel'])
        # print(f"  [CPU Load] Result_Parallel: {result_core}")
        
        init_inst = float(cpu_load_data['Init_Instr'])
        # print(f"  [CPU Load] Init_Instr: {init_inst}")
        
        comp_inst = float(cpu_load_data['Main_Instr'])
        # print(f"  [CPU Load] Main_Instr: {comp_inst}")
        
        result_inst = float(cpu_load_data['Result_Instr'])
        # print(f"  [CPU Load] Result_Instr: {result_inst}")
        
        main_inst_scale = float(cpu_load_data['Main_Instr_Scaling'])
        # print(f"  [CPU Load] Main_Instr_Scaling: {main_inst_scale}")
        
        init_uti = float(cpu_load_data['Init_Load'])
        # print(f"  [CPU Load] Init_Load: {init_uti}")
        
        comp_uti = float(cpu_load_data['Main_Load'])
        # print(f"  [CPU Load] Main_Load: {comp_uti}")
        
        result_uti = float(cpu_load_data['Result_Load'])
        # print(f"  [CPU Load] Result_Load: {result_uti}")
    except KeyError as e:
        print(f"❌ ERROR: Missing a required parameter in 'Load' sheet index: {e}")
        raise e
    except TypeError as e:
        print(f"❌ ERROR: {e}")
#         print("This error can be caused by duplicate row names in your 'Load' sheet.")
        raise e

    cpu_load = CPULoad(
        init_core=init_core,
        comp_core=comp_core,
        result_core=result_core,
        init_inst=init_inst,
        comp_inst=comp_inst,
        result_inst=result_inst,
        Main_inst_scale=main_inst_scale,
        init_uti=init_uti,
        comp_uti=comp_uti,
        result_uti=result_uti
    )
    
    # --- GPU Load ---
    # print("\n--- 3. Reading GPU Load Values ---")
    try:
        init_core_g = float(gpu_load_data['Init_Parallel'])
        # print(f"  [GPU Load] Init_Parallel: {init_core_g}")
        
        comp_core_g = float(gpu_load_data['Main_Parallel'])
        # print(f"  [GPU Load] Main_Parallel: {comp_core_g}")
        
        result_core_g = float(gpu_load_data['Result_Parallel'])
        # print(f"  [GPU Load] Result_Parallel: {result_core_g}")
        
        init_inst_g = float(gpu_load_data['Init_Instr'])
        # print(f"  [GPU Load] Init_Instr: {init_inst_g}")
        
        comp_inst_g = float(gpu_load_data['Main_Instr'])
        # print(f"  [GPU Load] Main_Instr: {comp_inst_g}")
        
        result_inst_g = float(gpu_load_data['Result_Instr'])
        # print(f"  [GPU Load] Result_Instr: {result_inst_g}")
        
        main_inst_scale_g = float(gpu_load_data['Main_Instr_Scaling'])
        # print(f"  [GPU Load] Main_Instr_Scaling: {main_inst_scale_g}")
        
        init_uti_g = float(gpu_load_data['Init_Load'])
        # print(f"  [GPU Load] Init_Load: {init_uti_g}")
        
        comp_uti_g = float(gpu_load_data['Main_Load'])
        # print(f"  [GPU Load] Main_Load: {comp_uti_g}")
        
        result_uti_g = float(gpu_load_data['Result_Load'])
        # print(f"  [GPU Load] Result_Load: {result_uti_g}")
    except KeyError as e:
        print(f"❌ ERROR: Missing a required parameter in 'Load' sheet index: {e}")
        raise e
    except TypeError as e:
        print(f"❌ ERROR: {e}")
#         print("This error can be caused by duplicate row names in your 'Load' sheet.")
        raise e

    gpu_load = GPULoad(
        init_core=init_core_g,
        comp_core=comp_core_g,
        result_core=result_core_g,
        init_inst=init_inst_g,
        comp_inst=comp_inst_g,
        result_inst=result_inst_g,
        Main_inst_scale=main_inst_scale_g,
        init_uti=init_uti_g,
        comp_uti=comp_uti_g,
        result_uti=result_uti_g
    )

    # print("--- Finished Loading Processor Load ---")
    return ProcessorLoad(cpu_load=cpu_load, gpu_load=gpu_load)