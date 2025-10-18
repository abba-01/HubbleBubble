"""
Mathematical Verification: Equations → Numbers

Recomputes epistemic penalty, effective sigmas, merged H₀, and z-scores
from first principles and compares to saved JSON outputs.
"""
import json
import math
import sys
from pathlib import Path

TOLERANCE = 1e-6  # Numerical tolerance for comparisons

def verify_epistemic_penalty_and_merge(scenario_name, mu_shoes_corr, sigma_shoes_raw):
    """
    Verify epistemic penalty calculation and inverse-variance merge.

    Parameters from config:
    - mu_planck = 67.27 km/s/Mpc
    - sigma_planck_raw = 0.60 km/s/Mpc
    - delta_T = 1.36 (observer tensor magnitude)
    - f_systematic = 0.50 (systematic fraction)
    """
    # Constants from config
    mu_planck = 67.27
    sigma_planck_raw = 0.60
    delta_T = 1.36
    f_systematic = 0.50

    # 1. Compute epistemic penalty
    delta_H = abs(mu_shoes_corr - mu_planck)
    u_epi = 0.5 * delta_H * delta_T * (1.0 - f_systematic)

    # 2. Effective uncertainties
    sigma_planck_eff = math.sqrt(sigma_planck_raw**2 + u_epi**2)
    sigma_shoes_eff = math.sqrt(sigma_shoes_raw**2 + u_epi**2)

    # 3. Inverse-variance weights
    w_planck = 1.0 / sigma_planck_eff**2
    w_shoes = 1.0 / sigma_shoes_eff**2

    # 4. Weighted mean and uncertainty
    mu_star = (w_planck * mu_planck + w_shoes * mu_shoes_corr) / (w_planck + w_shoes)
    sigma_star = 1.0 / math.sqrt(w_planck + w_shoes)

    # 5. Z-score to Planck (using sigma_star only, as in merge.py)
    z_planck = abs(mu_star - mu_planck) / sigma_star

    return {
        'delta_H': delta_H,
        'u_epi': u_epi,
        'sigma_planck_eff': sigma_planck_eff,
        'sigma_shoes_eff': sigma_shoes_eff,
        'mu_star': mu_star,
        'sigma_star': sigma_star,
        'z_planck': z_planck
    }

def compare_floats(computed, saved, name, tolerance=TOLERANCE):
    """Compare two floats and report"""
    diff = abs(computed - saved)
    match = diff < tolerance
    status = "✓" if match else "✗"
    print(f"  {status} {name}: computed={computed:.6f}, saved={saved:.6f}, diff={diff:.2e}")
    return match

def verify_loao_scenarios():
    """Verify all LOAO scenarios"""
    with open("outputs/results/loao.json") as f:
        loao = json.load(f)

    print("=" * 70)
    print("MATHEMATICAL VERIFICATION: LOAO Scenarios")
    print("=" * 70)

    all_passed = True

    for scenario_name, scenario_data in loao["scenarios"].items():
        print(f"\nScenario: {scenario_name}")
        print("-" * 70)

        # Extract saved values
        mu_shoes_corr = scenario_data["mu_shoes_corr"]
        sigma_shoes_raw = scenario_data["sigma_shoes_revised"]
        saved_mu_star = scenario_data["mu_star"]
        saved_sigma_star = scenario_data["sigma_star"]
        saved_z_planck = scenario_data["z_planck"]

        # Recompute from first principles
        computed = verify_epistemic_penalty_and_merge(
            scenario_name, mu_shoes_corr, sigma_shoes_raw
        )

        # Compare
        passed = True
        passed &= compare_floats(computed['mu_star'], saved_mu_star, "mu_star")
        passed &= compare_floats(computed['sigma_star'], saved_sigma_star, "sigma_star")
        passed &= compare_floats(computed['z_planck'], saved_z_planck, "z_planck")

        print(f"  Epistemic penalty: u_epi = {computed['u_epi']:.6f} km/s/Mpc")

        if not passed:
            all_passed = False
            print(f"  ✗ {scenario_name}: MISMATCH")
        else:
            print(f"  ✓ {scenario_name}: All values match")

    return all_passed

def main():
    """Run all mathematical verifications"""
    print("\n" + "=" * 70)
    print("MATHEMATICAL VERIFICATION SUITE")
    print("=" * 70)
    print()

    all_tests_passed = True

    # Test LOAO scenarios
    if not verify_loao_scenarios():
        all_tests_passed = False

    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✓ ALL MATHEMATICAL CHECKS PASSED")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME MATHEMATICAL CHECKS FAILED")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
