#!/usr/bin/env python3
"""
RENT Phase IV: Cryptographic Hash Audit

Computes SHA-256 of result files in outputs/ for iron-tight verification.
Generates baseline on first run, verifies on subsequent runs.

Excludes logs/ (regenerated each run) - focuses on RESULT files only.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0

Usage:
    python rent/phase4_audit/audit_hashes.py [--mode MODE]
"""
import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree
import hashlib

def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def should_verify_file(rel_path):
    """Determine if file should be verified (exclude logs and reproducibility metadata)"""
    # Exclude logs (regenerated each run)
    if rel_path.startswith('logs/'):
        return False

    # Exclude reproducibility metadata (these track the verification itself)
    if rel_path.startswith('reproducibility/'):
        return False

    # Verify everything else (results, figures, tables)
    return True

def load_baseline_hashes():
    """Load baseline hashes from SHASUMS256.json"""
    baseline_file = Path('outputs/reproducibility/BASELINE_HASHES.json')
    if not baseline_file.exists():
        return None

    try:
        with open(baseline_file) as f:
            data = json.load(f)
            return data.get('hashes', {})
    except Exception as e:
        print(f"⚠ WARNING: Could not read baseline hashes: {e}")
        return None

def save_baseline_hashes(hashes, metadata):
    """Save baseline hashes for future verification"""
    baseline_file = Path('outputs/reproducibility/BASELINE_HASHES.json')
    baseline_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'RENT_SPEC_VERSION': '1.0.0',
        'created': metadata['timestamp'],
        'purpose': 'Cryptographic baseline for iron-tight reproducibility proof',
        'algorithm': 'SHA-256',
        'file_count': len(hashes),
        'hashes': hashes
    }

    with open(baseline_file, 'w') as f:
        json.dump(data, f, indent=2)

    return baseline_file

def scan_result_files():
    """Scan result files in outputs/ (excluding logs and reproducibility)"""
    outputs_dir = Path('outputs')
    if not outputs_dir.exists():
        return []

    files = []
    for path in outputs_dir.rglob('*'):
        if path.is_file():
            rel_path = str(path.relative_to('outputs'))
            if should_verify_file(rel_path):
                files.append(path)

    return files

def main():
    """Main audit routine"""
    parser = argparse.ArgumentParser(description='RENT Phase IV: Cryptographic Hash Audit')
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        default=True, help='Disable interactive prompts')
    args = parser.parse_args()

    accept_tree = AcceptabilityTree(mode=args.mode, interactive=args.interactive)

    from datetime import datetime
    timestamp = datetime.now().isoformat()

    print("=" * 70)
    print("RENT PHASE IV: CRYPTOGRAPHIC HASH AUDIT")
    print(f"Mode: {args.mode}")
    print("=" * 70)
    print()

    print("Philosophy: Cryptographic proof prevents unfalsifiable claims")
    print("Scope:      Result files only (logs excluded)")
    print()

    print("Step 1: Scan result files")
    print("-" * 70)
    files = scan_result_files()
    print(f"✓ Found {len(files)} result files to verify")
    print()

    if len(files) == 0:
        print("⚠ No result files found - nothing to verify")
        print()
        print("=" * 70)
        print("✓ PHASE IV: PASS (no files to verify)")
        print("=" * 70)
        return 0

    print("Step 2: Compute SHA-256 hashes")
    print("-" * 70)
    computed_hashes = {}
    for file_path in sorted(files):
        rel_path = str(file_path.relative_to('outputs'))
        file_hash = compute_file_hash(file_path)
        computed_hashes[rel_path] = file_hash
        print(f"  {rel_path[:60]:60s} {file_hash[:16]}...")
    print()

    print("Step 3: Load or create baseline")
    print("-" * 70)
    baseline_hashes = load_baseline_hashes()

    if baseline_hashes is None:
        print("ℹ No baseline found - CREATING BASELINE")
        print()
        baseline_file = save_baseline_hashes(computed_hashes, {'timestamp': timestamp})
        print(f"✓ Baseline created: {baseline_file}")
        print()
        print("=" * 70)
        print("✓ PHASE IV: BASELINE CREATED")
        print("=" * 70)
        print()
        print("Next run will verify against this baseline.")
        print("This provides cryptographic proof of reproducibility.")

        # Save log
        log = {
            'RENT_SPEC_VERSION': '1.0.0',
            'mode': args.mode,
            'timestamp': timestamp,
            'action': 'baseline_created',
            'file_count': len(computed_hashes),
            'baseline_file': str(baseline_file),
            'passed': True
        }

        log_file = Path('outputs/logs/phase4_hash_audit.json')
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(json.dumps(log, indent=2))

        return 0

    print(f"✓ Loaded baseline with {len(baseline_hashes)} hashes")
    print()

    print("Step 4: Verify against baseline")
    print("-" * 70)

    matches = []
    mismatches = []
    new_files = []
    missing_files = []

    # Check computed files against baseline
    for rel_path, computed_hash in computed_hashes.items():
        if rel_path in baseline_hashes:
            if computed_hash == baseline_hashes[rel_path]:
                matches.append(rel_path)
                print(f"✓ MATCH       {rel_path}")
            else:
                mismatches.append((rel_path, baseline_hashes[rel_path], computed_hash))
                print(f"✗ MISMATCH    {rel_path}")
                print(f"              Baseline: {baseline_hashes[rel_path]}")
                print(f"              Current:  {computed_hash}")
        else:
            new_files.append(rel_path)
            print(f"⚠ NEW         {rel_path}")

    # Check for files in baseline that are now missing
    for rel_path in baseline_hashes:
        if rel_path not in computed_hashes:
            missing_files.append(rel_path)
            print(f"✗ MISSING     {rel_path}")

    print()
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"  Matches:     {len(matches)}")
    print(f"  Mismatches:  {len(mismatches)}")
    print(f"  New files:   {len(new_files)}")
    print(f"  Missing:     {len(missing_files)}")
    print()

    # Determine pass/fail
    critical_issues = len(mismatches) + len(missing_files)

    if critical_issues == 0:
        if len(new_files) > 0:
            print(f"ℹ {len(new_files)} new files detected (not in baseline)")
            print("  Consider updating baseline if these are expected results")
            print()

        print("=" * 70)
        print("✓ PHASE IV: CRYPTOGRAPHIC VERIFICATION PASSED")
        print("=" * 70)
        print()
        print("All result files match baseline hashes.")
        print("Calculation outputs are cryptographically identical.")
        passed = True
    else:
        print("=" * 70)
        print("✗ PHASE IV: VERIFICATION FAILED")
        print("=" * 70)
        print()
        if len(mismatches) > 0:
            print(f"✗ {len(mismatches)} file(s) have different hashes")
            print("  This means the calculation produced different outputs!")
        if len(missing_files) > 0:
            print(f"✗ {len(missing_files)} file(s) from baseline are missing")
            print("  Expected files were not generated!")
        print()
        print("⚠ This breaks iron-tight reproducibility proof")
        passed = False

    # Save detailed log
    log = {
        'RENT_SPEC_VERSION': '1.0.0',
        'mode': args.mode,
        'timestamp': timestamp,
        'action': 'verification',
        'summary': {
            'matches': len(matches),
            'mismatches': len(mismatches),
            'new_files': len(new_files),
            'missing_files': len(missing_files)
        },
        'mismatches': [
            {'file': f, 'baseline': b, 'current': c}
            for f, b, c in mismatches
        ],
        'new_files': new_files,
        'missing_files': missing_files,
        'passed': passed
    }

    log_file = Path('outputs/logs/phase4_hash_audit.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(log, indent=2))

    print(f"✓ Detailed log: {log_file}")
    print()

    accept_tree.save_log()

    # Mode-aware exit
    if args.mode in ['audit', 'dry-run']:
        return 0  # Audit mode always succeeds
    else:
        return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
