
"""
equilibrium_solver.py
---------------------
Single-file module to compute steady-state junction temperature (Tj)
by matching chip power vs. temperature to the thermal-path line.

Two solvers:
- solve_tj_sweep(): mirrors spreadsheet "sweep + min mismatch"
- solve_tj_bisection(): precise root find on residual(T) = (T - Ta)/theta_ja - P_model(T)

Helpers:
- piecewise_linear_power(): same piecewise model style as your sheet
- make_total_power_fn(): build P_total(T) = P_active_const + P_leak(T)
"""

from typing import Callable, Tuple, List, Optional

def ptheta(T: float, T_ambient: float, theta_ja: float) -> float:
    """Cooling line: heat that must be removed to hold temperature T."""
    return (T - T_ambient) / theta_ja

def solve_tj_sweep(
    power_fn: Callable[[float], float],
    theta_ja: float,
    T_ambient: float,
    T_hi: float = 100.0,
    T_lo: float = 20.0,
    step: float = 2.0
) -> Tuple[float, float, float]:
    """
    Mirror the spreadsheet logic: sweep T from T_hi down to T_lo in fixed steps,
    compute mismatch |P_model(T) - (T - Ta)/theta_ja|, and pick the T with
    the smallest mismatch.

    Returns:
        (T_best, P_model_at_T_best, P_theta_at_T_best)
    """
    if step <= 0:
        raise ValueError("step must be positive")
    T_vals: List[float] = []
    cur = float(T_hi)
    while cur >= T_lo - 1e-12:
        T_vals.append(cur)
        cur -= step

    best_T: Optional[float] = None
    best_err = float("inf")
    best_pair = (0.0, 0.0)

    for T in T_vals:
        pm = float(power_fn(T))
        pt = ptheta(T, T_ambient, theta_ja)
        err = abs(pm - pt)
        if err < best_err:
            best_err = err
            best_T = T
            best_pair = (pm, pt)

    # Defensive: best_T shouldn't be None if inputs are sane.
    if best_T is None:
        raise RuntimeError("Sweep failed to evaluate any temperatures.")
    return best_T, best_pair[0], best_pair[1]

def solve_tj_bisection(
    power_fn: Callable[[float], float],
    theta_ja: float,
    T_ambient: float,
    T_lo: Optional[float] = None,
    T_hi: Optional[float] = None,
    tol: float = 1e-3,
    max_iter: int = 100
) -> float:
    """
    Precise solve for T where residual(T) = (T - Ta)/theta_ja - P_model(T) == 0.
    If T_lo/T_hi not given, a conservative bracket is built automatically.

    Returns:
        Tj (float)
    """
    def residual(T: float) -> float:
        return ptheta(T, T_ambient, theta_ja) - float(power_fn(T))

    # Build a bracket if not provided
    if T_lo is None or T_hi is None:
        lo = T_ambient
        hi = max(T_ambient + 200.0, 200.0)  # generous upper bound
        # Expand upward until residual changes sign or limit reached
        r_lo = residual(lo)
        r_hi = residual(hi)
        grow = 0
        while r_lo * r_hi > 0 and grow < 10:
            hi += 100.0  # expand
            r_hi = residual(hi)
            grow += 1
        if r_lo * r_hi > 0:
            # No sign change detected; fall back to returning the sweep solution
            # to avoid raising in reasonable cases.
            # Using step=0.01 for decimal precision instead of integer steps
            T_sweep, _, _ = solve_tj_sweep(power_fn, theta_ja, T_ambient, T_hi=hi, T_lo=lo, step=0.01)
            return T_sweep
        T_lo, T_hi = lo, hi

    a, b = float(T_lo), float(T_hi)
    r_a = residual(a)
    r_b = residual(b)
    if r_a == 0.0:
        return a
    if r_b == 0.0:
        return b
    if r_a * r_b > 0:
        raise ValueError("Bisection requires residual to change sign on [T_lo, T_hi]. "
                         f"Residuals were {r_a} and {r_b}.")

    for _ in range(max_iter):
        m = 0.5*(a + b)
        r_m = residual(m)
        if abs(r_m) <= tol:
            return m
        if r_a * r_m < 0:
            b = m
            r_b = r_m
        else:
            a = m
            r_a = r_m
    # Return midpoint if we ran out of iterations
    return 0.5*(a + b)

# ---------------------
# Power-model helpers
# ---------------------

def piecewise_linear_power(
    T: float,
    T_ref: float,
    P_ref: float,
    slope_up: float,
    slope_down: float,
    scale: float = 1.0,
    overhead: float = 0.0
) -> float:
    """
    Replicates the sheet's piecewise-linear model:

        base = P_ref + slope_up*(T - T_ref)     if T > T_ref
             = P_ref - slope_down*(T_ref - T)   otherwise
        return base * scale + overhead
    """
    if T > T_ref:
        base = P_ref + slope_up*(T - T_ref)
    else:
        base = P_ref - slope_down*(T_ref - T)
    return base * scale + overhead

def make_total_power_fn(active_const: float, leakage_fn: Callable[[float], float]):
    """Convenience: P_total(T) = active_const + leakage_fn(T)."""
    def P(T: float) -> float:
        return float(active_const) + float(leakage_fn(T))
    return P
