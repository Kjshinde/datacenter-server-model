# In: main_simulator.py
import pandas as pd
from modules.loaders import load_processor_config, load_processor_load, select_dvfs_frequency_by_level, get_available_models
from modules.calculations import calculate_total_time, calculate_power
import sys

def get_validated_integer_input(prompt_message, min_value=1):
    """
    Prompts the user for an integer input and validates it.
    Ensures the input is an integer and is not less than min_value.
    """
    while True:
        try:
            user_input = input(prompt_message)
            value = int(user_input)
            if value < min_value:
                print(f"Input cannot be less than {min_value}. Please try again.")
            else:
                return value
        except ValueError:
            print("Invalid input. Please enter an integer.")

def select_from_list(options, prompt_name):
    print(f"\nAvailable {prompt_name}s:")
    for i, option in enumerate(options):
        print(f"{i + 1}. {option}")
    
    while True:
        try:
            selection = input(f"Select a {prompt_name} (1-{len(options)}): ")
            idx = int(selection) - 1
            if 0 <= idx < len(options):
                return options[idx]
            else:
                print(f"Invalid selection. Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# --- DEBUG MODE SELECTION ---
print("\n--- Debug Mode ---")
debug_mode_options = ['No', 'Yes']
DEBUG_MODE = select_from_list(debug_mode_options, "Enable Debug Mode") == 'Yes'

# --- IF DEBUG MODE: DUMP ALL DATA USING LOADER AND EXIT ---
if DEBUG_MODE:
    print("\n" + "="*100)
    print("DEBUG MODE: DUMPING ALL DATA USING LOADER")
    print("="*100)
    
    # Get all available models
    try:
        available_cpus = get_available_models('CPU')
        available_gpus = get_available_models('GPU')
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to get available models: {e}")
        sys.exit(1)
    
    # Dump all CPU configurations
    print("\n" + "="*100)
    print(f"ALL CPU MODELS ({len(available_cpus)} models)")
    print("="*100)
    for cpu_model in available_cpus:
        try:
            # Load just this CPU with a dummy GPU
            temp_config = load_processor_config(cpu_model, available_gpus[0])
            cpu_conf = temp_config.cpu_conf
            
            print("\n" + "─"*100)
            print(f"CPU MODEL: {cpu_model}")
            print("─"*100)
            print(f"  HD_cores          = {cpu_conf.HD_cores}")
            print(f"  Fmax_cpu          = {cpu_conf.Fmax_cpu} Hz ({cpu_conf.Fmax_cpu / 1e9:.2f} GHz)")
            print(f"  TDP               = {cpu_conf.TDP} W")
            print(f"  Tj_max            = {cpu_conf.Tj_max}°C")
            print(f"  ACT_pwr_split     = {cpu_conf.ACT_pwr_split}")
            print(f"  TDP_Tj            = {cpu_conf.TDP_Tj}°C")
            print(f"  Switching_cap     = {cpu_conf.Switching_cap}")
            print(f"  TDP_high_load     = {cpu_conf.TDP_high_load}")
            print(f"  V_cpu             = {cpu_conf.V_cpu} V  (Nominal voltage, V3 from Excel)")
            print(f"  V_spec            = {cpu_conf.V_spec} V  (Reference voltage for leakage scaling)")
            print(f"  NOTE: Actual operating voltage is dynamically selected from DVFS table below")
            print(f"  DVFS Table ({len(cpu_conf.dvfs_table)} entries):")
            for level, values in sorted(cpu_conf.dvfs_table.items()):
                print(f"    {level}: Freq={values['freq']/1e9:.2f} GHz, Voltage={values['voltage']:.2f} V")
        except Exception as e:
            print(f"\n[ERROR] ERROR loading CPU {cpu_model}: {e}")
    
    # Dump all GPU configurations
    print("\n" + "="*100)
    print(f"ALL GPU MODELS ({len(available_gpus)} models)")
    print("="*100)
    for gpu_model in available_gpus:
        try:
            # Load just this GPU with a dummy CPU
            temp_config = load_processor_config(available_cpus[0], gpu_model)
            gpu_conf = temp_config.gpu_conf
            
            print("\n" + "─"*100)
            print(f"GPU MODEL: {gpu_model}")
            print("─"*100)
            print(f"  HD_cores          = {gpu_conf.HD_cores}")
            print(f"  Fmax_gpu          = {gpu_conf.Fmax_gpu} Hz ({gpu_conf.Fmax_gpu / 1e9:.2f} GHz)")
            print(f"  TDP               = {gpu_conf.TDP} W")
            print(f"  Tj_max            = {gpu_conf.Tj_max}°C")
            print(f"  ACT_pwr_split     = {gpu_conf.ACT_pwr_split}")
            print(f"  TDP_Tj            = {gpu_conf.TDP_Tj}°C")
            print(f"  Switching_cap     = {gpu_conf.Switching_cap}")
            print(f"  TDP_high_load     = {gpu_conf.TDP_high_load}")
            print(f"  V_gpu             = {gpu_conf.V_gpu} V  (Nominal voltage, V3 from Excel)")
            print(f"  V_spec            = {gpu_conf.V_spec} V  (Reference voltage for leakage scaling)")
            print(f"  NOTE: Actual operating voltage is dynamically selected from DVFS table below")
            print(f"  DVFS Table ({len(gpu_conf.dvfs_table)} entries):")
            for level, values in sorted(gpu_conf.dvfs_table.items()):
                print(f"    {level}: Freq={values['freq']/1e9:.2f} GHz, Voltage={values['voltage']:.2f} V")
        except Exception as e:
            print(f"\n[ERROR] ERROR loading GPU {gpu_model}: {e}")
    
    # Dump all workload configurations
    print("\n" + "="*100)
    print("ALL WORKLOAD DATA")
    print("="*100)
    
    customer_workload_mapping = {
        'Customer A': ('Compute A', 'Compute AG'),
        'Customer B': ('Compute B', 'Compute BG'),
        'Customer C': ('Compute C', 'Compute CG'),
    }
    
    for customer_name, (cpu_load_col, gpu_load_col) in customer_workload_mapping.items():
        try:
            processor_load = load_processor_load(cpu_load_col, gpu_load_col)
            
            print("\n" + "─"*100)
            print(f"WORKLOAD: {customer_name}")
            print("─"*100)
            
            print(f"\n  CPU LOAD ({cpu_load_col}):")
            cpu_load = processor_load.cpu_load
            print(f"    init_core       = {cpu_load.init_core}")
            print(f"    init_uti        = {cpu_load.init_uti}")
            print(f"    init_inst       = {cpu_load.init_inst}")
            print(f"    comp_core       = {cpu_load.comp_core}")
            print(f"    comp_uti        = {cpu_load.comp_uti}")
            print(f"    comp_inst       = {cpu_load.comp_inst}")
            print(f"    result_core     = {cpu_load.result_core}")
            print(f"    result_uti      = {cpu_load.result_uti}")
            print(f"    result_inst     = {cpu_load.result_inst}")
            print(f"    Main_inst_scale = {cpu_load.Main_inst_scale}")
            
            print(f"\n  GPU LOAD ({gpu_load_col}):")
            gpu_load = processor_load.gpu_load
            print(f"    init_core       = {gpu_load.init_core}")
            print(f"    init_uti        = {gpu_load.init_uti}")
            print(f"    init_inst       = {gpu_load.init_inst}")
            print(f"    comp_core       = {gpu_load.comp_core}")
            print(f"    comp_uti        = {gpu_load.comp_uti}")
            print(f"    comp_inst       = {gpu_load.comp_inst}")
            print(f"    result_core     = {gpu_load.result_core}")
            print(f"    result_uti      = {gpu_load.result_uti}")
            print(f"    result_inst     = {gpu_load.result_inst}")
            print(f"    Main_inst_scale = {gpu_load.Main_inst_scale}")
        except Exception as e:
            print(f"\n[ERROR] ERROR loading workload {workload_name}: {e}")
    
    print("\n" + "="*100)
    print("END DEBUG MODE - ALL DATA DUMPED")
    print("="*100)
    
    # Exit after dumping
    sys.exit(0)

# --- 1. HARDWARE SELECTION ---
print("\n--- Hardware Selection ---")
try:
    available_cpus = get_available_models('CPU')
    CHOSEN_CPU_MODEL = select_from_list(available_cpus, "CPU Model")
    
    available_gpus = get_available_models('GPU')
    CHOSEN_GPU_MODEL = select_from_list(available_gpus, "GPU Model")
except Exception as e:
    print(f"[ERROR] ERROR: Failed to load available models: {e}")
    sys.exit(1)

# --- COOLING SELECTION ---
cooling_options = ['Air', 'Water', 'Water Enhanced']

print("\n--- Cooling Selection ---")
COOLING = select_from_list(cooling_options, "Cooling")

NUM_CPUS_PER_SERVER = get_validated_integer_input("Enter the number of CPUs per server (e.g., 2): ")
NUM_GPUS_PER_SERVER = get_validated_integer_input("Enter the number of GPUs per server (e.g., 8): ")

# Constraint: Maximum 8 GPUs per server
MAX_GPUS_PER_SERVER = 8
if NUM_GPUS_PER_SERVER > MAX_GPUS_PER_SERVER:
    print(f"[ERROR] ERROR: Cannot simulate more than {MAX_GPUS_PER_SERVER} GPUs per server.")
    sys.exit(1)

SERVER_OVERHEAD_W = 4000
T_AMBIENT_C = 20.0

# --- Set theta_ja based on cooling type ---
if COOLING == 'Air':
    THETA_JA_CPU_C_PER_W = 0.08
    THETA_JA_GPU_C_PER_W = 0.08
elif COOLING == 'Water':
    THETA_JA_CPU_C_PER_W = 0.05
    THETA_JA_GPU_C_PER_W = 0.05
else:  # Water Enhanced
    THETA_JA_CPU_C_PER_W = 0.04
    THETA_JA_GPU_C_PER_W = 0.04

# --- TEMPERATURE MODE SELECTION ---
print("\n--- Temperature Mode Selection ---")
temp_mode_options = ['Equilibrium (Calculate Tj)', 'Fixed Tj (User Specified)']
TEMP_MODE = select_from_list(temp_mode_options, "Temperature Mode")

FIXED_CPU_TJ = None
FIXED_GPU_TJ = None

if TEMP_MODE == 'Fixed Tj (User Specified)':
    print("\n--- Fixed Temperature Input ---")
    while True:
        try:
            cpu_tj_input = input("Enter fixed CPU junction temperature (°C, e.g., 70): ")
            FIXED_CPU_TJ = float(cpu_tj_input)
            if FIXED_CPU_TJ < T_AMBIENT_C:
                print(f"CPU Tj cannot be less than ambient ({T_AMBIENT_C}°C). Please try again.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    while True:
        try:
            gpu_tj_input = input("Enter fixed GPU junction temperature (°C, e.g., 80): ")
            FIXED_GPU_TJ = float(gpu_tj_input)
            if FIXED_GPU_TJ < T_AMBIENT_C:
                print(f"GPU Tj cannot be less than ambient ({T_AMBIENT_C}°C). Please try again.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    print(f"[OK] Using Fixed Tj: CPU={FIXED_CPU_TJ}°C, GPU={FIXED_GPU_TJ}°C")
else:
    print("[OK] Using Equilibrium mode (Tj will be calculated)")

print(f"\n--- Starting Simulation ---")
print(f"CPU: {NUM_CPUS_PER_SERVER}x {CHOSEN_CPU_MODEL}")
print(f"GPU: {NUM_GPUS_PER_SERVER}x {CHOSEN_GPU_MODEL}")
print(f"Temperature Mode: {TEMP_MODE}")
print("-------------------------------\n")

# --- 2. LOAD STATIC CONFIGURATION ---
try:
    processor_config = load_processor_config(CHOSEN_CPU_MODEL, CHOSEN_GPU_MODEL)
    print("[OK] Hardware configuration loaded.")
except Exception as e:
    print(f"[ERROR] ERROR: Failed to load hardware config: {e}")
    print("Please check model names and Excel file path in modules/loaders.py.")
    sys.exit(1)

# --- DEBUG: SHOW WHAT LOADER LOADED ---
if DEBUG_MODE:
    print("\n" + "="*100)
    print("DEBUG MODE: SHOWING WHAT LOADER LOADED")
    print("="*100)
    
    print("\n" + "─"*100)
    print(f"CPU CONFIGURATION: {CHOSEN_CPU_MODEL}")
    print("─"*100)
    cpu_conf = processor_config.cpu_conf
    print(f"  HD_cores          = {cpu_conf.HD_cores}")
    print(f"  Fmax_cpu          = {cpu_conf.Fmax_cpu} Hz ({cpu_conf.Fmax_cpu / 1e9:.2f} GHz)")
    print(f"  TDP               = {cpu_conf.TDP} W")
    print(f"  Tj_max            = {cpu_conf.Tj_max}°C")
    print(f"  ACT_pwr_split     = {cpu_conf.ACT_pwr_split}")
    print(f"  TDP_Tj            = {cpu_conf.TDP_Tj}°C")
    print(f"  Switching_cap     = {cpu_conf.Switching_cap}")
    print(f"  TDP_high_load     = {cpu_conf.TDP_high_load}")
    print(f"  V_cpu             = {cpu_conf.V_cpu} V")
    print(f"  V_spec            = {cpu_conf.V_spec} V")
    print(f"  DVFS Table ({len(cpu_conf.dvfs_table)} entries):")
    for level, values in sorted(cpu_conf.dvfs_table.items()):
        print(f"    {level}: Freq={values['freq']/1e9:.2f} GHz, Voltage={values['voltage']:.2f} V")
    
    print("\n" + "─"*100)
    print(f"GPU CONFIGURATION: {CHOSEN_GPU_MODEL}")
    print("─"*100)
    gpu_conf = processor_config.gpu_conf
    print(f"  HD_cores          = {gpu_conf.HD_cores}")
    print(f"  Fmax_gpu          = {gpu_conf.Fmax_gpu} Hz ({gpu_conf.Fmax_gpu / 1e9:.2f} GHz)")
    print(f"  TDP               = {gpu_conf.TDP} W")
    print(f"  Tj_max            = {gpu_conf.Tj_max}°C")
    print(f"  ACT_pwr_split     = {gpu_conf.ACT_pwr_split}")
    print(f"  TDP_Tj            = {gpu_conf.TDP_Tj}°C")
    print(f"  Switching_cap     = {gpu_conf.Switching_cap}")
    print(f"  TDP_high_load     = {gpu_conf.TDP_high_load}")
    print(f"  V_gpu             = {gpu_conf.V_gpu} V")
    print(f"  V_spec            = {gpu_conf.V_spec} V")
    print(f"  DVFS Table ({len(gpu_conf.dvfs_table)} entries):")
    for level, values in sorted(gpu_conf.dvfs_table.items()):
        print(f"    {level}: Freq={values['freq']/1e9:.2f} GHz, Voltage={values['voltage']:.2f} V")
    
    print("\n" + "─"*100)
    print("SIMULATION PARAMETERS")
    print("─"*100)
    print(f"  Cooling           = {COOLING}")
    print(f"  THETA_JA_CPU      = {THETA_JA_CPU_C_PER_W}°C/W")
    print(f"  THETA_JA_GPU      = {THETA_JA_GPU_C_PER_W}°C/W")
    print(f"  T_AMBIENT         = {T_AMBIENT_C}°C")
    print(f"  SERVER_OVERHEAD   = {SERVER_OVERHEAD_W} W")
    print(f"  NUM_CPUS          = {NUM_CPUS_PER_SERVER}")
    print(f"  NUM_GPUS          = {NUM_GPUS_PER_SERVER}")
    
    print("\n" + "="*100)
    print("END DEBUG OUTPUT")
    print("="*100 + "\n")

# --- RUN MODE SELECTION ---
print("\n--- Run Mode Selection ---")
run_mode_options = ['Single Simulation', 'Parameter Sweep']
run_mode = select_from_list(run_mode_options, "Run Mode")

# --- 3. DEFINE WORKLOAD MAPPINGS ---
# Direct mapping: Customer -> (CPU_Load_Column, GPU_Load_Column)
customer_to_workload_map = {
    'Customer A': ('Compute A', 'Compute AG'),
    'Customer B': ('Compute B', 'Compute BG'),
    'Customer C': ('Compute C', 'Compute CG'),
}

results = []

if run_mode == 'Parameter Sweep':
    # --- PARAMETER SWEEP MODE ---
    print("\n" + "="*50)
    print("PARAMETER SWEEP MODE")
    print("="*50)
    
    cpu_dvfs_options = sorted(list(processor_config.cpu_conf.dvfs_table.keys()))
    gpu_dvfs_options = sorted(list(processor_config.gpu_conf.dvfs_table.keys()))
    
    print(f"Sweeping all combinations of:")
    print(f"  - Customers: {len(customer_to_workload_map)}")
    print(f"  - CPU DVFS Levels: {len(cpu_dvfs_options)}")
    print(f"  - GPU DVFS Levels: {len(gpu_dvfs_options)}")
    
    total_combinations = len(customer_to_workload_map) * len(cpu_dvfs_options) * len(gpu_dvfs_options)
    print(f"Total simulations: {total_combinations}")
    print("="*50 + "\n")
    
    sim_count = 0
    
    # Triple nested loop: Customer -> CPU DVFS -> GPU DVFS
    for customer_label, (cpu_load_col, gpu_load_col) in customer_to_workload_map.items():
        processor_load = load_processor_load(cpu_load_col, gpu_load_col)
        
        for cpu_dvfs_level in cpu_dvfs_options:
            for gpu_dvfs_level in gpu_dvfs_options:
                sim_count += 1
                print(f"[{sim_count}/{total_combinations}] {customer_label} | CPU:{cpu_dvfs_level} | GPU:{gpu_dvfs_level}")
                
                # Set DVFS
                select_dvfs_frequency_by_level(processor_config.cpu_conf, cpu_dvfs_level)
                select_dvfs_frequency_by_level(processor_config.gpu_conf, gpu_dvfs_level)
                
                # Calculate time
                total_time, status_text, time_breakdown = calculate_total_time(
                    NUM_CPUS_PER_SERVER,
                    NUM_GPUS_PER_SERVER,
                    processor_load,
                    processor_config
                )
                
                # Calculate power
                max_power = calculate_power(
                    SERVER_OVERHEAD_W,
                    NUM_CPUS_PER_SERVER,
                    NUM_GPUS_PER_SERVER,
                    processor_load,
                    processor_config,
                    T_AMBIENT_C,
                    THETA_JA_CPU_C_PER_W,
                    THETA_JA_GPU_C_PER_W,
                    CHOSEN_CPU_MODEL,
                    CHOSEN_GPU_MODEL,
                    FIXED_CPU_TJ,  # NEW: Pass fixed Tj
                    FIXED_GPU_TJ   # NEW: Pass fixed Tj
                )
                
                # Store results
                results.append({
                    'Customer': customer_label,
                    'CPU_Workload': cpu_load_col,
                    'GPU_Workload': gpu_load_col,
                    'CPU_Model': CHOSEN_CPU_MODEL,
                    'GPU_Model': CHOSEN_GPU_MODEL,
                    'CPU_Count': NUM_CPUS_PER_SERVER,
                    'GPU_Count': NUM_GPUS_PER_SERVER,
                    'Cooling': COOLING,
                    'Temp_Mode': TEMP_MODE,  # NEW: Include temp mode
                    'CPU_DVFS': cpu_dvfs_level,
                    'GPU_DVFS': gpu_dvfs_level,
                    'Calc_Time_sec': total_time,
                    'Max_Power_W': max_power["max_power"],
                    'CPU_Temp_C': max_power["cpu_temp"],
                    'GPU_Temp_C': max_power["gpu_temp"],
                    'CPU_Leak_W': max_power["cpu_leak"],
                    'GPU_Leak_W': max_power["gpu_leak"],
                    'CPU_Active_Main_W': max_power["cpu_active"]["main"],
                    'GPU_Active_Main_W': max_power["gpu_active"]["main"],
                    'Bottleneck': status_text
                })
    
    # Save to CSV
    results_df = pd.DataFrame(results)
    csv_filename = 'simulation_sweep_results.csv'
    results_df.to_csv(csv_filename, index=False)
    
    print("\n" + "="*50)
    print(f"SWEEP COMPLETE")
    print("="*50)
    print(f"Total simulations run: {sim_count}")
    print(f"Results saved to: {csv_filename}")
    print("="*50 + "\n")

else:
    # --- SINGLE SIMULATION MODE ---
    print("\n--- DVFS Selection ---")
    
    # CPU DVFS
    cpu_dvfs_options = list(processor_config.cpu_conf.dvfs_table.keys())
    if not cpu_dvfs_options:
        print("No DVFS table found for CPU. Using default.")
        CHOSEN_CPU_DVFS_LEVEL = 'Fmax'
    else:
        cpu_dvfs_options.sort() 
        CHOSEN_CPU_DVFS_LEVEL = select_from_list(cpu_dvfs_options, "CPU DVFS Level")
    
    # GPU DVFS
    gpu_dvfs_options = list(processor_config.gpu_conf.dvfs_table.keys())
    if not gpu_dvfs_options:
        print("No DVFS table found for GPU. Using default.")
        CHOSEN_GPU_DVFS_LEVEL = 'Fmax'
    else:
        gpu_dvfs_options.sort()
        CHOSEN_GPU_DVFS_LEVEL = select_from_list(gpu_dvfs_options, "GPU DVFS Level")
    
    print("\n--- Customer Selection ---")
    customer_options = list(customer_to_workload_map.keys())
    customer_label = select_from_list(customer_options, "Customer")
    
    # Get workload columns directly
    workload_data = customer_to_workload_map.get(customer_label)
    
    if not workload_data:
        print(f"[ERROR] ERROR: Invalid customer_label '{customer_label}'.  ")
        sys.exit(1)
    
    cpu_load_col, gpu_load_col = workload_data
    print(f"Running workload for {customer_label}: CPU={cpu_load_col}, GPU={gpu_load_col}")
    
    # Load the specific workload data
    processor_load = load_processor_load(cpu_load_col, gpu_load_col)
    
    # --- DEBUG: SHOW WHAT LOADER LOADED FOR WORKLOAD ---
    if DEBUG_MODE:
        print("\n" + "="*100)
        print("DEBUG MODE: SHOWING WORKLOAD DATA LOADER LOADED")
        print("="*100)
        
        print("\n" + "─"*100)
        print(f"CPU WORKLOAD: {cpu_load_col}")
        print("─"*100)
        cpu_load = processor_load.cpu_load
        print(f"  init_core         = {cpu_load.init_core}")
        print(f"  init_uti          = {cpu_load.init_uti}")
        print(f"  init_inst         = {cpu_load.init_inst}")
        print(f"  comp_core         = {cpu_load.comp_core}")
        print(f"  comp_uti          = {cpu_load.comp_uti}")
        print(f"  comp_inst         = {cpu_load.comp_inst}")
        print(f"  result_core       = {cpu_load.result_core}")
        print(f"  result_uti        = {cpu_load.result_uti}")
        print(f"  result_inst       = {cpu_load.result_inst}")
        print(f"  Main_inst_scale   = {cpu_load.Main_inst_scale}")
        
        print("\n" + "─"*100)
        print(f"GPU WORKLOAD: {gpu_load_col}")
        print("─"*100)
        gpu_load = processor_load.gpu_load
        print(f"  init_core         = {gpu_load.init_core}")
        print(f"  init_uti          = {gpu_load.init_uti}")
        print(f"  init_inst         = {gpu_load.init_inst}")
        print(f"  comp_core         = {gpu_load.comp_core}")
        print(f"  comp_uti          = {gpu_load.comp_uti}")
        print(f"  comp_inst         = {gpu_load.comp_inst}")
        print(f"  result_core       = {gpu_load.result_core}")
        print(f"  result_uti        = {gpu_load.result_uti}")
        print(f"  result_inst       = {gpu_load.result_inst}")
        print(f"  Main_inst_scale   = {gpu_load.Main_inst_scale}")
        
        print("\n" + "="*100)
        print("END DEBUG OUTPUT")
        print("="*100 + "\n")
    
    # --- SET DVFS STATE EXPLICITLY ---
    print(f"Applying DVFS levels: CPU={CHOSEN_CPU_DVFS_LEVEL}, GPU={CHOSEN_GPU_DVFS_LEVEL}")
    select_dvfs_frequency_by_level(processor_config.cpu_conf, CHOSEN_CPU_DVFS_LEVEL)
    select_dvfs_frequency_by_level(processor_config.gpu_conf, CHOSEN_GPU_DVFS_LEVEL)
    print("[OK] DVFS frequencies set on config object.")
    
    # --- RUN TIME CALCULATION ---
    total_time, status_text, time_breakdown = calculate_total_time(
        NUM_CPUS_PER_SERVER,
        NUM_GPUS_PER_SERVER,
        processor_load,
        processor_config
    )
    
    # --- SOLVE FOR MAX POWER ---
    max_power = calculate_power(
        SERVER_OVERHEAD_W,
        NUM_CPUS_PER_SERVER,
        NUM_GPUS_PER_SERVER,
        processor_load,
        processor_config,
        T_AMBIENT_C,
        THETA_JA_CPU_C_PER_W,
        THETA_JA_GPU_C_PER_W,
        CHOSEN_CPU_MODEL,
        CHOSEN_GPU_MODEL,
        FIXED_CPU_TJ,  # NEW: Pass fixed Tj
        FIXED_GPU_TJ   # NEW: Pass fixed Tj
    )
    
    # Extract metrics from the power dictionary
    max_power_val = max_power["max_power"]
    cpu_temp = max_power["cpu_temp"]
    gpu_temp = max_power["gpu_temp"]
    cpu_leak = max_power["cpu_leak"]
    gpu_leak = max_power["gpu_leak"]
    cpu_active_main = max_power["cpu_active"]["main"]
    gpu_active_main = max_power["gpu_active"]["main"]
    
    # --- PRINT DETAILED REPORT ---
    print("\n" + "="*50)
    print(f"SIMULATION REPORT: {customer_label}")
    print(f"Workload: CPU={cpu_load_col}, GPU={gpu_load_col}")
    print("="*50)
    
    print(f"\n--- Hardware Configuration ---")
    print(f"CPU: {NUM_CPUS_PER_SERVER}x {CHOSEN_CPU_MODEL} @ {CHOSEN_CPU_DVFS_LEVEL}")
    print(f"GPU: {NUM_GPUS_PER_SERVER}x {CHOSEN_GPU_MODEL} @ {CHOSEN_GPU_DVFS_LEVEL}")
    print(f"Cooling: {COOLING}")
    print(f"Ambient Temp: {T_AMBIENT_C}°C")
    print(f"Theta_JA (CPU): {THETA_JA_CPU_C_PER_W}°C/W")
    print(f"Theta_JA (GPU): {THETA_JA_GPU_C_PER_W}°C/W")
    
    print(f"\n--- Thermal & Power Metrics (Equilibrium) ---")
    print(f"{'Component':<10} | {'Temp (°C)':<10} | {'Leakage (W)':<12} | {'Active (Main) (W)':<18}")
    print("-" * 60)
    print(f"{'CPU':<10} | {cpu_temp:<10.2f} | {cpu_leak:<12.2f} | {cpu_active_main:<18.2f}")
    print(f"{'GPU':<10} | {gpu_temp:<10.2f} | {gpu_leak:<12.2f} | {gpu_active_main:<18.2f}")
    
    # --- VERBOSE PHASE-BY-PHASE BREAKDOWN ---
    print("\n" + "="*80)
    print("DETAILED PHASE-BY-PHASE BREAKDOWN")
    print("="*80)
    
    cpu_active_phases = max_power["cpu_active"]
    gpu_active_phases = max_power["gpu_active"]
    total_power_by_phase = max_power["total_power_by_phase"]
    
    # --- TIME BREAKDOWN ---
    cpu_times = time_breakdown['cpu_times']
    gpu_times = time_breakdown['gpu_times']
    phase_times = time_breakdown['phase_times']
    
    print("\n--- Time Breakdown by Phase (Seconds) ---")
    print(f"{'Phase':<10} | {'CPU Time':<15} | {'GPU Time':<15} | {'Phase Time':<15} | {'Bottleneck':<15}")
    print("-" * 80)
    
    for phase in ['init', 'main', 'result']:
        cpu_t = cpu_times[phase]
        gpu_t = gpu_times[phase]
        phase_t = phase_times[phase]
        
        # Determine bottleneck for this phase
        if cpu_t > gpu_t:
            phase_bottleneck = "CPU"
        elif gpu_t > cpu_t:
            phase_bottleneck = "GPU"
        else:
            phase_bottleneck = "Balanced"
        
        print(f"{phase.upper():<10} | {cpu_t:<15.6e} | {gpu_t:<15.6e} | {phase_t:<15.6e} | {phase_bottleneck:<15}")
    
    print(f"\nTotal Calculation Time: {total_time:.6e} sec")
    print(f"Note: Phase time is max(CPU time, GPU time) as they run in parallel.")
    
    print("\n--- Power Breakdown by Phase (Watts) ---")
    print(f"{'Phase':<10} | {'CPU Active':<12} | {'GPU Active':<12} | {'CPU Leak':<11} | {'GPU Leak':<11} | {'Overhead':<10} | {'Phase Total':<12}")
    print("-" * 105)
    
    for phase in ['init', 'main', 'result']:
        cpu_act = cpu_active_phases[phase]
        gpu_act = gpu_active_phases[phase]
        total = total_power_by_phase[phase]
        print(f"{phase.upper():<10} | {cpu_act:<12.2f} | {gpu_act:<12.2f} | {cpu_leak:<11.2f} | {gpu_leak:<11.2f} | {SERVER_OVERHEAD_W:<10.2f} | {total:<12.2f}")
    
    print(f"\nServer Max Power = {max_power_val:.2f} W (maximum across all phases)")
    print(f"Note: Leakage, overhead, and temps are constant across phases.")
    
    print("="*80)
    
    print(f"\n--- System Totals ---")
    print(f"Total Server Max Power: {max_power_val:.2f} W")
    print(f"Total Calculation Time: {total_time:.4f} sec")
    print(f"System Bottleneck:      {status_text}")
    print("="*50 + "\n")