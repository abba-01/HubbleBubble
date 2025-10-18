#!/usr/bin/env python3
"""
RENT Phase III: Verify SH0ES Anchor Data Fidelity

Cross-validates SH0ES anchor means and spread.
Checks for outliers, data entry errors, and anchor consistency.

Expected values:
- MW:      ~76.1 km/s/Mpc
- LMC:     ~72.3 km/s/Mpc
- NGC4258: ~72.5 km/s/Mpc
- Spread:  ~3.8 km/s/Mpc

DATASET PROVENANCE:
- Uses riess_2016_systematic_grid_210.csv from assets/vizier/
- If results differ, check dataset version

SSOT Compliance: RENT_SPEC_VERSION 1.0.0

Usage:
    python rent/phase3_crossvalidation/verify_shoes_anchors.py
"""
import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree
import numpy as np
import pandas as pd
import hashlib
from scipy import stats

# Tolerance for numerical comparisons
TOLERANCE_MEAN = 0.2  # km/s/Mpc (loose for anchor means)
TOLERANCE_SPREAD = 0.5  # km/s/Mpc

# Expected values from documentation
EXPECTED_ANCHORS = {
    'MW': 76.1,
    'LMC': 72.3,
    'NGC4258': 72.5
}

def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()

def load_shoes_grid():
    """Load SH0ES systematic grid"""
    grid_file = Path('assets/vizier/riess_2016_systematic_grid_210.csv')

    if not grid_file.exists():
        print(f"✗ CRITICAL: {grid_file} not found")
        return None

    try:
        df = pd.read_csv(grid_file)
        file_hash = compute_file_hash(grid_file)

        print("=" * 70)
        print("SH0ES DATA PROVENANCE")
        print("=" * 70)
        print(f"File: {grid_file}")
        print(f"SHA-256: {file_hash}")
        print(f"Size: {grid_file.stat().st_size} bytes")
        print(f"Rows: {len(df)}")
        print()

        print("Columns:")
        for col in df.columns:
            print(f"  {col}")
        print()

        return df, file_hash
    except Exception as e:
        print(f"✗ ERROR loading SH0ES grid: {e}")
        return None

def compute_anchor_statistics(df):
    """
    Compute statistics for each anchor.

    Expected anchor codes: 'M' (MW), 'L' (LMC), 'N' (NGC4258)
    """
    anchor_codes = {
        'M': 'MW',
        'L': 'LMC',
        'N': 'NGC4258'
    }

    print("Anchor Statistics:")
    print("-" * 70)

    anchor_stats = {}
    for code, name in anchor_codes.items():
        subset = df[df['Anc'] == code]

        if len(subset) == 0:
            print(f"⚠ WARNING: No data for anchor {name}")
            continue

        h0_values = subset['H0']
        mean = h0_values.mean()
        std = h0_values.std()
        median = h0_values.median()
        count = len(subset)
        q25 = h0_values.quantile(0.25)
        q75 = h0_values.quantile(0.75)

        anchor_stats[name] = {
            'mean': mean,
            'std': std,
            'median': median,
            'count': count,
            'q25': q25,
            'q75': q75
        }

        print(f"{name:12s}: {mean:6.2f} ± {std:4.2f} km/s/Mpc  (n={count}, median={median:.2f})")
        print(f"              Range: [{h0_values.min():.2f}, {h0_values.max():.2f}]")
        print(f"              IQR:   [{q25:.2f}, {q75:.2f}]")
        print()

    # Compute anchor spread
    if len(anchor_stats) >= 2:
        means = [v['mean'] for v in anchor_stats.values()]
        spread = max(means) - min(means)

        print(f"Anchor spread (max - min): {spread:.2f} km/s/Mpc")
        print()

        return anchor_stats, spread
    else:
        print("✗ CRITICAL: Not enough anchors to compute spread")
        return anchor_stats, None

def check_for_outliers(df):
    """
    Check for outliers in the systematic grid.

    Use IQR method to detect potential data entry errors.
    """
    print("Outlier Detection:")
    print("-" * 70)

    h0_all = df['H0']
    q25 = h0_all.quantile(0.25)
    q75 = h0_all.quantile(0.75)
    iqr = q75 - q25

    lower_bound = q25 - 3.0 * iqr  # 3× IQR (very conservative)
    upper_bound = q75 + 3.0 * iqr

    outliers = df[(h0_all < lower_bound) | (h0_all > upper_bound)]

    print(f"IQR: {iqr:.2f} km/s/Mpc")
    print(f"Outlier bounds: [{lower_bound:.2f}, {upper_bound:.2f}] km/s/Mpc")
    print(f"Outliers detected: {len(outliers)}")

    if len(outliers) > 0:
        print()
        print("⚠ WARNING: Outliers found:")
        for idx, row in outliers.iterrows():
            print(f"  Row {idx}: H0={row['H0']:.2f}, Anc={row.get('Anc', 'N/A')}")
        print()
        return outliers
    else:
        print("✓ No extreme outliers detected")
        print()
        return None

def verify_anchor_consistency(anchor_stats):
    """
    Verify anchor consistency against expected values.

    Checks if computed means are within tolerance of documented values.
    """
    print("Anchor Consistency Check:")
    print("-" * 70)

    comparisons = {}
    all_pass = True

    for anchor_name, expected_mean in EXPECTED_ANCHORS.items():
        if anchor_name not in anchor_stats:
            print(f"⚠ {anchor_name}: NOT FOUND in data")
            all_pass = False
            continue

        computed_mean = anchor_stats[anchor_name]['mean']
        diff = abs(computed_mean - expected_mean)

        comparisons[anchor_name] = {
            'expected': expected_mean,
            'computed': computed_mean,
            'difference': diff
        }

        print(f"{anchor_name:12s}:")
        print(f"  Expected:  {expected_mean:.2f} km/s/Mpc")
        print(f"  Computed:  {computed_mean:.2f} km/s/Mpc")
        print(f"  Δ:         {diff:.2f} km/s/Mpc")

        if diff < TOLERANCE_MEAN:
            print(f"  ✓ Within {TOLERANCE_MEAN} km/s/Mpc")
        else:
            print(f"  ✗ Exceeds {TOLERANCE_MEAN} km/s/Mpc")
            all_pass = False
        print()

    return comparisons, all_pass

def main():
    """Main verification routine"""
    print("=" * 70)
    print("RENT PHASE III: VERIFY SH0ES ANCHOR DATA FIDELITY")
    print("=" * 70)
    print()

    print("Step 1: Load SH0ES systematic grid")
    print("-" * 70)
    result = load_shoes_grid()
    if result is None:
        return 1

    df, file_hash = result
    print()

    print("Step 2: Compute anchor statistics")
    print("-" * 70)
    anchor_stats, spread = compute_anchor_statistics(df)
    if spread is None:
        return 1
    print()

    print("Step 3: Check for outliers")
    print("-" * 70)
    outliers = check_for_outliers(df)
    print()

    print("Step 4: Verify anchor consistency")
    print("-" * 70)
    comparisons, consistency_pass = verify_anchor_consistency(anchor_stats)
    print()

    print("Step 5: Verify anchor spread")
    print("-" * 70)

    expected_spread = 3.84  # MW - LMC ≈ 3.8 km/s/Mpc
    diff_spread = abs(spread - expected_spread)

    print(f"Anchor spread:")
    print(f"  Expected:  ~{expected_spread:.2f} km/s/Mpc")
    print(f"  Computed:  {spread:.2f} km/s/Mpc")
    print(f"  Δ:         {diff_spread:.2f} km/s/Mpc")

    if diff_spread < TOLERANCE_SPREAD:
        print(f"  ✓ Within {TOLERANCE_SPREAD} km/s/Mpc")
        spread_pass = True
    else:
        print(f"  ✗ Exceeds {TOLERANCE_SPREAD} km/s/Mpc")
        spread_pass = False

    outlier_pass = (outliers is None or len(outliers) == 0)
    passed = consistency_pass and spread_pass and outlier_pass

    print()
    print("=" * 70)
    if passed:
        print("✓ PHASE III SH0ES ANCHOR VERIFICATION: PASS")
    else:
        print("✗ PHASE III SH0ES ANCHOR VERIFICATION: FAIL")
    print("=" * 70)

    # Save log
    log = {
        'provenance': {
            'file': 'assets/vizier/riess_2016_systematic_grid_210.csv',
            'sha256': file_hash
        },
        'anchor_statistics': {
            name: {
                'mean': float(stats['mean']),
                'std': float(stats['std']),
                'median': float(stats['median']),
                'count': int(stats['count'])
            } for name, stats in anchor_stats.items()
        },
        'anchor_spread': {
            'computed': float(spread),
            'expected': float(expected_spread),
            'difference': float(diff_spread)
        },
        'consistency_checks': {
            name: {
                'expected': float(comp['expected']),
                'computed': float(comp['computed']),
                'difference': float(comp['difference'])
            } for name, comp in comparisons.items()
        },
        'outliers': {
            'count': len(outliers) if outliers is not None else 0,
            'detected': outliers is not None and len(outliers) > 0
        },
        'passed': passed,
        'note': 'If results differ, check dataset version and SHA-256 hash'
    }

    log_file = Path('outputs/logs/phase3_shoes_anchor_verification.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(log, indent=2))

    print(f"✓ Log saved: {log_file}")

    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
