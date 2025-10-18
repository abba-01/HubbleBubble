"""
Leave-One-Anchor-Out (LOAO) Validation with Scenario-Local Estimators

Tests robustness of concordance result to anchor choice using:
- Scenario-local Δ_anchor, Δ_PL, and σ_SH0ES,corr
- Engineering gate (≤ 1.5σ)
- Šidák family-wise gate (K=4, α=0.05, ≈ 2.24σ)

Principled completion of model-consistent policy.
"""
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import norm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Gates, Baseline, Epistemic, Seeds, Paths
from merge import concordance
from data_io import load_shoes_grid

# Anchor mapping
ANCHOR_MAP = {
    'baseline': {'keep': ['M', 'L', 'N'], 'filter': ['All', 'NML']},
    'drop_MW':  {'keep': ['L', 'N'], 'filter': ['NL', 'N', 'L']},
    'drop_LMC': {'keep': ['M', 'N'], 'filter': ['NM', 'N', 'M']},
    'drop_NGC4258': {'keep': ['M', 'L'], 'filter': ['M+L', 'M', 'L']},
}

EPSILON = 1e-12

def anchor_demean(df, anchor_col='Anc'):
    """
    Anchor-demean: subtract anchor-specific mean from each row.

    For multi-anchor configs (e.g., 'All'), use the mean of all data
    with that anchor combination.
    """
    df = df.copy()
    df['H0_dm'] = df['H0'] - df.groupby(anchor_col)['H0'].transform('mean')
    return df

def compute_pl_correction(df_dm, pl_col='PL'):
    """
    Compute Δ_PL = -1/2 × (span of PL variants after anchor-demean).

    If PL column exists, span = max - min of group means.
    Otherwise, use (q84 - q16) as robust span estimator.
    """
    if pl_col in df_dm.columns and df_dm[pl_col].nunique() > 1:
        # Group by PL variant and compute span
        means = df_dm.groupby(pl_col)['H0_dm'].mean()
        span = float(means.max() - means.min())
    else:
        # Robust span from quantiles
        q84 = float(df_dm['H0_dm'].quantile(0.84))
        q16 = float(df_dm['H0_dm'].quantile(0.16))
        span = q84 - q16

    return -0.5 * span

def compute_sigma_corrected(df_dm):
    """
    σ_SH0ES,corr = std of anchor-demeaned H0 values.

    This captures the scatter after removing anchor offsets.
    """
    sigma = float(df_dm['H0_dm'].std(ddof=1))
    if not np.isfinite(sigma) or sigma <= 0.0:
        # Fallback to raw std if demeaned is invalid
        sigma = float(df_dm['H0'].std(ddof=1))
    return sigma

def compute_anchor_correction(df, keep_anchors):
    """
    Scenario-local Δ_anchor using only anchors present in scenario.

    Model-consistent policy:
    - drop_MW (L,N only): Δ_anchor = 0 (no MW-external split)
    - drop_LMC (M,N): Δ_anchor = -0.5×(μ_M - μ_N)
    - drop_NGC4258 (M,L): Δ_anchor = -0.5×(μ_M - μ_L)
    - baseline (M,L,N): Δ_anchor = -0.5×(μ_M - μ_ext), μ_ext = 0.5×(μ_L + μ_N)
    """
    # Get means for individual anchors (single-anchor configs)
    anchor_means = {}
    for anc in ['M', 'L', 'N']:
        subset = df[df['Anc'] == anc]
        if len(subset) > 0:
            anchor_means[anc] = float(subset['H0'].mean())
        else:
            anchor_means[anc] = np.nan

    # Scenario-specific correction
    if 'M' not in keep_anchors:
        # drop_MW: no MW-external split exists
        return 0.0
    elif 'L' not in keep_anchors:
        # drop_LMC: MW vs NGC4258 only
        if np.isfinite(anchor_means['M']) and np.isfinite(anchor_means['N']):
            return -0.5 * (anchor_means['M'] - anchor_means['N'])
        return 0.0
    elif 'N' not in keep_anchors:
        # drop_NGC4258: MW vs LMC only
        if np.isfinite(anchor_means['M']) and np.isfinite(anchor_means['L']):
            return -0.5 * (anchor_means['M'] - anchor_means['L'])
        return 0.0
    else:
        # baseline: MW vs external mean
        if all(np.isfinite(anchor_means[a]) for a in ['M', 'L', 'N']):
            mu_ext = 0.5 * (anchor_means['L'] + anchor_means['N'])
            return -0.5 * (anchor_means['M'] - mu_ext)
        return 0.0

def run_scenario(grid_df, scenario_name, scenario_config):
    """
    Run LOAO for a single scenario with scenario-local estimators.

    Returns
    -------
    dict with keys: excluded_anchor, corr_anchor, corr_pl, sigma_shoes_corr,
                    mu_shoes_uncorr, mu_shoes_corr, mu_star, sigma_star,
                    z_planck, z_shoes_corr
    """
    keep_anchors = scenario_config['keep']
    anchor_filters = scenario_config['filter']

    # Filter to configs with only the kept anchors
    df_sc = grid_df[grid_df['Anc'].isin(anchor_filters)].copy()

    if len(df_sc) == 0:
        return None

    # 1. Anchor correction (scenario-local)
    corr_anchor = compute_anchor_correction(df_sc, keep_anchors)

    # 2. Anchor-demean using anchors in this scenario
    df_dm = anchor_demean(df_sc, anchor_col='Anc')

    # 3. P-L correction (scenario-local, after anchor-demean)
    corr_pl = compute_pl_correction(df_dm, pl_col='PL')

    # 4. Corrected scatter (scenario-local)
    sigma_shoes_corr = compute_sigma_corrected(df_dm)

    # 5. SH0ES means (uncorrected and corrected)
    mu_shoes_uncorr = float(df_sc['H0'].mean())
    mu_shoes_corr = mu_shoes_uncorr + corr_anchor + corr_pl

    # 6. Concordance calculation with scenario-local values
    result = concordance(
        delta_T=Epistemic.delta_T,
        f_systematic=Epistemic.f_systematic,
        mu_planck=Baseline.planck_mu,
        sigma_planck=Baseline.planck_sigma_raw,
        mu_shoes=mu_shoes_corr,
        sigma_shoes=sigma_shoes_corr
    )

    # 7. Determine excluded anchor for reporting
    all_anchors = set(['M', 'L', 'N'])
    excluded = all_anchors - set(keep_anchors)
    if len(excluded) == 0:
        excluded_name = "none"
    else:
        anc_names = {'M': 'MW', 'L': 'LMC', 'N': 'NGC4258'}
        excluded_name = anc_names[list(excluded)[0]]

    return {
        'excluded_anchor': excluded_name,
        'corr_anchor': float(corr_anchor),
        'corr_pl': float(corr_pl),
        'sigma_shoes_corr': float(sigma_shoes_corr),
        'mu_shoes_uncorr': float(mu_shoes_uncorr),
        'mu_shoes_corr': float(mu_shoes_corr),
        'mu_star': float(result['mu_star']),
        'sigma_star': float(result['sigma_star']),
        'z_planck': float(result['z_planck']),
        'z_shoes_corr': float(result['z_shoes_corr'])
    }

def run_loao(alpha=0.05):
    """
    Run Leave-One-Anchor-Out validation with scenario-local estimators.

    Parameters
    ----------
    alpha : float
        Family-wise error rate for Šidák gate (default: 0.05)

    Returns
    -------
    results : dict
        Full results including scenarios and gates
    passed : bool
        True if both gates passed
    """
    np.random.seed(Seeds.master)

    # Load 210-config grid
    try:
        grid_df = load_shoes_grid()
    except Exception as e:
        print(f"ERROR: Could not load SH0ES grid: {e}")
        print("Run 'python src/data_io.py --fetch' first")
        return {}, False

    print("=" * 70)
    print("LEAVE-ONE-ANCHOR-OUT (LOAO) VALIDATION")
    print("Scenario-local estimators (Δ_anchor, Δ_PL, σ)")
    print("=" * 70)
    print()

    # Run all scenarios
    scenarios = {}
    z_vals = []

    for name, config in ANCHOR_MAP.items():
        result = run_scenario(grid_df, name, config)
        if result is None:
            continue

        scenarios[name] = result
        z_vals.append(result['z_planck'])

        # Print scenario results
        status = "✓ PASS" if result['z_planck'] <= 1.5 else "✗ MARGINAL"
        print(f"Scenario: {name:20s} (exclude {result['excluded_anchor']})")
        print(f"  Δ_anchor:     {result['corr_anchor']:+.2f} km/s/Mpc")
        print(f"  Δ_PL:         {result['corr_pl']:+.2f} km/s/Mpc")
        print(f"  σ_SH0ES,corr: {result['sigma_shoes_corr']:.2f} km/s/Mpc")
        print(f"  SH0ES uncorr: {result['mu_shoes_uncorr']:.2f} km/s/Mpc")
        print(f"  SH0ES corr:   {result['mu_shoes_corr']:.2f} km/s/Mpc")
        print(f"  H₀ conc:      {result['mu_star']:.2f} ± {result['sigma_star']:.2f}")
        print(f"  z_Planck:     {result['z_planck']:.3f}σ {status}")
        print()

    # Gate A: Engineering gate (≤ 1.5σ)
    z_max = float(np.max(z_vals))
    gate_a_passed = (z_max <= 1.5 + EPSILON)

    # Gate B: Šidák family-wise correction
    K = len(scenarios)
    alpha_prime = 1.0 - (1.0 - alpha)**(1.0 / K)
    sidak_thresh = float(norm.isf(alpha_prime))
    gate_b_passed = (z_max <= sidak_thresh + EPSILON)

    # Print gate results
    print("=" * 70)
    print("GATES")
    print("=" * 70)
    print(f"Maximum z_Planck: {z_max:.4f}σ")
    print()
    print(f"Gate A (Engineering): ≤ 1.5σ")
    print(f"  Result: {'✓ PASS' if gate_a_passed else '✗ MARGINAL'}")
    print()
    print(f"Gate B (Šidák family-wise): ≤ {sidak_thresh:.4f}σ (α={alpha}, K={K})")
    print(f"  Result: {'✓ PASS' if gate_b_passed else '✗ FAIL'}")
    print("=" * 70)

    # Overall pass if both gates pass
    overall_passed = gate_a_passed and gate_b_passed

    return {
        'scenarios': scenarios,
        'z_planck_max': z_max,
        'gate_a_engineering': {
            'threshold': 1.5,
            'passed': bool(gate_a_passed)
        },
        'gate_b_sidak': {
            'alpha': alpha,
            'K': K,
            'threshold': float(sidak_thresh),
            'passed': bool(gate_b_passed)
        },
        'overall_passed': bool(overall_passed)
    }, overall_passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LOAO validation with scenario-local estimators')
    parser.add_argument('--out', type=str, required=True, help='Output JSON file')
    parser.add_argument('--alpha', type=float, default=0.05, help='Family-wise alpha for Šidák gate')
    args = parser.parse_args()

    results, passed = run_loao(alpha=args.alpha)

    # Save results
    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {outpath}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)
