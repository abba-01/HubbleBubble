#!/usr/bin/env python3
"""
RENT Phase II: Re-compute Systematic Corrections

Independently recomputes anchor and P-L corrections from raw SH0ES CSV data.
Compares to the documented values in systematic_corrections_applied.json.

This is ZERO-TRUST: we start from the raw CSV and rebuild everything.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0
Uses acceptability tree and discovery tree for graceful failure handling.

Usage:
    python rent/phase2_reexecution/recompute_corrections.py [--mode MODE]
"""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree
from lib.discovery_tree import DiscoveryTree

# Tolerance for numerical comparisons
TOLERANCE_CORRECTION = 0.01  # km/s/Mpc
TOLERANCE_MEAN = 0.1  # km/s/Mpc

def load_shoes_grid(discovery_tree, accept_tree):
    """Load raw SH0ES systematic grid using discovery tree"""
    grid_file = Path('assets/vizier/riess_2016_systematic_grid_210.csv')

    if not grid_file.exists():
        print(f"⚠ {grid_file} not found locally")
        print("Attempting to fetch using discovery tree...")

        # Use discovery tree to fetch
        success, path = discovery_tree.discover('shoes_systematic_grid')

        if not success:
            action = accept_tree.handle('data_missing', {
                'file': str(grid_file),
                'dataset': 'shoes_systematic_grid',
                'phase': 'Phase II'
            })

            if action == 'abort':
                return None
            elif action == 'skip':
                print("⚠ Skipping Phase II due to missing data")
                return None
            # If fetch action, discovery tree already attempted

    try:
        df = pd.read_csv(grid_file)
        print(f"✓ Loaded {len(df)} configurations from SH0ES grid")
        return df
    except Exception as e:
        print(f"✗ ERROR loading grid: {e}")
        action = accept_tree.handle('logic_error', {
            'error': str(e),
            'file': str(grid_file)
        })
        return None if action == 'abort' else None

def compute_anchor_correction_from_scratch(df):
    """
    Recompute anchor correction from raw data.

    Formula: Δ_anchor = -0.5 × (μ_MW - μ_external)
    where μ_external = 0.5 × (μ_LMC + μ_NGC4258)

    Single-anchor configs: Anc = 'M', 'L', 'N'
    """
    # Extract single-anchor configurations
    anchor_means = {}
    for anc_code, anc_name in [('M', 'MW'), ('L', 'LMC'), ('N', 'NGC4258')]:
        subset = df[df['Anc'] == anc_code]
        if len(subset) == 0:
            print(f"⚠ WARNING: No data for anchor {anc_name}")
            continue

        mean_h0 = subset['H0'].mean()
        std_h0 = subset['H0'].std()
        count = len(subset)

        anchor_means[anc_name] = {
            'mean': mean_h0,
            'std': std_h0,
            'count': count
        }

        print(f"  {anc_name:12s}: {mean_h0:6.2f} ± {std_h0:4.2f} km/s/Mpc  (n={count})")

    # Compute anchor correction
    if all(k in anchor_means for k in ['MW', 'LMC', 'NGC4258']):
        mu_mw = anchor_means['MW']['mean']
        mu_lmc = anchor_means['LMC']['mean']
        mu_ngc = anchor_means['NGC4258']['mean']

        mu_external = 0.5 * (mu_lmc + mu_ngc)
        anchor_correction = -0.5 * (mu_mw - mu_external)

        print()
        print(f"Anchor split:")
        print(f"  MW:       {mu_mw:.2f} km/s/Mpc")
        print(f"  External: {mu_external:.2f} km/s/Mpc")
        print(f"  Split:    {mu_mw - mu_external:.2f} km/s/Mpc")
        print(f"  Δ_anchor: {anchor_correction:.2f} km/s/Mpc")

        return anchor_correction, anchor_means
    else:
        print("✗ CRITICAL: Cannot compute anchor correction (missing anchors)")
        return None, anchor_means

def compute_pl_correction_from_scratch(df):
    """
    Recompute P-L correction from raw data.

    Formula: Δ_PL = -0.5 × span(H0_demeaned, grouped by PL)

    Steps:
    1. Demean by anchor
    2. Group by P-L variant (PL column)
    3. Compute span = max - min of group means
    4. Δ_PL = -0.5 × span
    """
    # Anchor-demean
    df = df.copy()
    df['H0_dm'] = df['H0'] - df.groupby('Anc')['H0'].transform('mean')

    # Check if PL column exists and has variants
    if 'PL' not in df.columns:
        print("⚠ WARNING: No PL column, using quantile method")
        # Fallback: use quantiles
        q84 = df['H0_dm'].quantile(0.84)
        q16 = df['H0_dm'].quantile(0.16)
        span = q84 - q16
        pl_correction = -0.5 * span

        print(f"  P-L span (q84-q16): {span:.2f} km/s/Mpc")
        print(f"  Δ_PL: {pl_correction:.2f} km/s/Mpc")

        return pl_correction

    # Group by PL variant
    pl_groups = df.groupby('PL')['H0_dm'].mean()

    if len(pl_groups) < 2:
        print("⚠ WARNING: Only one P-L variant, using quantile method")
        q84 = df['H0_dm'].quantile(0.84)
        q16 = df['H0_dm'].quantile(0.16)
        span = q84 - q16
        pl_correction = -0.5 * span
    else:
        span = pl_groups.max() - pl_groups.min()
        pl_correction = -0.5 * span

        print(f"  P-L variants: {len(pl_groups)}")
        print(f"  P-L span: {span:.2f} km/s/Mpc")
        print(f"  Δ_PL: {pl_correction:.2f} km/s/Mpc")

    return pl_correction

def load_documented_corrections():
    """Load the documented correction values"""
    corrections_file = Path('assets/external/systematic_corrections_applied.json')
    if corrections_file.exists():
        with open(corrections_file) as f:
            return json.load(f)
    return None

def main():
    """Main re-computation routine"""
    parser = argparse.ArgumentParser(description='RENT Phase II: Recompute Corrections')
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        default=True, help='Disable interactive prompts')
    args = parser.parse_args()

    # Initialize SSOT modules
    accept_tree = AcceptabilityTree(mode=args.mode, interactive=args.interactive)
    discovery_tree = DiscoveryTree()

    print("=" * 70)
    print("RENT PHASE II: RE-COMPUTE SYSTEMATIC CORRECTIONS")
    print(f"Mode: {args.mode}")
    print("=" * 70)
    print()

    print("Step 1: Load raw SH0ES data")
    print("-" * 70)
    df = load_shoes_grid(discovery_tree, accept_tree)
    if df is None:
        accept_tree.save_log()
        discovery_tree.save_log()
        return 1 if args.mode == 'strict' else 0
    print()

    print("Step 2: Recompute anchor correction from scratch")
    print("-" * 70)
    anchor_corr_recomputed, anchor_means = compute_anchor_correction_from_scratch(df)
    if anchor_corr_recomputed is None:
        return 1
    print()

    print("Step 3: Recompute P-L correction from scratch")
    print("-" * 70)
    pl_corr_recomputed = compute_pl_correction_from_scratch(df)
    print()

    print("Step 4: Compare to documented values")
    print("-" * 70)
    documented = load_documented_corrections()

    if documented:
        anchor_corr_doc = documented.get('anchor_bias_correction', None)
        pl_corr_doc = documented.get('pl_bias_correction', None)

        print(f"Anchor correction:")
        print(f"  Documented:  {anchor_corr_doc:.4f} km/s/Mpc")
        print(f"  Recomputed:  {anchor_corr_recomputed:.4f} km/s/Mpc")
        diff_anchor = abs(anchor_corr_recomputed - anchor_corr_doc)
        print(f"  Difference:  {diff_anchor:.4f} km/s/Mpc")

        if diff_anchor < TOLERANCE_CORRECTION:
            print(f"  ✓ PASS (within {TOLERANCE_CORRECTION} km/s/Mpc)")
        else:
            print(f"  ✗ FAIL (exceeds {TOLERANCE_CORRECTION} km/s/Mpc)")

        print()
        print(f"P-L correction:")
        print(f"  Documented:  {pl_corr_doc:.4f} km/s/Mpc")
        print(f"  Recomputed:  {pl_corr_recomputed:.4f} km/s/Mpc")
        diff_pl = abs(pl_corr_recomputed - pl_corr_doc)
        print(f"  Difference:  {diff_pl:.4f} km/s/Mpc")

        if diff_pl < TOLERANCE_CORRECTION:
            print(f"  ✓ PASS (within {TOLERANCE_CORRECTION} km/s/Mpc)")
        else:
            print(f"  ✗ FAIL (exceeds {TOLERANCE_CORRECTION} km/s/Mpc)")

        passed = (diff_anchor < TOLERANCE_CORRECTION and
                 diff_pl < TOLERANCE_CORRECTION)
    else:
        print("⚠ WARNING: No documented corrections found for comparison")
        passed = False

    print()
    print("=" * 70)
    if passed:
        print("✓ PHASE II VERIFICATION: PASS")
    else:
        print("✗ PHASE II VERIFICATION: FAIL")
    print("=" * 70)

    # Save log
    log = {
        'anchor_correction': {
            'recomputed': float(anchor_corr_recomputed),
            'documented': float(anchor_corr_doc) if documented else None,
            'difference': float(diff_anchor) if documented else None
        },
        'pl_correction': {
            'recomputed': float(pl_corr_recomputed),
            'documented': float(pl_corr_doc) if documented else None,
            'difference': float(diff_pl) if documented else None
        },
        'anchor_means': {k: {'mean': float(v['mean']), 'std': float(v['std']), 'count': int(v['count'])}
                        for k, v in anchor_means.items()},
        'passed': passed
    }

    log_file = Path('outputs/logs/phase2_corrections_recomputation.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(log, indent=2))

    print(f"✓ Log saved: {log_file}")

    # Save SSOT logs
    accept_log = accept_tree.save_log()
    discovery_log = discovery_tree.save_log()
    print(f"✓ Acceptability tree log: {accept_log}")
    print(f"✓ Discovery tree log: {discovery_log}")

    # Return based on mode
    if args.mode == 'audit':
        return 0  # Always succeed in audit mode
    elif args.mode == 'dry-run':
        return 0
    else:
        return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
