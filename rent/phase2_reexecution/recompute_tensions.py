#!/usr/bin/env python3
"""
RENT Phase II: Re-compute Tensions

Independently recomputes baseline and final tensions.
Verifies the ~77% tension reduction claim.

This is ZERO-TRUST: we rebuild the tension calculation from scratch.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0
Uses acceptability tree for graceful failure handling.

DATASET PROVENANCE:
- This script uses the exact datasets documented in assets/external/
- If you're seeing different results, check dataset versions and checksums
- All input file hashes are logged to outputs/logs/phase2_tensions_recomputation.json

Usage:
    python rent/phase2_reexecution/recompute_tensions.py [--mode MODE]
"""
import sys
import json
from pathlib import Path
import numpy as np
from scipy import stats
import hashlib
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree

# Tolerance for numerical comparisons
TOLERANCE_TENSION = 0.05  # sigma
TOLERANCE_REDUCTION = 1.0  # percentage points

def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()

def document_input_provenance():
    """Document the exact input files used"""
    input_files = [
        'assets/external/baseline_measurements.json',
        'assets/external/systematic_corrections_applied.json',
        'outputs/corrections/epistemic_penalty_applied.json',
        'outputs/final_results/concordance_h0.json'
    ]

    print("=" * 70)
    print("INPUT DATA PROVENANCE")
    print("=" * 70)
    print()

    provenance = {}
    for file_path in input_files:
        path = Path(file_path)
        if path.exists():
            file_hash = compute_file_hash(path)
            provenance[file_path] = {'sha256': file_hash, 'exists': True}
            print(f"  {file_path}")
            print(f"    SHA-256: {file_hash}")
        else:
            provenance[file_path] = {'exists': False}
            print(f"  {file_path}: ✗ NOT FOUND")

    print()
    print("=" * 70)
    print()

    return provenance

def compute_tension(h1, sigma1, h2, sigma2):
    """
    Compute tension between two measurements.

    Formula: T = |H₁ - H₂| / √(σ₁² + σ₂²)

    Returns tension in units of sigma.
    """
    delta = abs(h1 - h2)
    sigma_combined = np.sqrt(sigma1**2 + sigma2**2)
    tension = delta / sigma_combined
    return tension

def compute_baseline_tension():
    """
    Compute baseline tension (no corrections).

    Uses raw SH0ES and Planck measurements.
    """
    measurements_file = Path('assets/external/baseline_measurements.json')
    if not measurements_file.exists():
        print(f"✗ CRITICAL: {measurements_file} not found")
        return None

    with open(measurements_file) as f:
        measurements = json.load(f)

    shoes_raw = measurements.get('shoes_h0_mean', None)
    shoes_unc_raw = measurements.get('shoes_h0_uncertainty', None)
    planck_raw = measurements.get('planck_h0_mean', None)
    planck_unc_raw = measurements.get('planck_h0_uncertainty', None)

    if None in [shoes_raw, shoes_unc_raw, planck_raw, planck_unc_raw]:
        print("✗ CRITICAL: Missing baseline measurements")
        return None

    tension_baseline = compute_tension(shoes_raw, shoes_unc_raw, planck_raw, planck_unc_raw)

    print("Baseline Tension (No Corrections):")
    print("-" * 70)
    print(f"  SH0ES (raw):  {shoes_raw:.3f} ± {shoes_unc_raw:.3f} km/s/Mpc")
    print(f"  Planck:       {planck_raw:.3f} ± {planck_unc_raw:.3f} km/s/Mpc")
    print(f"  Split:        {abs(shoes_raw - planck_raw):.3f} km/s/Mpc")
    print(f"  σ_combined:   {np.sqrt(shoes_unc_raw**2 + planck_unc_raw**2):.3f} km/s/Mpc")
    print(f"  Tension:      {tension_baseline:.3f}σ")
    print()

    return {
        'tension': tension_baseline,
        'shoes': shoes_raw,
        'shoes_unc': shoes_unc_raw,
        'planck': planck_raw,
        'planck_unc': planck_unc_raw
    }

def compute_final_tension():
    """
    Compute final tension (with corrections + epistemic penalty).

    Uses corrected measurements and concordance result.
    """
    # Load corrections
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

    # Load epistemic penalty
    penalty_file = Path('outputs/corrections/epistemic_penalty_applied.json')
    if penalty_file.exists():
        with open(penalty_file) as f:
            penalty_data = json.load(f)
        u_epi = penalty_data.get('epistemic_penalty', 0.0)
    else:
        u_epi = corrections.get('epistemic_penalty', 0.0)

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

    # Apply corrections
    shoes_corrected = shoes_raw + anchor_corr + pl_corr
    planck_corrected = planck_raw

    # Apply epistemic penalty
    shoes_unc_penalized = np.sqrt(shoes_unc_raw**2 + u_epi**2)
    planck_unc_penalized = np.sqrt(planck_unc_raw**2 + u_epi**2)

    # Compute tension
    tension_final = compute_tension(
        shoes_corrected, shoes_unc_penalized,
        planck_corrected, planck_unc_penalized
    )

    print("Final Tension (With Corrections + Epistemic Penalty):")
    print("-" * 70)
    print(f"  Corrections applied:")
    print(f"    Anchor:  {anchor_corr:+.4f} km/s/Mpc")
    print(f"    P-L:     {pl_corr:+.4f} km/s/Mpc")
    print(f"    u_epi:   {u_epi:.4f} km/s/Mpc")
    print()
    print(f"  SH0ES (corrected):  {shoes_corrected:.3f} ± {shoes_unc_penalized:.3f} km/s/Mpc")
    print(f"  Planck:             {planck_corrected:.3f} ± {planck_unc_penalized:.3f} km/s/Mpc")
    print(f"  Split:              {abs(shoes_corrected - planck_corrected):.3f} km/s/Mpc")
    print(f"  σ_combined:         {np.sqrt(shoes_unc_penalized**2 + planck_unc_penalized**2):.3f} km/s/Mpc")
    print(f"  Tension:            {tension_final:.3f}σ")
    print()

    return {
        'tension': tension_final,
        'shoes': shoes_corrected,
        'shoes_unc': shoes_unc_penalized,
        'planck': planck_corrected,
        'planck_unc': planck_unc_penalized,
        'corrections': {
            'anchor': anchor_corr,
            'pl': pl_corr,
            'epistemic_penalty': u_epi
        }
    }

def compute_tension_reduction(baseline, final):
    """
    Compute tension reduction percentage.

    Formula: reduction = (T_baseline - T_final) / T_baseline × 100%
    """
    if baseline is None or final is None:
        return None

    t_baseline = baseline['tension']
    t_final = final['tension']

    reduction_abs = t_baseline - t_final
    reduction_pct = (reduction_abs / t_baseline) * 100.0

    print("Tension Reduction:")
    print("-" * 70)
    print(f"  Baseline tension: {t_baseline:.3f}σ")
    print(f"  Final tension:    {t_final:.3f}σ")
    print(f"  Reduction:        {reduction_abs:.3f}σ ({reduction_pct:.2f}%)")
    print()

    return {
        'baseline': t_baseline,
        'final': t_final,
        'reduction_sigma': reduction_abs,
        'reduction_percent': reduction_pct
    }

def load_documented_tensions():
    """Load documented tension values"""
    tensions_file = Path('outputs/validations/tension_metrics.json')
    if tensions_file.exists():
        with open(tensions_file) as f:
            data = json.load(f)
        return {
            'baseline': data.get('baseline_tension', None),
            'final': data.get('final_tension', None),
            'reduction_pct': data.get('tension_reduction_percent', None)
        }
    return None

def main():
    """Main re-computation routine"""
    parser = argparse.ArgumentParser(description='RENT Phase II: Recompute Tensions')
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        default=True, help='Disable interactive prompts')
    args = parser.parse_args()

    # Initialize acceptability tree
    accept_tree = AcceptabilityTree(mode=args.mode, interactive=args.interactive)

    print("=" * 70)
    print("RENT PHASE II: RE-COMPUTE TENSIONS")
    print(f"Mode: {args.mode}")
    print("=" * 70)
    print()

    # Document input provenance
    provenance = document_input_provenance()

    print("Step 1: Recompute baseline tension")
    print("-" * 70)
    baseline = compute_baseline_tension()
    if baseline is None:
        accept_tree.save_log()
        return 1 if args.mode == 'strict' else 0
    print()

    print("Step 2: Recompute final tension")
    print("-" * 70)
    final = compute_final_tension()
    if final is None:
        accept_tree.save_log()
        return 1 if args.mode == 'strict' else 0
    print()

    print("Step 3: Compute tension reduction")
    print("-" * 70)
    reduction = compute_tension_reduction(baseline, final)
    if reduction is None:
        return 1
    print()

    print("Step 4: Compare to documented values")
    print("-" * 70)
    documented = load_documented_tensions()

    if documented and documented['baseline'] is not None:
        print("Baseline tension:")
        print(f"  Documented:  {documented['baseline']:.4f}σ")
        print(f"  Recomputed:  {baseline['tension']:.4f}σ")
        diff_baseline = abs(baseline['tension'] - documented['baseline'])
        print(f"  Difference:  {diff_baseline:.4f}σ")

        if diff_baseline < TOLERANCE_TENSION:
            print(f"  ✓ PASS (within {TOLERANCE_TENSION}σ)")
            baseline_pass = True
        else:
            print(f"  ✗ FAIL (exceeds {TOLERANCE_TENSION}σ)")
            baseline_pass = False
        print()

        print("Final tension:")
        print(f"  Documented:  {documented['final']:.4f}σ")
        print(f"  Recomputed:  {final['tension']:.4f}σ")
        diff_final = abs(final['tension'] - documented['final'])
        print(f"  Difference:  {diff_final:.4f}σ")

        if diff_final < TOLERANCE_TENSION:
            print(f"  ✓ PASS (within {TOLERANCE_TENSION}σ)")
            final_pass = True
        else:
            print(f"  ✗ FAIL (exceeds {TOLERANCE_TENSION}σ)")
            final_pass = False
        print()

        print("Tension reduction:")
        print(f"  Documented:  {documented['reduction_pct']:.2f}%")
        print(f"  Recomputed:  {reduction['reduction_percent']:.2f}%")
        diff_reduction = abs(reduction['reduction_percent'] - documented['reduction_pct'])
        print(f"  Difference:  {diff_reduction:.2f} percentage points")

        if diff_reduction < TOLERANCE_REDUCTION:
            print(f"  ✓ PASS (within {TOLERANCE_REDUCTION} percentage points)")
            reduction_pass = True
        else:
            print(f"  ✗ FAIL (exceeds {TOLERANCE_REDUCTION} percentage points)")
            reduction_pass = False

        passed = baseline_pass and final_pass and reduction_pass
    else:
        print("⚠ WARNING: No documented tensions found for comparison")
        passed = False

    print()
    print("=" * 70)
    if passed:
        print("✓ PHASE II TENSIONS: PASS")
    else:
        print("✗ PHASE II TENSIONS: FAIL")
    print("=" * 70)

    # Save log
    log = {
        'input_provenance': provenance,
        'baseline_tension': {
            'recomputed': float(baseline['tension']),
            'documented': float(documented['baseline']) if documented and documented['baseline'] else None,
            'difference': float(diff_baseline) if documented and documented['baseline'] else None
        },
        'final_tension': {
            'recomputed': float(final['tension']),
            'documented': float(documented['final']) if documented and documented['final'] else None,
            'difference': float(diff_final) if documented and documented['final'] else None
        },
        'tension_reduction': {
            'recomputed_percent': float(reduction['reduction_percent']),
            'documented_percent': float(documented['reduction_pct']) if documented and documented['reduction_pct'] else None,
            'difference_pct': float(diff_reduction) if documented and documented['reduction_pct'] else None
        },
        'corrections_applied': final['corrections'],
        'passed': passed,
        'note': 'If results differ from documented values, check input file hashes in input_provenance above'
    }

    log_file = Path('outputs/logs/phase2_tensions_recomputation.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(log, indent=2))

    print(f"✓ Log saved: {log_file}")

    # Save acceptability tree log
    accept_log = accept_tree.save_log()
    print(f"✓ Acceptability tree log: {accept_log}")

    # Return based on mode
    if args.mode in ['audit', 'dry-run']:
        return 0
    else:
        return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
