#!/usr/bin/env python3
"""
RENT Phase II: Re-compute Epistemic Penalty

Independently recomputes the epistemic penalty from first principles.
Verifies the formula: u_epi = 0.5 × |ΔH| × Δ_T × (1 - f_systematic)

This is ZERO-TRUST: we rebuild the penalty calculation from scratch.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0
Uses acceptability tree for graceful failure handling.

Usage:
    python rent/phase2_reexecution/recompute_penalty.py [--mode MODE]
"""
import sys
import json
from pathlib import Path
import numpy as np
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree

# Tolerance for numerical comparisons
TOLERANCE_PENALTY = 0.01  # km/s/Mpc

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
        'planck': {'mean': planck_corrected, 'uncertainty': planck_unc},
        'corrections': {'anchor': anchor_corr, 'pl': pl_corr}
    }

def compute_epistemic_penalty_from_scratch(data):
    """
    Recompute epistemic penalty from first principles.

    Formula: u_epi = 0.5 × |ΔH| × Δ_T × (1 - f_systematic)

    Where:
    - ΔH = H₀(SH0ES) - H₀(Planck) [after corrections]
    - Δ_T = 1.36 [tension reduction factor, from documented protocol]
    - f_systematic = 0.50 [fraction of split attributable to systematics]

    The penalty is applied symmetrically to both measurements.
    """
    shoes_mean = data['shoes']['mean']
    planck_mean = data['planck']['mean']

    # Compute split
    delta_h = shoes_mean - planck_mean

    # Load epistemic parameters
    params_file = Path('assets/external/epistemic_penalty_parameters.json')
    if params_file.exists():
        with open(params_file) as f:
            params = json.load(f)
        delta_t = params.get('delta_t', 1.36)
        f_systematic = params.get('f_systematic', 0.50)
        print(f"✓ Loaded epistemic parameters from {params_file}")
    else:
        # Use documented defaults
        delta_t = 1.36
        f_systematic = 0.50
        print(f"⚠ WARNING: {params_file} not found, using documented defaults")

    # Compute penalty
    u_epi = 0.5 * abs(delta_h) * delta_t * (1.0 - f_systematic)

    print()
    print("Epistemic Penalty Calculation:")
    print("-" * 70)
    print(f"  SH0ES (corrected):  {shoes_mean:.3f} km/s/Mpc")
    print(f"  Planck:             {planck_mean:.3f} km/s/Mpc")
    print(f"  Split (ΔH):         {delta_h:.3f} km/s/Mpc")
    print()
    print(f"  Δ_T:                {delta_t:.3f}")
    print(f"  f_systematic:       {f_systematic:.3f}")
    print(f"  (1 - f_sys):        {1.0 - f_systematic:.3f}")
    print()
    print(f"  u_epi = 0.5 × |ΔH| × Δ_T × (1 - f_sys)")
    print(f"        = 0.5 × {abs(delta_h):.3f} × {delta_t:.3f} × {1.0 - f_systematic:.3f}")
    print(f"        = {u_epi:.4f} km/s/Mpc")

    return u_epi, delta_h, delta_t, f_systematic

def load_documented_penalty():
    """Load the documented penalty value"""
    penalty_file = Path('outputs/corrections/epistemic_penalty_applied.json')
    if penalty_file.exists():
        with open(penalty_file) as f:
            data = json.load(f)
        return data.get('epistemic_penalty', None)
    return None

def verify_information_conservation(data, u_epi):
    """
    Verify that the epistemic penalty reduces confidence (information conservation).

    Check: 1/σ²_penalized < 1/σ²_simple

    This ensures we're not inflating confidence by adding systematic corrections.
    """
    shoes_unc_simple = data['shoes']['uncertainty']
    planck_unc_simple = data['planck']['uncertainty']

    # Simple merge
    w_shoes_simple = 1.0 / shoes_unc_simple**2
    w_planck_simple = 1.0 / planck_unc_simple**2
    w_total_simple = w_shoes_simple + w_planck_simple

    # Penalized merge
    shoes_unc_penalized = np.sqrt(shoes_unc_simple**2 + u_epi**2)
    planck_unc_penalized = np.sqrt(planck_unc_simple**2 + u_epi**2)

    w_shoes_penalized = 1.0 / shoes_unc_penalized**2
    w_planck_penalized = 1.0 / planck_unc_penalized**2
    w_total_penalized = w_shoes_penalized + w_planck_penalized

    # Check conservation
    conservation_holds = w_total_penalized < w_total_simple

    print()
    print("Information Conservation Check:")
    print("-" * 70)
    print(f"  Simple merge:")
    print(f"    SH0ES uncertainty:  {shoes_unc_simple:.4f} km/s/Mpc")
    print(f"    Planck uncertainty: {planck_unc_simple:.4f} km/s/Mpc")
    print(f"    Total weight:       {w_total_simple:.6f} (Mpc/km/s)²")
    print()
    print(f"  Penalized merge (u_epi = {u_epi:.4f}):")
    print(f"    SH0ES uncertainty:  {shoes_unc_penalized:.4f} km/s/Mpc")
    print(f"    Planck uncertainty: {planck_unc_penalized:.4f} km/s/Mpc")
    print(f"    Total weight:       {w_total_penalized:.6f} (Mpc/km/s)²")
    print()

    if conservation_holds:
        reduction = (1.0 - w_total_penalized / w_total_simple) * 100
        print(f"  ✓ PASS: Information conservation holds")
        print(f"  Confidence reduced by {reduction:.2f}%")
        return True
    else:
        inflation = (w_total_penalized / w_total_simple - 1.0) * 100
        print(f"  ✗ FAIL: Confidence inflated by {inflation:.2f}%")
        print(f"  This violates information conservation!")
        return False

def main():
    """Main re-computation routine"""
    parser = argparse.ArgumentParser(description='RENT Phase II: Recompute Epistemic Penalty')
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        default=True, help='Disable interactive prompts')
    args = parser.parse_args()

    # Initialize acceptability tree
    accept_tree = AcceptabilityTree(mode=args.mode, interactive=args.interactive)

    print("=" * 70)
    print("RENT PHASE II: RE-COMPUTE EPISTEMIC PENALTY")
    print(f"Mode: {args.mode}")
    print("=" * 70)
    print()

    print("Step 1: Load corrected measurements")
    print("-" * 70)
    data = load_corrected_measurements()
    if data is None:
        accept_tree.save_log()
        return 1 if args.mode == 'strict' else 0

    print(f"✓ SH0ES (corrected): {data['shoes']['mean']:.3f} ± {data['shoes']['uncertainty']:.3f} km/s/Mpc")
    print(f"✓ Planck:            {data['planck']['mean']:.3f} ± {data['planck']['uncertainty']:.3f} km/s/Mpc")
    print(f"  (Anchor correction: {data['corrections']['anchor']:.4f} km/s/Mpc)")
    print(f"  (P-L correction:    {data['corrections']['pl']:.4f} km/s/Mpc)")
    print()

    print("Step 2: Recompute epistemic penalty from scratch")
    print("-" * 70)
    u_epi_recomputed, delta_h, delta_t, f_sys = compute_epistemic_penalty_from_scratch(data)
    print()

    print("Step 3: Verify information conservation")
    print("-" * 70)
    conservation_ok = verify_information_conservation(data, u_epi_recomputed)
    print()

    print("Step 4: Compare to documented value")
    print("-" * 70)
    u_epi_documented = load_documented_penalty()

    if u_epi_documented is not None:
        print(f"Epistemic penalty:")
        print(f"  Documented:  {u_epi_documented:.4f} km/s/Mpc")
        print(f"  Recomputed:  {u_epi_recomputed:.4f} km/s/Mpc")
        diff_penalty = abs(u_epi_recomputed - u_epi_documented)
        print(f"  Difference:  {diff_penalty:.4f} km/s/Mpc")

        if diff_penalty < TOLERANCE_PENALTY:
            print(f"  ✓ PASS (within {TOLERANCE_PENALTY} km/s/Mpc)")
            comparison_pass = True
        else:
            print(f"  ✗ FAIL (exceeds {TOLERANCE_PENALTY} km/s/Mpc)")
            comparison_pass = False
    else:
        print("⚠ WARNING: No documented penalty found for comparison")
        comparison_pass = False

    passed = conservation_ok and comparison_pass

    print()
    print("=" * 70)
    if passed:
        print("✓ PHASE II EPISTEMIC PENALTY: PASS")
    else:
        print("✗ PHASE II EPISTEMIC PENALTY: FAIL")
    print("=" * 70)

    # Save log
    log = {
        'epistemic_penalty': {
            'recomputed': float(u_epi_recomputed),
            'documented': float(u_epi_documented) if u_epi_documented else None,
            'difference': float(diff_penalty) if u_epi_documented else None
        },
        'parameters': {
            'delta_h': float(delta_h),
            'delta_t': float(delta_t),
            'f_systematic': float(f_sys)
        },
        'information_conservation': {
            'passed': conservation_ok
        },
        'passed': passed
    }

    log_file = Path('outputs/logs/phase2_penalty_recomputation.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(log, indent=2))

    print(f"✓ Log saved: {log_file}")

    # Save acceptability tree log
    accept_log = accept_tree.save_log()
    print(f"✓ Acceptability tree log: {accept_log}")

    # Return based on mode
    if args.mode == 'audit':
        return 0
    elif args.mode == 'dry-run':
        return 0
    else:
        return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
