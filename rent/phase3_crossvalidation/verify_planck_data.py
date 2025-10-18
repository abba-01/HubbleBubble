#!/usr/bin/env python3
"""
RENT Phase III: Verify Planck Data Fidelity

Cross-validates Planck H₀ by recomputing from ΛCDM chains.
Verifies 67.27 ± 0.60 km/s/Mpc claim and checks correlation structure.

DATASET PROVENANCE:
- Uses planck_samples_key_params.npz from assets/external/
- If results differ, check if you're using a different Planck release

SSOT Compliance: RENT_SPEC_VERSION 1.0.0

Usage:
    python rent/phase3_crossvalidation/verify_planck_data.py
"""
import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree
import numpy as np
import hashlib

# Tolerance for numerical comparisons
TOLERANCE_MEAN = 0.1  # km/s/Mpc
TOLERANCE_UNC = 0.05  # km/s/Mpc

def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()

def load_planck_chains():
    """Load Planck ΛCDM chains"""
    chains_file = Path('assets/external/planck_samples_key_params.npz')

    if not chains_file.exists():
        print(f"✗ CRITICAL: {chains_file} not found")
        print()
        print("This file should contain Planck ΛCDM posterior samples.")
        print("Expected parameters: H0, omega_b, omega_c, n_s, tau, ...")
        return None

    try:
        data = np.load(chains_file)
        file_hash = compute_file_hash(chains_file)

        print("=" * 70)
        print("PLANCK DATA PROVENANCE")
        print("=" * 70)
        print(f"File: {chains_file}")
        print(f"SHA-256: {file_hash}")
        print(f"Size: {chains_file.stat().st_size} bytes")
        print()

        # List available parameters
        print("Available parameters:")
        for key in data.keys():
            if hasattr(data[key], 'shape'):
                print(f"  {key:20s} shape={data[key].shape}")
            else:
                print(f"  {key:20s}")
        print()

        return data, file_hash
    except Exception as e:
        print(f"✗ ERROR loading Planck chains: {e}")
        return None

def compute_h0_statistics(h0_samples):
    """Compute statistics for H₀ samples"""
    mean = np.mean(h0_samples)
    std = np.std(h0_samples, ddof=1)
    median = np.median(h0_samples)
    q16 = np.percentile(h0_samples, 16)
    q84 = np.percentile(h0_samples, 84)

    print("H₀ Statistics:")
    print("-" * 70)
    print(f"  Mean:   {mean:.3f} km/s/Mpc")
    print(f"  Median: {median:.3f} km/s/Mpc")
    print(f"  Std:    {std:.3f} km/s/Mpc")
    print(f"  16th percentile: {q16:.3f} km/s/Mpc")
    print(f"  84th percentile: {q84:.3f} km/s/Mpc")
    print(f"  68% interval:    [{q16:.3f}, {q84:.3f}] km/s/Mpc")
    print()

    return {
        'mean': mean,
        'std': std,
        'median': median,
        'q16': q16,
        'q84': q84
    }

def check_correlation_structure(data):
    """
    Check correlation structure between ΛCDM parameters.

    Strong correlations between ω_b, ω_c, n_s affect H₀ inference.
    """
    print("Correlation Structure:")
    print("-" * 70)

    # Look for common parameter names
    param_names = {
        'h0': ['H0', 'h0', 'hubble'],
        'omega_b': ['omega_b', 'omegab', 'ombh2'],
        'omega_c': ['omega_c', 'omegac', 'omch2'],
        'n_s': ['n_s', 'ns', 'scalar_spectral_index'],
        'tau': ['tau', 'tau_reio']
    }

    # Find which parameters are available
    available_params = {}
    for param_label, possible_names in param_names.items():
        for name in possible_names:
            if name in data.keys():
                available_params[param_label] = name
                break

    if len(available_params) < 2:
        print("⚠ WARNING: Not enough parameters to compute correlations")
        return None

    # Compute correlation matrix
    param_arrays = []
    param_labels = []
    for label, name in available_params.items():
        arr = data[name]
        if hasattr(arr, 'shape') and len(arr.shape) == 1:
            param_arrays.append(arr)
            param_labels.append(f"{label} ({name})")

    if len(param_arrays) < 2:
        print("⚠ WARNING: Could not construct correlation matrix")
        return None

    # Stack arrays
    stacked = np.column_stack(param_arrays)
    corr_matrix = np.corrcoef(stacked.T)

    print("Correlation matrix:")
    print()
    print("       ", end="")
    for label in param_labels:
        print(f"{label[:8]:>10s}", end="")
    print()

    for i, label_i in enumerate(param_labels):
        print(f"{label_i[:8]:10s}", end="")
        for j in range(len(param_labels)):
            print(f"{corr_matrix[i, j]:10.3f}", end="")
        print()
    print()

    return {
        'matrix': corr_matrix.tolist(),
        'labels': param_labels
    }

def main():
    """Main verification routine"""
    print("=" * 70)
    print("RENT PHASE III: VERIFY PLANCK DATA FIDELITY")
    print("=" * 70)
    print()

    print("Step 1: Load Planck ΛCDM chains")
    print("-" * 70)
    result = load_planck_chains()
    if result is None:
        return 1

    data, file_hash = result
    print()

    print("Step 2: Recompute H₀ from chains")
    print("-" * 70)

    # Find H0 parameter
    h0_param = None
    for key in ['H0', 'h0', 'hubble']:
        if key in data.keys():
            h0_param = key
            break

    if h0_param is None:
        print("✗ CRITICAL: H₀ parameter not found in chains")
        print("Available keys:", list(data.keys()))
        return 1

    h0_samples = data[h0_param]
    if len(h0_samples.shape) > 1:
        # Flatten if multi-dimensional
        h0_samples = h0_samples.flatten()

    print(f"✓ Found H₀ parameter: '{h0_param}'")
    print(f"  Number of samples: {len(h0_samples)}")
    print()

    stats = compute_h0_statistics(h0_samples)
    print()

    print("Step 3: Check correlation structure")
    print("-" * 70)
    correlations = check_correlation_structure(data)
    print()

    print("Step 4: Compare to documented value")
    print("-" * 70)

    # Load documented Planck value
    measurements_file = Path('assets/external/baseline_measurements.json')
    if measurements_file.exists():
        with open(measurements_file) as f:
            measurements = json.load(f)
        planck_documented_mean = measurements.get('planck_h0_mean', None)
        planck_documented_unc = measurements.get('planck_h0_uncertainty', None)
    else:
        planck_documented_mean = 67.27  # Documented value
        planck_documented_unc = 0.60

    print(f"Planck H₀:")
    print(f"  Documented:  {planck_documented_mean:.3f} ± {planck_documented_unc:.3f} km/s/Mpc")
    print(f"  Recomputed:  {stats['mean']:.3f} ± {stats['std']:.3f} km/s/Mpc")

    diff_mean = abs(stats['mean'] - planck_documented_mean)
    diff_unc = abs(stats['std'] - planck_documented_unc)

    print()
    print(f"  Δ mean: {diff_mean:.3f} km/s/Mpc")
    print(f"  Δ σ:    {diff_unc:.3f} km/s/Mpc")

    mean_pass = diff_mean < TOLERANCE_MEAN
    unc_pass = diff_unc < TOLERANCE_UNC

    if mean_pass:
        print(f"  ✓ Mean within {TOLERANCE_MEAN} km/s/Mpc")
    else:
        print(f"  ✗ Mean exceeds {TOLERANCE_MEAN} km/s/Mpc")

    if unc_pass:
        print(f"  ✓ Uncertainty within {TOLERANCE_UNC} km/s/Mpc")
    else:
        print(f"  ✗ Uncertainty exceeds {TOLERANCE_UNC} km/s/Mpc")

    passed = mean_pass and unc_pass

    print()
    print("=" * 70)
    if passed:
        print("✓ PHASE III PLANCK VERIFICATION: PASS")
    else:
        print("✗ PHASE III PLANCK VERIFICATION: FAIL")
    print("=" * 70)

    # Save log
    log = {
        'provenance': {
            'file': str(chains_file),
            'sha256': file_hash
        },
        'statistics': {
            'mean': float(stats['mean']),
            'std': float(stats['std']),
            'median': float(stats['median']),
            'q16': float(stats['q16']),
            'q84': float(stats['q84'])
        },
        'documented': {
            'mean': float(planck_documented_mean),
            'uncertainty': float(planck_documented_unc)
        },
        'comparison': {
            'difference_mean': float(diff_mean),
            'difference_uncertainty': float(diff_unc)
        },
        'correlations': correlations,
        'passed': passed,
        'note': 'If results differ, check if you are using a different Planck data release'
    }

    log_file = Path('outputs/logs/phase3_planck_verification.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(log, indent=2))

    print(f"✓ Log saved: {log_file}")

    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
