"""
Grid-Scan Validation (ΔT × f_systematic)

Tests sensitivity of concordance result to epistemic parameter choices by:
- Scanning ΔT ∈ [1.0, 1.8] (17 points)
- Scanning f_systematic ∈ [0.3, 0.7] (17 points)
- Total: 289 parameter combinations

Acceptance gate: Median z_planck ∈ [0.9, 1.1]σ
"""
import sys
import json
from pathlib import Path
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Gates, Baseline, Epistemic, Seeds
from merge import concordance

def run_grid():
    """
    Run grid-scan over (ΔT, f_systematic) parameter space

    Returns
    -------
    results : dict
        Grid surface and statistics
    passed : bool
        True if gate passed
    """
    np.random.seed(Seeds.master)

    # Define grid
    delta_T_vals = np.linspace(Epistemic.delta_T_min, Epistemic.delta_T_max, 17)
    f_sys_vals = np.linspace(Epistemic.f_sys_min, Epistemic.f_sys_max, 17)

    print("="*70)
    print("GRID-SCAN VALIDATION (ΔT × f_systematic)")
    print("="*70)
    print(f"\nΔT range: [{Epistemic.delta_T_min:.2f}, {Epistemic.delta_T_max:.2f}] (17 points)")
    print(f"f_sys range: [{Epistemic.f_sys_min:.2f}, {Epistemic.f_sys_max:.2f}] (17 points)")
    print(f"Total evaluations: {len(delta_T_vals) * len(f_sys_vals)}")
    print()

    surface = []
    z_planck_vals = []

    for i, dt in enumerate(delta_T_vals):
        for j, fs in enumerate(f_sys_vals):
            res = concordance(dt, fs)

            surface.append({
                "delta_T": float(dt),
                "f_systematic": float(fs),
                "mu_star": res["mu_star"],
                "sigma_star": res["sigma_star"],
                "u_epistemic": res["u_epistemic"],
                "z_planck": res["z_planck"],
                "z_shoes_corr": res["z_shoes_corr"]
            })

            z_planck_vals.append(res["z_planck"])

        # Progress indicator
        if (i + 1) % 5 == 0:
            print(f"  Progress: {i+1}/{len(delta_T_vals)} ΔT values...")

    # Statistics
    z_median = float(np.median(z_planck_vals))
    z_mean = float(np.mean(z_planck_vals))
    z_std = float(np.std(z_planck_vals))
    z_min = float(np.min(z_planck_vals))
    z_max = float(np.max(z_planck_vals))
    z_p25 = float(np.percentile(z_planck_vals, 25))
    z_p75 = float(np.percentile(z_planck_vals, 75))

    # Gate: median ∈ [0.9, 1.1]σ
    passed = (Gates.grid_sigma_planck_median_min <= z_median <= Gates.grid_sigma_planck_median_max)

    print()
    print("="*70)
    print("GRID STATISTICS (z_planck across parameter space)")
    print("="*70)
    print(f"  Median: {z_median:.2f}σ")
    print(f"  Mean:   {z_mean:.2f}σ ± {z_std:.2f}σ")
    print(f"  Range:  [{z_min:.2f}, {z_max:.2f}]σ")
    print(f"  IQR:    [{z_p25:.2f}, {z_p75:.2f}]σ")
    print()
    print(f"GRID GATE: median z_planck ∈ [{Gates.grid_sigma_planck_median_min}, {Gates.grid_sigma_planck_median_max}]σ")
    if passed:
        print(f"✓ PASS: Median {z_median:.2f}σ within gate")
    else:
        print(f"✗ FAIL: Median {z_median:.2f}σ outside gate")
    print("="*70)

    return {
        "grid": {
            "delta_T_range": [Epistemic.delta_T_min, Epistemic.delta_T_max],
            "f_systematic_range": [Epistemic.f_sys_min, Epistemic.f_sys_max],
            "n_points": len(surface)
        },
        "surface": surface,
        "statistics": {
            "z_planck_median": z_median,
            "z_planck_mean": z_mean,
            "z_planck_std": z_std,
            "z_planck_min": z_min,
            "z_planck_max": z_max,
            "z_planck_p25": z_p25,
            "z_planck_p75": z_p75
        },
        "gate": {
            "min": Gates.grid_sigma_planck_median_min,
            "max": Gates.grid_sigma_planck_median_max
        },
        "passed": passed
    }, passed

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Grid-scan validation")
    parser.add_argument("--out", type=str, required=True, help="Output JSON file")
    args = parser.parse_args()

    results, passed = run_grid()

    # Save results
    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {outpath}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)
