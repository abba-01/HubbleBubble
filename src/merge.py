"""
Concordance H₀ Calculation with Epistemic Penalty
"""
import numpy as np
from config import Baseline
from penalty import compute_epistemic_penalty, effective_uncertainties

def concordance(delta_T, f_systematic,
                mu_planck=None, sigma_planck=None,
                mu_shoes=None, sigma_shoes=None):
    """
    Compute concordance H₀ with epistemic penalty

    Parameters
    ----------
    delta_T : float
        Epistemic distance (observer tensor magnitude)
    f_systematic : float
        Fraction attributed to systematic (0-1)
    mu_planck : float, optional
        Planck mean (default: from config)
    sigma_planck : float, optional
        Planck raw uncertainty (default: from config)
    mu_shoes : float, optional
        SH0ES corrected mean (default: from config)
    sigma_shoes : float, optional
        SH0ES corrected uncertainty (default: from config)

    Returns
    -------
    result : dict
        Dictionary containing:
        - mu_star: concordance H₀ (km/s/Mpc)
        - sigma_star: concordance uncertainty (km/s/Mpc)
        - u_epistemic: epistemic penalty (km/s/Mpc)
        - sigma_eff_planck: effective Planck uncertainty (km/s/Mpc)
        - sigma_eff_shoes: effective SH0ES uncertainty (km/s/Mpc)
        - w_planck: Planck weight
        - w_shoes: SH0ES weight
        - z_planck: tension to Planck (sigma)
        - z_shoes_orig: tension to SH0ES original (sigma)
        - z_shoes_corr: tension to SH0ES corrected (sigma)
    """
    # Use defaults from config if not provided
    if mu_planck is None:
        mu_planck = Baseline.planck_mu
    if sigma_planck is None:
        sigma_planck = Baseline.planck_sigma_raw
    if mu_shoes is None:
        mu_shoes = Baseline.shoes_mu_corr
    if sigma_shoes is None:
        sigma_shoes = Baseline.shoes_sigma_corr

    # Disagreement
    disagreement = abs(mu_shoes - mu_planck)

    # Epistemic penalty
    u_epistemic = compute_epistemic_penalty(disagreement, delta_T, f_systematic)

    # Effective uncertainties
    sigma_eff_planck, sigma_eff_shoes = effective_uncertainties(
        sigma_planck, sigma_shoes, u_epistemic
    )

    # Inverse-variance weights
    w_planck = 1.0 / (sigma_eff_planck**2)
    w_shoes = 1.0 / (sigma_eff_shoes**2)

    # Weighted mean
    mu_star = (w_planck * mu_planck + w_shoes * mu_shoes) / (w_planck + w_shoes)

    # Combined uncertainty
    sigma_star = 1.0 / np.sqrt(w_planck + w_shoes)

    # Tensions
    z_planck = abs(mu_star - mu_planck) / sigma_star
    z_shoes_orig = abs(mu_star - Baseline.shoes_mu_orig) / sigma_star
    z_shoes_corr = abs(mu_star - mu_shoes) / sigma_star

    return {
        "mu_star": float(mu_star),
        "sigma_star": float(sigma_star),
        "u_epistemic": float(u_epistemic),
        "sigma_eff_planck": float(sigma_eff_planck),
        "sigma_eff_shoes": float(sigma_eff_shoes),
        "w_planck": float(w_planck),
        "w_shoes": float(w_shoes),
        "w_planck_frac": float(w_planck / (w_planck + w_shoes)),
        "w_shoes_frac": float(w_shoes / (w_planck + w_shoes)),
        "z_planck": float(z_planck),
        "z_shoes_orig": float(z_shoes_orig),
        "z_shoes_corr": float(z_shoes_corr),
        "disagreement": float(disagreement),
        "inputs": {
            "mu_planck": float(mu_planck),
            "sigma_planck": float(sigma_planck),
            "mu_shoes": float(mu_shoes),
            "sigma_shoes": float(sigma_shoes),
            "delta_T": float(delta_T),
            "f_systematic": float(f_systematic)
        }
    }

if __name__ == "__main__":
    # Test with baseline parameters
    from config import Epistemic
    result = concordance(Epistemic.delta_T, Epistemic.f_systematic)

    print("="*60)
    print("CONCORDANCE H₀ (BASELINE)")
    print("="*60)
    print(f"H₀ = {result['mu_star']:.2f} ± {result['sigma_star']:.2f} km/s/Mpc")
    print(f"\nEpistemic penalty: {result['u_epistemic']:.2f} km/s/Mpc")
    print(f"\nEffective uncertainties:")
    print(f"  Planck: {Baseline.planck_sigma_raw:.2f} → {result['sigma_eff_planck']:.2f}")
    print(f"  SH0ES:  {Baseline.shoes_sigma_corr:.2f} → {result['sigma_eff_shoes']:.2f}")
    print(f"\nWeights:")
    print(f"  Planck: {result['w_planck_frac']*100:.1f}%")
    print(f"  SH0ES:  {result['w_shoes_frac']*100:.1f}%")
    print(f"\nTensions:")
    print(f"  To Planck: {result['z_planck']:.2f}σ")
    print(f"  To SH0ES (corrected): {result['z_shoes_corr']:.2f}σ")
    print("="*60)
