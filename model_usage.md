# Limitations
- The model need to have same name for customer Load parts, i.e., customer A , customer AG etc.

# Parameters 
## Load from xls
1. HD_cores — max cores per chip
    - row 35 - cpu
    - row 34 - gpu
2. TDP (W)
    - row 12 - cpu
    - row 11 - gpu
3. ACT_pwr_split
    - row 21 - cpu
    - row 20 - gpu
4. TDP_Tj (°C) 
    - row 19 -cpu
    - row 18 - gpu
5. Tj_max (°C) 
    - row 41 -cpu
    - row 15 - gpu
6. Switching_cap 
    - row 26 - cpu 
    - row 25 - gpu
7. TDP_high_load 
    - row 20 - cpu 
    - row 19 - gpu
8. V_spec 
    - row 45 - DVFS table — V3
    - row 44 - gpu
9. F_spec, F_max
    - row 44 - DVFS talbe - F3
    - row 43 - cpu

## Hardcoded
0. Name of the file
    - loader.py `EXCEL_FILE_PATH`
1. T ambient - 
    - simulator.py `T_AMBIENT_C`
2. theta Ja s - 
    simulator.py `THETA_JA_CPU_C_PER_W`
    simulator.py `THETA_JA_GPU_C_PER_W`
3. Server overhead - 
    - simulator.py `SERVER_OVERHEAD_W`
4. Max GPU per server
    - simulatory.py `MAX_GPUS_PER_SERVER`
5. Ambient tmeperatur
    - power_calculations.py `ambient_c`
    - simulator.py `T_AMBIENT_C`
