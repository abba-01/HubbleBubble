#!/usr/bin/env python3
"""
RENT Phase III: Master Cross-Validation Harness

Runs all Phase III data fidelity scripts.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0

Usage:
    python rent/phase3_crossvalidation/run_phase3.py [--mode MODE]
"""
import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime
import argparse

PHASE3_SCRIPTS = [
    ('verify_planck', 'rent/phase3_crossvalidation/verify_planck_data.py'),
    ('verify_shoes_anchors', 'rent/phase3_crossvalidation/verify_shoes_anchors.py')
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

def main():
    """Main Phase III harness"""
    parser = argparse.ArgumentParser(description='RENT Phase III: Master Cross-Validation Harness')
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        default=True, help='Disable interactive prompts')
    args = parser.parse_args()

    print("=" * 70)
    print("RENT PHASE III: MASTER CROSS-VALIDATION HARNESS")
    print(f"Mode: {args.mode}")
    print("=" * 70)
    print()

    results = []
    for name, script in PHASE3_SCRIPTS:
        result = run_script(name, script, mode=args.mode, interactive=args.interactive)
        results.append(result)

    # Summary
    print()
    print("=" * 70)
    print("PHASE III SUMMARY")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for r in results if r['passed'])

    for result in results:
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        print(f"  {result['name']:30s} {status}")

    print()
    print(f"Tests: {passed}/{total} passed")

    if passed == total:
        print("✓ PHASE III: COMPLETE PASS")
    else:
        print("✗ PHASE III: FAILURES DETECTED")

    print("=" * 70)

    # Return based on mode
    if args.mode in ['audit', 'dry-run']:
        return 0
    else:
        return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
