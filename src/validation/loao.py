"""
Leave-One-Anchor-Out (LOAO) Validation

Tests robustness of concordance result to anchor choice by:
1. Removing MW anchor (test if MW bias drives result)
2. Removing LMC anchor
3. Removing NGC4258 anchor
4. Using only external anchors (LMC + NGC4258)

Acceptance gate: z_planck ≤ 1.5σ for ALL variants
"""
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import norm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Gates, Baseline, Epistemic, Seeds
from merge import concordance
from data_io import load_shoes_grid

def estimate_correction_without_anchor(grid_df, exclude_anchor):
    """
    Re-estimate anchor correction excluding one anchor

    MODEL-CONSISTENT POLICY:
    - drop_MW: Δ_anchor = 0 (no MW-external split exists)
    - drop_LMC: Δ_anchor = -0.5*(μ_MW - μ_NGC4258)
    - drop_NGC4258: Δ_anchor = -0.5*(μ_MW - μ_LMC)
    - baseline: Δ_anchor = -0.5*(μ_MW - μ_ext), μ_ext = 0.5*(μ_LMC + μ_NGC4258)

    This prevents leakage: anchor corrections only use anchors present in scenario.

    Parameters
    ----------
    grid_df : pd.DataFrame
        Full 210-config systematic grid
    exclude_anchor : str or None
        Anchor to exclude ('M', 'L', 'N', or None for baseline)

    Returns
    -------
    corr_anchor : float
        Revised anchor correction (km/s/Mpc)
    mu_shoes : float
        Revised SH0ES mean (km/s/Mpc)
    sigma_shoes : float
        Revised SH0ES uncertainty (km/s/Mpc)
    """
    # Filter out excluded anchor
    if exclude_anchor:
        mask = ~grid_df['Anc'].str.contains(exclude_anchor, na=False)
        subset = grid_df[mask]
    else:
        subset = grid_df

    # Re-compute overall statistics
    mu_shoes = subset['H0'].mean()
    sigma_shoes = subset['H0'].std()

    # Compute individual anchor means
    anchor_vals = {}
    for anc in ['N', 'M', 'L']:
        anc_data = subset[subset['Anc'] == anc]['H0']
        if len(anc_data) > 0:
            anchor_vals[anc] = anc_data.mean()
        else:
            anchor_vals[anc] = np.nan

    # Scenario-specific anchor correction (model-consistent)
    if exclude_anchor == 'M':
        # drop_MW: No MW-external split exists → Δ_anchor = 0
        corr_anchor = 0.0
    elif exclude_anchor == 'L':
        # drop_LMC: Use MW vs NGC4258 only
        if np.isfinite(anchor_vals['M']) and np.isfinite(anchor_vals['N']):
            corr_anchor = -0.5 * (anchor_vals['M'] - anchor_vals['N'])
        else:
            corr_anchor = 0.0
    elif exclude_anchor == 'N':
        # drop_NGC4258: Use MW vs LMC only
        if np.isfinite(anchor_vals['M']) and np.isfinite(anchor_vals['L']):
            corr_anchor = -0.5 * (anchor_vals['M'] - anchor_vals['L'])
        else:
            corr_anchor = 0.0
    else:
        # Baseline: Use MW vs external mean (LMC + NGC4258)
        if np.isfinite(anchor_vals['M']) and np.isfinite(anchor_vals['L']) and np.isfinite(anchor_vals['N']):
            mu_ext = 0.5 * (anchor_vals['L'] + anchor_vals['N'])
            corr_anchor = -0.5 * (anchor_vals['M'] - mu_ext)
        else:
            corr_anchor = 0.0

    return corr_anchor, mu_shoes, sigma_shoes

def run_loao():
    """
    Run Leave-One-Anchor-Out validation

    Returns
    -------
    results : dict
        Results for each scenario
    passed : bool
        True if all gates passed
    """
    np.random.seed(Seeds.master)

    # Load 210-config grid
    try:
        grid_df = load_shoes_grid()
    except Exception as e:
        print(f"ERROR: Could not load SH0ES grid: {e}")
        print("Run 'python src/data_io.py --fetch' first")
        return {}, False

    scenarios = {
        "baseline": None,        # All anchors
        "drop_MW": "M",          # Remove Milky Way
        "drop_LMC": "L",         # Remove LMC
        "drop_NGC4258": "N",     # Remove NGC4258
        "external_only": "M",    # Same as drop_MW (only external)
    }

    results = {}
    z_planck_vals = []

    print("="*70)
    print("LEAVE-ONE-ANCHOR-OUT (LOAO) VALIDATION")
    print("="*70)
    print()

    for name, exclude in scenarios.items():
        if name == "external_only" and "drop_MW" in results:
            # Skip duplicate (same as drop_MW)
            results[name] = results["drop_MW"]
            z_planck_vals.append(results["drop_MW"]["z_planck"])
            continue

        # Re-estimate corrections without this anchor
        corr_anchor, mu_shoes_revised, sigma_shoes_revised = \
            estimate_correction_without_anchor(grid_df, exclude)

        # Apply correction to get corrected mean
        mu_shoes_corr = mu_shoes_revised + corr_anchor + Baseline.corr_pl

        # Run concordance with revised SH0ES
        res = concordance(
            Epistemic.delta_T,
            Epistemic.f_systematic,
            mu_shoes=mu_shoes_corr,
            sigma_shoes=sigma_shoes_revised
        )

        results[name] = {
            "excluded_anchor": exclude if exclude else "none",
            "corr_anchor_revised": float(corr_anchor),
            "mu_shoes_revised": float(mu_shoes_revised),
            "mu_shoes_corr": float(mu_shoes_corr),
            "sigma_shoes_revised": float(sigma_shoes_revised),
            "mu_star": res["mu_star"],
            "sigma_star": res["sigma_star"],
            "z_planck": res["z_planck"],
            "z_shoes_corr": res["z_shoes_corr"]
        }

        z_planck_vals.append(res["z_planck"])

        print(f"Scenario: {name:20s} (exclude {exclude if exclude else 'none'})")
        print(f"  Revised anchor corr: {corr_anchor:+.2f} km/s/Mpc")
        print(f"  SH0ES corrected:     {mu_shoes_corr:.2f} ± {sigma_shoes_revised:.2f}")
        print(f"  Concordance H₀:      {res['mu_star']:.2f} ± {res['sigma_star']:.2f}")
        print(f"  Tension to Planck:   {res['z_planck']:.2f}σ", end="")

        if res['z_planck'] <= Gates.loao_sigma_planck_max:
            print(" ✓ PASS")
        else:
            print(f" ✗ FAIL (> {Gates.loao_sigma_planck_max}σ)")
        print()

    # Gate A: Engineering gate (ALL must be ≤ 1.5σ)
    # Use unrounded values for decision, epsilon tolerance for float precision
    max_z = max(z_planck_vals)
    EPSILON = 1e-9  # Tolerance for floating-point comparison
    gate_a_passed = (max_z <= Gates.loao_sigma_planck_max + EPSILON)

    # Gate B: Šidák family-wise correction for multiple comparisons
    # For K=4 scenarios with one-sided α=0.05:
    # Per-scenario threshold = Φ⁻¹(1 - (1-(1-α)^(1/K)))
    K = len(scenarios)
    alpha = 0.05
    alpha_prime = 1.0 - (1.0 - alpha)**(1.0 / K)
    sidak_thresh = float(norm.isf(alpha_prime))  # ≈ 2.24 for K=4
    gate_b_passed = (max_z <= sidak_thresh + EPSILON)

    print("="*70)
    print("GATES")
    print("="*70)
    print(f"Maximum z_Planck: {max_z:.4f}σ")
    print()
    print(f"Gate A (Engineering): ≤ {Gates.loao_sigma_planck_max}σ")
    if gate_a_passed:
        print("  ✓ PASS: All scenarios concordant with Planck")
    else:
        print(f"  ✗ MARGINAL: Max tension {max_z:.4f}σ exceeds {Gates.loao_sigma_planck_max}σ")
    print()
    print(f"Gate B (Šidák family-wise): ≤ {sidak_thresh:.4f}σ (K={K}, α={alpha})")
    if gate_b_passed:
        print("  ✓ PASS: Family-wise error control satisfied")
    else:
        print(f"  ✗ FAIL: Max tension {max_z:.4f}σ exceeds Šidák threshold")
    print("="*70)

    # Overall pass requires both gates
    overall_passed = gate_a_passed and gate_b_passed

    return {
        "scenarios": results,
        "max_z_planck": float(max_z),
        "gate_a_engineering": {
            "threshold": Gates.loao_sigma_planck_max,
            "passed": bool(gate_a_passed)
        },
        "gate_b_sidak": {
            "alpha": alpha,
            "K": K,
            "threshold": float(sidak_thresh),
            "passed": bool(gate_b_passed)
        },
        "overall_passed": bool(overall_passed)
    }, overall_passed

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LOAO validation")
    parser.add_argument("--out", type=str, required=True, help="Output JSON file")
    args = parser.parse_args()

    results, passed = run_loao()

    # Save results
    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {outpath}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)
