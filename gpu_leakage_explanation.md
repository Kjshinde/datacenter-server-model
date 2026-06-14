The GPU leakage at 20°C is **not 1050.00W**, but actually **350.00W for a single GPU**. The 1050.00W you observed in the debug output `T=20°C: P_total_single=1050.00W` refers to the *total power* of a single GPU, which is the sum of its active power and leakage power at 20°C.

Here's the breakdown of how the values are calculated for a **single B200 Water GPU at 20°C**:

**1. GPU Configuration (B200 Water):**
*   `TDP` = 1400.0 W
*   `ACT_pwr_split` = 0.5 (Active Power Split)
*   `TDP_Tj` = 70.0°C (Temperature at which TDP is specified)
*   `Tj_max` = 95.0°C (Maximum Junction Temperature)
*   `V_spec` = 1.0 V (Reference voltage for leakage scaling)

**2. Active Power for a Single GPU:**
*   From the simulation, the `GPU active (main)` for 8 GPUs was 5600.00 W.
*   Therefore, for a **single GPU**, the active power (`active_power_single`) is `5600.00 W / 8 = 700.00 W`.

**3. Leakage Power Calculation for a Single GPU (`_leakage_power` function):**
The `_leakage_power` function calculates leakage based on configuration and temperature (`proj_T`). Let's trace it with `proj_T = 20°C`:

*   **`base` calculation:** This represents the base leakage at `TDP_Tj` (70°C).
    `base = conf.TDP * (1 - conf.ACT_pwr_split)`
    `base = 1400 * (1 - 0.5) = 1400 * 0.5 = 700.00 W`

*   **`dT_low` and `slope_low` calculation:** Since `proj_T` (20°C) is less than `TDP_Tj` (70°C), the "low" temperature slope is used.
    `dT_low = (conf.TDP_Tj - 20)`
    `dT_low = 70 - 20 = 50`
    `slope_low = (0.5 * base / dT_low)`
    `slope_low = (0.5 * 700) / 50 = 350 / 50 = 7.0`

*   **`leak` (temperature-scaled leakage):**
    `leak = base + ((proj_T - conf.TDP_Tj) * slope_low)`
    `leak = 700 + ((20 - 70) * 7.0)`
    `leak = 700 + (-50 * 7.0)`
    `leak = 700 - 350 = 350.00 W`

*   **`vscale` (voltage scaling):** Assuming the selected voltage for the GPU is 1.0V (F3 DVFS level for B200 Water is 1.0V) and `V_spec` is 1.0V.
    `vscale = (V / conf.V_spec) = 1.0 / 1.0 = 1.0`

*   **`final_leakage` for a single chip:**
    `final_leakage = num_chip * (leak * vscale)`
    `final_leakage = 1 * (350.00 W * 1.0) = 350.00 W`

**Conclusion:**
*   **Single GPU Active Power @ 20°C:** 700.00 W
*   **Single GPU Leakage Power @ 20°C:** 350.00 W
*   **Single GPU Total Power (`P_total_single`) @ 20°C:** `700.00 W (active) + 350.00 W (leakage) = 1050.00 W`

Therefore, the `1050.00W` you saw is the total power for one GPU, not just its leakage. The actual leakage for a single GPU at 20°C is 350.00W.