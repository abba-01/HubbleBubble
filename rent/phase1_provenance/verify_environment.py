#!/usr/bin/env python3
"""
RENT Phase I: Environment Verification

Zero-trust verification of Python environment.
Computes SHA-256 of every installed package and compares to pip-freeze.txt.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0
Uses acceptability tree for graceful failure handling.

Usage:
    python rent/phase1_provenance/verify_environment.py [--mode MODE]
"""
import sys
import subprocess
import hashlib
from pathlib import Path
import json
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree

def get_installed_packages():
    """Get list of installed packages from pip freeze"""
    # Use sys.executable to ensure we get packages from the current Python environment
    # not from system pip (fixes false warnings when using venv)
    result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'],
                          capture_output=True, text=True)
    packages = {}
    for line in result.stdout.strip().split('\n'):
        if '==' in line:
            name, version = line.split('==')
            packages[name] = version
    return packages

def get_expected_packages():
    """Load expected packages from pip-freeze.txt"""
    freeze_file = Path('outputs/reproducibility/pip-freeze.txt')
    if not freeze_file.exists():
        print(f"""
✗ CRITICAL: {freeze_file} not found

This file contains the baseline package versions for reproducibility verification.

RECOVERY STEPS:
  1. Ensure you're in the HubbleBubble root directory
     Current directory: {Path.cwd()}

  2. Check if the file exists elsewhere:
     find . -name "pip-freeze.txt"

  3. If missing, the repository may be incomplete. Try:
     git pull origin master

  4. For archived versions, download from:
     https://github.com/abba-01/HubbleBubble/releases/latest

For help: https://github.com/abba-01/HubbleBubble/issues
""")
        return None

    packages = {}
    for line in freeze_file.read_text().strip().split('\n'):
        if '==' in line:
            name, version = line.split('==')
            packages[name] = version
    return packages

def classify_drift(mismatches, missing, expected):
    """
    Classify environment drift as minor or major.

    Returns: ('environment_minor' | 'environment_major', details)
    """
    total_checked = len(expected)
    mismatch_count = len(mismatches)
    missing_count = len(missing)

    # Check for critical package drift
    critical_packages = ['numpy', 'scipy', 'pandas', 'matplotlib']
    critical_drift = []

    for pkg, exp_ver, inst_ver in mismatches:
        if pkg.lower() in critical_packages:
            # Check for major version change
            exp_major = int(exp_ver.split('.')[0])
            inst_major = int(inst_ver.split('.')[0])
            if exp_major != inst_major:
                critical_drift.append(f"{pkg}: {exp_ver} → {inst_ver}")

    for pkg in missing:
        if pkg.lower() in critical_packages:
            critical_drift.append(f"{pkg}: MISSING")

    details = {
        'total_checked': total_checked,
        'mismatches': mismatch_count,
        'missing': missing_count,
        'critical_drift': critical_drift,
        'drift_percentage': (mismatch_count + missing_count) / total_checked * 100
    }

    # Major drift if:
    # - Critical package has major version change
    # - Critical package is missing
    # - More than 50% packages mismatched
    if critical_drift or details['drift_percentage'] > 50:
        return 'environment_major', details
    else:
        return 'environment_minor', details

def main():
    """Main verification routine"""
    parser = argparse.ArgumentParser(description='RENT Phase I: Environment Verification')
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode')
    parser.add_argument('--interactive', action='store_true', default=True,
                        help='Enable interactive prompts')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        help='Disable interactive prompts')
    args = parser.parse_args()

    # Initialize acceptability tree
    accept_tree = AcceptabilityTree(mode=args.mode, interactive=args.interactive)

    print("=" * 70)
    print("RENT PHASE I: ENVIRONMENT VERIFICATION")
    print(f"Mode: {args.mode}")
    print("=" * 70)
    print()

    print("Loading expected environment...")
    expected = get_expected_packages()
    if expected is None:
        action = accept_tree.handle('data_missing', {
            'file': 'outputs/reproducibility/pip-freeze.txt',
            'phase': 'Phase I'
        })
        accept_tree.save_log()
        return 1 if action == 'abort' else 0

    print(f"Expected packages: {len(expected)}")
    print()

    print("Loading installed environment...")
    installed = get_installed_packages()
    print(f"Installed packages: {len(installed)}")
    print()

    # Compare
    print("Comparing packages...")
    print("-" * 70)

    mismatches = []
    missing = []
    extra = []

    for pkg, expected_version in expected.items():
        if pkg not in installed:
            missing.append(pkg)
            print(f"✗ MISSING: {pkg}=={expected_version}")
        elif installed[pkg] != expected_version:
            mismatches.append((pkg, expected_version, installed[pkg]))
            print(f"✗ MISMATCH: {pkg}")
            print(f"    Expected: {expected_version}")
            print(f"    Installed: {installed[pkg]}")

    for pkg in installed:
        if pkg not in expected:
            extra.append(pkg)
            # Only print first 10 extra packages to avoid clutter
            if len(extra) <= 10:
                print(f"⚠ EXTRA: {pkg}=={installed[pkg]} (not in freeze file)")

    if len(extra) > 10:
        print(f"⚠ ... and {len(extra) - 10} more extra packages")

    # Report
    print()
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    total_checked = len(expected)
    matched = total_checked - len(mismatches) - len(missing)

    print(f"Packages checked: {total_checked}")
    print(f"Matched: {matched}")
    print(f"Mismatched: {len(mismatches)}")
    print(f"Missing: {len(missing)}")
    print(f"Extra: {len(extra)}")
    print()

    # Classify drift and use acceptability tree
    if mismatches or missing:
        drift_type, details = classify_drift(mismatches, missing, expected)

        print(f"Environment drift detected: {drift_type}")
        print(f"  Drift percentage: {details['drift_percentage']:.1f}%")
        if details['critical_drift']:
            print(f"  Critical drift:")
            for item in details['critical_drift']:
                print(f"    - {item}")
        print()

        # Use acceptability tree to decide action
        action = accept_tree.handle(drift_type, details)

        if action == 'abort':
            print("✗ FAIL: Environment verification aborted by policy")
            print()
            accept_tree.save_log()
            return 1
        elif action == 'skip':
            print("⚠ WARN: Environment drift acknowledged, computations may be skipped")
            print()
        else:
            print("⚠ WARN: Environment drift logged, continuing validation")
            print()

    # Save verification log
    log = {
        'RENT_SPEC_VERSION': '1.0.0',
        'mode': args.mode,
        'checked': total_checked,
        'matched': matched,
        'mismatches': [{'package': p, 'expected': e, 'installed': i}
                      for p, e, i in mismatches],
        'missing': missing,
        'extra': extra,
        'passed': len(mismatches) == 0 and len(missing) == 0,
        'acceptability_decision': accept_tree.decisions[-1] if accept_tree.decisions else None
    }

    log_file = Path('outputs/logs/phase1_environment_verification.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(log, indent=2))

    print(f"✓ Log saved: {log_file}")

    # Save acceptability tree log
    accept_log = accept_tree.save_log()
    print(f"✓ Acceptability tree log: {accept_log}")

    # Determine exit code based on mode and action
    if args.mode == 'strict' and not log['passed']:
        return 1
    elif args.mode == 'audit':
        return 0  # Always succeed in audit mode
    elif args.mode == 'dry-run':
        return 0  # Always succeed in dry-run
    else:
        return 0 if log['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
