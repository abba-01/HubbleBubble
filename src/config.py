"""
Configuration: All parameters, gates, and seeds for HubbleBubble validation
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Paths:
    """Directory paths"""
    cache = "assets"
    outputs = "outputs"
    results = "outputs/results"
    figs = "outputs/figures"
    tables = "outputs/tables"
    repro = "outputs/reproducibility"

@dataclass(frozen=True)
class Seeds:
    """REQUIRED fixed seed for reproducibility"""
    master = 172901

@dataclass(frozen=True)
class Epistemic:
    """Epistemic penalty parameters (Paper 3 baseline)"""
    # Baseline parameters
    delta_T = 1.36          # epistemic distance (observer tensor magnitude)
    f_systematic = 0.50     # fraction attributed to systematic

    # Accepted scan bounds for grid validation
    delta_T_min = 1.0
    delta_T_max = 1.8
    f_sys_min  = 0.3
    f_sys_max  = 0.7

@dataclass(frozen=True)
class Baseline:
    """Baseline measurements and corrections from Paper 3"""
    # Planck
    planck_mu = 67.27
    planck_sigma_raw = 0.60

    # SH0ES (original)
    shoes_mu_orig = 73.59
    shoes_sigma_orig = 1.56

    # Corrections derived in Paper 3 analysis
    corr_anchor = -1.92     # MW anchor bias
    corr_pl     = -0.22     # P-L relation bias

    # SH0ES (corrected)
    shoes_mu_corr = 71.45   # = 73.59 - 1.92 - 0.22
    shoes_sigma_corr = 1.89 # propagated from 210-config spread

@dataclass(frozen=True)
class Gates:
    """Acceptance gates (REQUIRED) - failing any gate = research finding, not publication"""
    # LOAO: all anchor-removal variants must be concordant
    loao_sigma_planck_max = 1.5

    # Grid-scan: median tension across parameter space
    grid_sigma_planck_median_min = 0.9
    grid_sigma_planck_median_max = 1.1

    # Synthetic injection: calibration test
    inject_abs_bias_max = 0.3           # km/s/Mpc
    inject_sigma_planck_max = 1.0

    # Bootstrap: correction uncertainty
    bootstrap_sigma_planck_p95_max = 1.2
