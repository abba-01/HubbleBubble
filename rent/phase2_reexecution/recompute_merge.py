#!/usr/bin/env python3
"""
RENT Phase II: Re-compute Concordance Merge

Independently recomputes the inverse-variance weighted merge with epistemic penalty.
Verifies the concordance calculation from first principles.

This is ZERO-TRUST: we rebuild the merge calculation from scratch.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0
Uses acceptability tree for graceful failure handling.

DATASET PROVENANCE:
- This script uses the exact datasets documented in assets/external/
- If you're seeing different results, check dataset versions and checksums
- Run: sha256sum assets/external/*.json to verify input data integrity

Usage:
    python rent/phase2_reexecution/recompute_merge.py [--mode MODE]
"""
import sys
import json
from pathlib import Path
import numpy as np
import hashlib
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree

# Tolerance for numerical comparisons
TOLERANCE_MEAN = 0.01  # km/s/Mpc
TOLERANCE_UNCERTAINTY = 0.01  # km/s/Mpc

def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()

def document_input_provenance():
    """
    Document the exact input files used.

    This is critical for RENT: if someone runs this later and gets different
    results, they can check if it's because they have different input data
    or because the methodology is broken.
    """
    input_files = [
        'assets/external/baseline_measurements.json',
        'assets/external/systematic_corrections_applied.json',
        'outputs/corrections/epistemic_penalty_applied.json'
    ]

    print("=" * 70)
    print("INPUT DATA PROVENANCE")
    print("=" * 70)
    print()
    print("This script uses the following input files:")
    print()

    provenance = {}
    for file_path in input_files:
        path = Path(file_path)
        if path.exists():
            file_hash = compute_file_hash(path)
            file_size = path.stat().st_size
            print(f"  {file_path}")
            print(f"    SHA-256: {file_hash}")
            print(f"    Size:    {file_size} bytes")
            print()
            provenance[file_path] = {
                'sha256': file_hash,
                'size': file_size,
                'exists': True
            }
        else:
            print(f"  {file_path}")
            print(f"    ✗ NOT FOUND")
            print()
            provenance[file_path] = {
                'exists': False
            }

    print("If you're seeing different results than documented:")
    print("  1. Check the hashes above against the documented values")
    print("  2. Verify you're using the same dataset version")
    print("  3. Check outputs/logs/phase2_merge_recomputation.json for details")
    print()
    print("=" * 70)
    print()

    return provenance

def load_corrected_measurements():
    """Load the corrected SH0ES and Planck measurements"""
    # Load systematic corrections
    corrections_file = Path('assets/external/systematic_corrections_applied.json')
    if not corrections_file.exists():
        print(f"✗ CRITICAL: {corrections_file} not found")
        return None

    with open(corrections_file) as f:
        corrections = json.load(f)

    # Load raw measurements
    measurements_file = Path('assets/external/baseline_measurements.json')
    if not measurements_file.exists():
        print(f"✗ CRITICAL: {measurements_file} not found")
        return None

    with open(measurements_file) as f:
        measurements = json.load(f)

    # Apply corrections
    shoes_raw = measurements.get('shoes_h0_mean', None)
    shoes_unc_raw = measurements.get('shoes_h0_uncertainty', None)
    planck_raw = measurements.get('planck_h0_mean', None)
    planck_unc_raw = measurements.get('planck_h0_uncertainty', None)

    anchor_corr = corrections.get('anchor_bias_correction', 0.0)
    pl_corr = corrections.get('pl_bias_correction', 0.0)

    if None in [shoes_raw, shoes_unc_raw, planck_raw, planck_unc_raw]:
        print("✗ CRITICAL: Missing baseline measurements")
        return None

    # Apply corrections to SH0ES
    shoes_corrected = shoes_raw + anchor_corr + pl_corr
    shoes_unc = shoes_unc_raw  # Uncertainty unchanged

    planck_corrected = planck_raw
    planck_unc = planck_unc_raw

    return {
        'shoes': {'mean': shoes_corrected, 'uncertainty': shoes_unc},
        'planck': {'mean': planck_corrected, 'uncertainty': planck_unc}
    }

def load_epistemic_penalty():
    """Load the epistemic penalty"""
    penalty_file = Path('outputs/corrections/epistemic_penalty_applied.json')
    if penalty_file.exists():
        with open(penalty_file) as f:
            data = json.load(f)
        return data.get('epistemic_penalty', None)

    # Fallback: try to find it in documented corrections
    corrections_file = Path('assets/external/systematic_corrections_applied.json')
    if corrections_file.exists():
        with open(corrections_file) as f:
            data = json.load(f)
        return data.get('epistemic_penalty', None)

    return None

def compute_concordance_merge_from_scratch(data, u_epi):
    """
    Recompute inverse-variance weighted merge with epistemic penalty.

    Formula:
    1. Inflate uncertainties: σ'² = σ² + u_epi²
    2. Compute weights: w = 1/σ'²
    3. Weighted mean: H₀ = Σ(w × H) / Σ(w)
    4. Merged uncertainty: σ = 1/√(Σw)
    """
    shoes_mean = data['shoes']['mean']
    shoes_unc = data['shoes']['uncertainty']
    planck_mean = data['planck']['mean']
    planck_unc = data['planck']['uncertainty']

    print()
    print("Concordance Merge Calculation:")
    print("-" * 70)
    print()
    print("Step 1: Inflate uncertainties with epistemic penalty")
    print(f"  u_epi = {u_epi:.4f} km/s/Mpc")
    print()

    # Inflate uncertainties
    shoes_unc_penalized = np.sqrt(shoes_unc**2 + u_epi**2)
    planck_unc_penalized = np.sqrt(planck_unc**2 + u_epi**2)

    print(f"  SH0ES:")
    print(f"    Original uncertainty: {shoes_unc:.4f} km/s/Mpc")
    print(f"    Penalized uncertainty: {shoes_unc_penalized:.4f} km/s/Mpc")
    print(f"    Inflation: +{shoes_unc_penalized - shoes_unc:.4f} km/s/Mpc")
    print()
    print(f"  Planck:")
    print(f"    Original uncertainty: {planck_unc:.4f} km/s/Mpc")
    print(f"    Penalized uncertainty: {planck_unc_penalized:.4f} km/s/Mpc")
    print(f"    Inflation: +{planck_unc_penalized - planck_unc:.4f} km/s/Mpc")
    print()

    print("Step 2: Compute inverse-variance weights")
    w_shoes = 1.0 / shoes_unc_penalized**2
    w_planck = 1.0 / planck_unc_penalized**2
    w_total = w_shoes + w_planck

    print(f"  w_SH0ES  = 1/{shoes_unc_penalized:.4f}² = {w_shoes:.6f} (Mpc/km/s)²")
    print(f"  w_Planck = 1/{planck_unc_penalized:.4f}² = {w_planck:.6f} (Mpc/km/s)²")
    print(f"  w_total  = {w_total:.6f} (Mpc/km/s)²")
    print()

    print("Step 3: Compute weighted mean")
    h0_concordance = (w_shoes * shoes_mean + w_planck * planck_mean) / w_total
    print(f"  H₀ = (w_SH0ES × H_SH0ES + w_Planck × H_Planck) / w_total")
    print(f"     = ({w_shoes:.6f} × {shoes_mean:.3f} + {w_planck:.6f} × {planck_mean:.3f}) / {w_total:.6f}")
    print(f"     = {h0_concordance:.4f} km/s/Mpc")
    print()

    print("Step 4: Compute merged uncertainty")
    sigma_concordance = 1.0 / np.sqrt(w_total)
    print(f"  σ = 1/√(w_total)")
    print(f"    = 1/√({w_total:.6f})")
    print(f"    = {sigma_concordance:.4f} km/s/Mpc")
    print()

    # Relative weights
    rel_weight_shoes = w_shoes / w_total * 100
    rel_weight_planck = w_planck / w_total * 100

    print("Relative weights:")
    print(f"  SH0ES:  {rel_weight_shoes:.2f}%")
    print(f"  Planck: {rel_weight_planck:.2f}%")

    return h0_concordance, sigma_concordance, {
        'shoes_weight': w_shoes,
        'planck_weight': w_planck,
        'shoes_relative': rel_weight_shoes,
        'planck_relative': rel_weight_planck
    }

def load_documented_concordance():
    """Load the documented concordance value"""
    concordance_file = Path('outputs/final_results/concordance_h0.json')
    if concordance_file.exists():
        with open(concordance_file) as f:
            data = json.load(f)
        return data.get('h0_mean', None), data.get('h0_uncertainty', None)
    return None, None

def main():
    """Main re-computation routine"""
    parser = argparse.ArgumentParser(description='RENT Phase II: Recompute Concordance Merge')
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        default=True, help='Disable interactive prompts')
    args = parser.parse_args()

    # Initialize acceptability tree
    accept_tree = AcceptabilityTree(mode=args.mode, interactive=args.interactive)

    print("=" * 70)
    print("RENT PHASE II: RE-COMPUTE CONCORDANCE MERGE")
    print(f"Mode: {args.mode}")
    print("=" * 70)
    print()

    # Document input provenance
    provenance = document_input_provenance()

    print("Step 1: Load corrected measurements")
    print("-" * 70)
    data = load_corrected_measurements()
    if data is None:
        accept_tree.save_log()
        return 1 if args.mode == 'strict' else 0

    print(f"✓ SH0ES (corrected): {data['shoes']['mean']:.3f} ± {data['shoes']['uncertainty']:.3f} km/s/Mpc")
    print(f"✓ Planck:            {data['planck']['mean']:.3f} ± {data['planck']['uncertainty']:.3f} km/s/Mpc")
    print()

    print("Step 2: Load epistemic penalty")
    print("-" * 70)
    u_epi = load_epistemic_penalty()
    if u_epi is None:
        print("✗ CRITICAL: Epistemic penalty not found")
        return 1

    print(f"✓ u_epi = {u_epi:.4f} km/s/Mpc")
    print()

    print("Step 3: Recompute concordance merge from scratch")
    print("-" * 70)
    h0_recomputed, sigma_recomputed, weights = compute_concordance_merge_from_scratch(data, u_epi)
    print()

    print("Step 4: Compare to documented value")
    print("-" * 70)
    h0_documented, sigma_documented = load_documented_concordance()

    if h0_documented is not None and sigma_documented is not None:
        print(f"Concordance H₀:")
        print(f"  Documented:  {h0_documented:.4f} ± {sigma_documented:.4f} km/s/Mpc")
        print(f"  Recomputed:  {h0_recomputed:.4f} ± {sigma_recomputed:.4f} km/s/Mpc")

        diff_mean = abs(h0_recomputed - h0_documented)
        diff_unc = abs(sigma_recomputed - sigma_documented)

        print()
        print(f"  Difference (mean):        {diff_mean:.4f} km/s/Mpc")
        print(f"  Difference (uncertainty): {diff_unc:.4f} km/s/Mpc")

        mean_pass = diff_mean < TOLERANCE_MEAN
        unc_pass = diff_unc < TOLERANCE_UNCERTAINTY

        if mean_pass:
            print(f"  ✓ Mean within {TOLERANCE_MEAN} km/s/Mpc")
        else:
            print(f"  ✗ Mean exceeds {TOLERANCE_MEAN} km/s/Mpc")

        if unc_pass:
            print(f"  ✓ Uncertainty within {TOLERANCE_UNCERTAINTY} km/s/Mpc")
        else:
            print(f"  ✗ Uncertainty exceeds {TOLERANCE_UNCERTAINTY} km/s/Mpc")

        passed = mean_pass and unc_pass
    else:
        print("⚠ WARNING: No documented concordance found for comparison")
        passed = False

    print()
    print("=" * 70)
    if passed:
        print("✓ PHASE II CONCORDANCE MERGE: PASS")
    else:
        print("✗ PHASE II CONCORDANCE MERGE: FAIL")
    print("=" * 70)

    # Save log
    log = {
        'input_provenance': provenance,
        'concordance': {
            'recomputed_mean': float(h0_recomputed),
            'recomputed_uncertainty': float(sigma_recomputed),
            'documented_mean': float(h0_documented) if h0_documented else None,
            'documented_uncertainty': float(sigma_documented) if sigma_documented else None,
            'difference_mean': float(diff_mean) if h0_documented else None,
            'difference_uncertainty': float(diff_unc) if sigma_documented else None
        },
        'weights': {
            'shoes_weight': float(weights['shoes_weight']),
            'planck_weight': float(weights['planck_weight']),
            'shoes_relative_percent': float(weights['shoes_relative']),
            'planck_relative_percent': float(weights['planck_relative'])
        },
        'passed': passed,
        'note': 'If results differ from documented values, check input file hashes in input_provenance above'
    }

    log_file = Path('outputs/logs/phase2_merge_recomputation.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(log, indent=2))

    print(f"✓ Log saved: {log_file}")

    # Save acceptability tree log
    accept_log = accept_tree.save_log()
    print(f"✓ Acceptability tree log: {accept_log}")

    print()
    print("NOTE: All input file hashes are saved in the log.")
    print("      If someone reruns this later with different data, they can compare hashes")
    print("      to determine if differences are due to data changes or methodology errors.")

    # Return based on mode
    if args.mode in ['audit', 'dry-run']:
        return 0
    else:
        return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
