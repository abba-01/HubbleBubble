"""
Bootstrap Validation (10,000 iterations)

Tests uncertainty in correction estimation by:
1. Resampling 210-config grid with replacement
2. Re-estimating anchor and P-L corrections from resample
3. Re-running concordance merge
4. Building distribution of z_planck

Acceptance gate: z_planck 95th percentile ≤ 1.2σ
"""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Gates, Baseline, Epistemic, Seeds
from merge import concordance
from data_io import load_shoes_grid

def estimate_corrections_from_sample(sample_df):
    """
    Estimate anchor and P-L corrections from bootstrap sample

    Parameters
    ----------
    sample_df : pd.DataFrame
        Bootstrap resample of 210-config grid

    Returns
    -------
    corr_anchor : float
        Anchor correction (km/s/Mpc)
    corr_pl : float
        P-L correction (km/s/Mpc)
    mu_shoes : float
        SH0ES mean (km/s/Mpc)
    sigma_shoes : float
        SH0ES uncertainty (km/s/Mpc)
    """
    # Overall statistics
    mu_shoes = sample_df['H0'].mean()
    sigma_shoes = sample_df['H0'].std()

    # Anchor correction: spread among single anchors
    single_anchors = ['N', 'M', 'L']
    anchor_means = []
    for anc in single_anchors:
        anc_data = sample_df[sample_df['Anc'] == anc]['H0']
        if len(anc_data) > 0:
            anchor_means.append(anc_data.mean())

    if len(anchor_means) >= 2:
        anchor_spread = max(anchor_means) - min(anchor_means)
        corr_anchor = -anchor_spread / 2.0  # Conservative: midpoint
    else:
        corr_anchor = Baseline.corr_anchor  # Fallback

    # P-L correction: variation across P-L configs
    pl_groups = sample_df.groupby('PL')['H0'].mean()
    if len(pl_groups) >= 2:
        pl_var = pl_groups.std()
        corr_pl = -pl_var * 0.5  # Assume 50% is bias
    else:
        corr_pl = Baseline.corr_pl  # Fallback

    return corr_anchor, corr_pl, mu_shoes, sigma_shoes

def run_bootstrap(n_iterations=10000):
    """
    Run bootstrap validation

    Parameters
    ----------
    n_iterations : int
        Number of bootstrap iterations (default: 10000)

    Returns
    -------
    results : dict
        Bootstrap distribution and statistics
    passed : bool
        True if gate passed
    """
    np.random.seed(Seeds.master)

    # Load 210-config grid
    try:
        grid_df = load_shoes_grid()
    except Exception as e:
        print(f"ERROR: Could not load SH0ES grid: {e}")
        print("Run 'python src/data_io.py --fetch' first")
        return {}, False

    n_configs = len(grid_df)

    print("="*70)
    print(f"BOOTSTRAP VALIDATION ({n_iterations} iterations)")
    print("="*70)
    print(f"\nResampling {n_configs} configs with replacement")
    print("Re-estimating corrections and concordance for each bootstrap sample")
    print()

    z_planck_vals = []
    mu_star_vals = []
    corr_anchor_vals = []
    corr_pl_vals = []

    for i in range(n_iterations):
        # Resample with replacement
        sample_indices = np.random.choice(n_configs, size=n_configs, replace=True)
        sample_df = grid_df.iloc[sample_indices]

        # Re-estimate corrections
        corr_anchor, corr_pl, mu_shoes, sigma_shoes = estimate_corrections_from_sample(sample_df)

        # Apply corrections
        mu_shoes_corr = mu_shoes + corr_anchor + corr_pl

        # Run concordance
        res = concordance(
            Epistemic.delta_T,
            Epistemic.f_systematic,
            mu_shoes=mu_shoes_corr,
            sigma_shoes=sigma_shoes
        )

        z_planck_vals.append(res["z_planck"])
        mu_star_vals.append(res["mu_star"])
        corr_anchor_vals.append(corr_anchor)
        corr_pl_vals.append(corr_pl)

        # Progress indicator
        if (i + 1) % 2000 == 0:
            print(f"  Progress: {i+1}/{n_iterations} iterations...")

    # Convert to arrays
    z_planck_vals = np.array(z_planck_vals)
    mu_star_vals = np.array(mu_star_vals)
    corr_anchor_vals = np.array(corr_anchor_vals)
    corr_pl_vals = np.array(corr_pl_vals)

    # Statistics
    z_median = float(np.median(z_planck_vals))
    z_mean = float(np.mean(z_planck_vals))
    z_std = float(np.std(z_planck_vals))
    z_p95 = float(np.percentile(z_planck_vals, 95))

    mu_median = float(np.median(mu_star_vals))
    mu_mean = float(np.mean(mu_star_vals))
    mu_std = float(np.std(mu_star_vals))

    # Gate: 95th percentile ≤ 1.2σ
    passed = (z_p95 <= Gates.bootstrap_sigma_planck_p95_max)

    print()
    print("="*70)
    print("BOOTSTRAP STATISTICS")
    print("="*70)
    print(f"\nConcordance H₀:")
    print(f"  Median: {mu_median:.2f} km/s/Mpc")
    print(f"  Mean:   {mu_mean:.2f} ± {mu_std:.2f} km/s/Mpc")
    print(f"\nTension to Planck (z_planck):")
    print(f"  Median: {z_median:.2f}σ")
    print(f"  Mean:   {z_mean:.2f}σ ± {z_std:.2f}σ")
    print(f"  95th percentile: {z_p95:.2f}σ")
    print(f"\nCorrections:")
    print(f"  Anchor: {np.mean(corr_anchor_vals):.2f} ± {np.std(corr_anchor_vals):.2f} km/s/Mpc")
    print(f"  P-L:    {np.mean(corr_pl_vals):.2f} ± {np.std(corr_pl_vals):.2f} km/s/Mpc")
    print()
    print(f"BOOTSTRAP GATE: z_planck p95 ≤ {Gates.bootstrap_sigma_planck_p95_max}σ")
    if passed:
        print(f"✓ PASS: p95 = {z_p95:.2f}σ within gate")
    else:
        print(f"✗ FAIL: p95 = {z_p95:.2f}σ exceeds gate")
    print("="*70)

    return {
        "n_iterations": n_iterations,
        "statistics": {
            "h0": {
                "median": mu_median,
                "mean": mu_mean,
                "std": mu_std
            },
            "z_planck": {
                "median": z_median,
                "mean": z_mean,
                "std": z_std,
                "p95": z_p95
            },
            "corrections": {
                "anchor_mean": float(np.mean(corr_anchor_vals)),
                "anchor_std": float(np.std(corr_anchor_vals)),
                "pl_mean": float(np.mean(corr_pl_vals)),
                "pl_std": float(np.std(corr_pl_vals))
            }
        },
        "distributions": {
            "z_planck": z_planck_vals.tolist(),
            "h0": mu_star_vals.tolist(),
            "corr_anchor": corr_anchor_vals.tolist(),
            "corr_pl": corr_pl_vals.tolist()
        },
        "gate": Gates.bootstrap_sigma_planck_p95_max,
        "passed": passed
    }, passed

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bootstrap validation")
    parser.add_argument("--iters", type=int, default=10000, help="Number of bootstrap iterations")
    parser.add_argument("--out", type=str, required=True, help="Output JSON file")
    args = parser.parse_args()

    results, passed = run_bootstrap(args.iters)

    # Save results
    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {outpath}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)
