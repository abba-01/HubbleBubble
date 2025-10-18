#!/usr/bin/env python3
"""
RENT Phase II: Master Re-execution Harness

Runs all Phase II re-execution scripts in sequence.
Aggregates results and generates comprehensive Phase II report.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0
Passes execution mode to all child scripts.

Usage:
    python rent/phase2_reexecution/run_phase2.py [--mode MODE]
"""
import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime
import argparse

PHASE2_SCRIPTS = [
    ('verify_environment', 'rent/phase1_provenance/verify_environment.py'),
    ('recompute_corrections', 'rent/phase2_reexecution/recompute_corrections.py'),
    ('recompute_penalty', 'rent/phase2_reexecution/recompute_penalty.py'),
    ('recompute_merge', 'rent/phase2_reexecution/recompute_merge.py'),
    ('recompute_tensions', 'rent/phase2_reexecution/recompute_tensions.py')
]

def run_script(name, script_path, mode='audit', interactive=True):
    """Run a single validation script with mode"""
    print()
    print("=" * 70)
    print(f"Running: {name}")
    print("=" * 70)
    print()

    cmd = ['python', script_path, '--mode', mode]
    if not interactive:
        cmd.append('--no-interactive')

    result = subprocess.run(
        cmd,
        capture_output=False,
        text=True
    )

    return {
        'name': name,
        'script': script_path,
        'return_code': result.returncode,
        'passed': result.returncode == 0
    }

def aggregate_logs():
    """Aggregate all Phase II logs"""
    logs = {}
    log_files = [
        ('environment', 'outputs/logs/phase1_environment_verification.json'),
        ('corrections', 'outputs/logs/phase2_corrections_recomputation.json'),
        ('penalty', 'outputs/logs/phase2_penalty_recomputation.json'),
        ('merge', 'outputs/logs/phase2_merge_recomputation.json'),
        ('tensions', 'outputs/logs/phase2_tensions_recomputation.json')
    ]

    for name, log_path in log_files:
        path = Path(log_path)
        if path.exists():
            with open(path) as f:
                logs[name] = json.load(f)
        else:
            logs[name] = {'error': 'Log file not found'}

    return logs

def generate_report(results, logs):
    """Generate comprehensive Phase II report"""
    print()
    print("=" * 70)
    print("RENT PHASE II: COMPREHENSIVE REPORT")
    print("=" * 70)
    print()

    # Summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['passed'])
    failed_tests = total_tests - passed_tests

    print(f"Tests run:    {total_tests}")
    print(f"Tests passed: {passed_tests}")
    print(f"Tests failed: {failed_tests}")
    print()

    # Detailed results
    print("Detailed Results:")
    print("-" * 70)
    for result in results:
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        print(f"  {result['name']:30s} {status}")
    print()

    # Key metrics recomputed
    print("Key Metrics (Recomputed vs Documented):")
    print("-" * 70)

    if 'corrections' in logs and logs['corrections'].get('passed'):
        corr = logs['corrections']
        print("Anchor correction:")
        print(f"  Recomputed: {corr['anchor_correction']['recomputed']:.4f} km/s/Mpc")
        print(f"  Documented: {corr['anchor_correction']['documented']:.4f} km/s/Mpc")
        print(f"  Δ:          {corr['anchor_correction']['difference']:.4f} km/s/Mpc")
        print()
        print("P-L correction:")
        print(f"  Recomputed: {corr['pl_correction']['recomputed']:.4f} km/s/Mpc")
        print(f"  Documented: {corr['pl_correction']['documented']:.4f} km/s/Mpc")
        print(f"  Δ:          {corr['pl_correction']['difference']:.4f} km/s/Mpc")
        print()

    if 'penalty' in logs and logs['penalty'].get('passed'):
        pen = logs['penalty']
        print("Epistemic penalty:")
        print(f"  Recomputed: {pen['epistemic_penalty']['recomputed']:.4f} km/s/Mpc")
        print(f"  Documented: {pen['epistemic_penalty']['documented']:.4f} km/s/Mpc")
        print(f"  Δ:          {pen['epistemic_penalty']['difference']:.4f} km/s/Mpc")
        print()

    if 'merge' in logs and logs['merge'].get('passed'):
        merge = logs['merge']
        print("Concordance H₀:")
        print(f"  Recomputed: {merge['concordance']['recomputed_mean']:.4f} ± {merge['concordance']['recomputed_uncertainty']:.4f} km/s/Mpc")
        print(f"  Documented: {merge['concordance']['documented_mean']:.4f} ± {merge['concordance']['documented_uncertainty']:.4f} km/s/Mpc")
        print(f"  Δ mean:     {merge['concordance']['difference_mean']:.4f} km/s/Mpc")
        print(f"  Δ σ:        {merge['concordance']['difference_uncertainty']:.4f} km/s/Mpc")
        print()

    if 'tensions' in logs and logs['tensions'].get('passed'):
        tens = logs['tensions']
        print("Tension reduction:")
        print(f"  Baseline:   {tens['baseline_tension']['recomputed']:.3f}σ")
        print(f"  Final:      {tens['final_tension']['recomputed']:.3f}σ")
        print(f"  Reduction:  {tens['tension_reduction']['recomputed_percent']:.2f}%")
        print()

    # Overall verdict
    print("=" * 70)
    if failed_tests == 0:
        print("✓ PHASE II: COMPLETE PASS")
        print()
        print("All recomputations match documented values within tolerances.")
        print("The analysis is reproducible from first principles.")
    else:
        print("✗ PHASE II: FAILURES DETECTED")
        print()
        print(f"{failed_tests} test(s) failed. Investigate discrepancies in:")
        for result in results:
            if not result['passed']:
                print(f"  - {result['name']}")
        print()
        print("Check individual logs in outputs/logs/ for details.")

    print("=" * 70)

    # Save comprehensive report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests
        },
        'results': results,
        'logs': logs,
        'overall_passed': failed_tests == 0
    }

    report_file = Path('outputs/logs/phase2_comprehensive_report.json')
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2))

    print()
    print(f"✓ Comprehensive report saved: {report_file}")

    return failed_tests == 0

def main():
    """Main Phase II harness"""
    parser = argparse.ArgumentParser(description='RENT Phase II: Master Re-execution Harness')
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        default=True, help='Disable interactive prompts')
    args = parser.parse_args()

    print("=" * 70)
    print("RENT PHASE II: MASTER RE-EXECUTION HARNESS")
    print(f"Mode: {args.mode}")
    print("=" * 70)
    print()
    print("This harness will run all Phase II re-execution scripts:")
    print()
    for name, script in PHASE2_SCRIPTS:
        print(f"  - {name}")
    print()
    print("Each script independently recomputes results from raw data.")
    print("All discrepancies are logged to outputs/logs/")
    print()

    if args.interactive:
        input("Press Enter to begin Phase II re-execution...")
        print()

    # Run all scripts with mode
    results = []
    for name, script in PHASE2_SCRIPTS:
        result = run_script(name, script, mode=args.mode, interactive=args.interactive)
        results.append(result)

    # Aggregate logs
    logs = aggregate_logs()

    # Generate report
    passed = generate_report(results, logs)

    # Return based on mode
    if args.mode in ['audit', 'dry-run']:
        return 0
    else:
        return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
