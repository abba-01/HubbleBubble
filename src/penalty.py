"""
Epistemic Penalty Calculation using N/U Algebra
"""
import numpy as np

def compute_epistemic_penalty(disagreement, delta_T, f_systematic):
    """
    Compute epistemic penalty for methodological differences

    Formula: u_epistemic = (disagreement/2) × Δ_T × (1 - f_systematic)

    Parameters
    ----------
    disagreement : float
        Absolute difference between measurements (km/s/Mpc)
    delta_T : float
        Epistemic distance (observer tensor magnitude difference)
    f_systematic : float
        Fraction of disagreement attributed to systematic (0-1)

    Returns
    -------
    u_epistemic : float
        Epistemic penalty to add in quadrature to uncertainties (km/s/Mpc)
    """
    u_epistemic = (disagreement / 2.0) * delta_T * (1.0 - f_systematic)
    return u_epistemic

def effective_uncertainties(sigma_planck, sigma_shoes, u_epistemic):
    """
    Compute effective uncertainties including epistemic penalty

    Parameters
    ----------
    sigma_planck : float
        Raw Planck uncertainty (km/s/Mpc)
    sigma_shoes : float
        Raw SH0ES uncertainty (km/s/Mpc)
    u_epistemic : float
        Epistemic penalty (km/s/Mpc)

    Returns
    -------
    sigma_eff_planck : float
        Effective Planck uncertainty (km/s/Mpc)
    sigma_eff_shoes : float
        Effective SH0ES uncertainty (km/s/Mpc)
    """
    sigma_eff_planck = np.sqrt(sigma_planck**2 + u_epistemic**2)
    sigma_eff_shoes = np.sqrt(sigma_shoes**2 + u_epistemic**2)
    return sigma_eff_planck, sigma_eff_shoes
