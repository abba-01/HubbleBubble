#!/usr/bin/env python3
"""
RENT: Rebuild Everything, Nothing Trusted
Master Validation Runner

Philosophy: "If you're not trying to break it, you're not really testing it."
Core Principle: "Spooky is fine. Unfalsifiable is not."

Runs all implemented RENT phases sequentially and generates comprehensive report.

Usage:
    python rent/run_rent.py [--phase N] [--stop-on-fail]

Options:
    --phase N         Run only Phase N (1-7)
    --stop-on-fail    Stop execution if any phase fails
    --quick           Skip interactive prompts
"""
import sys
import subprocess
import argparse
from pathlib import Path
import json
from datetime import datetime

RENT_PHASES = [
    {
        'number': 1,
        'name': 'Provenance Reconstruction',
        'status': 'implemented',
        'runner': 'rent/phase1_provenance/verify_environment.py'
    },
    {
        'number': 2,
        'name': 'Re-execution from Scratch',
        'status': 'implemented',
        'runner': 'rent/phase2_reexecution/run_phase2.py'
    },
    {
        'number': 3,
        'name': 'Data Fidelity Cross-Validation',
        'status': 'implemented',
        'runner': 'rent/phase3_crossvalidation/run_phase3.py'
    },
    {
        'number': 4,
        'name': 'Cryptographic Hash Audit',
        'status': 'implemented',
        'runner': 'rent/phase4_audit/audit_hashes.py'
    },
    {
        'number': 5,
        'name': 'Calculation Validation',
        'status': 'implemented',
        'runner': 'rent/phase5_reimplementation/validate_calculation.py'
    },
    {
        'number': 6,
        'name': 'External Cosmology Cross-Checks',
        'status': 'planned',
        'runner': None
    },
    {
        'number': 7,
        'name': 'Audit Report & Archival',
        'status': 'planned',
        'runner': None
    }
]

def print_banner():
    """Print RENT banner"""
    print()
    print("=" * 70)
    print(" " * 15 + "RENT: Rebuild Everything, Nothing Trusted")
    print("=" * 70)
    print()
    print('Philosophy: "If you\'re not trying to break it,')
    print('             you\'re not really testing it."')
    print()
    print('Core Principle: "Spooky is fine. Unfalsifiable is not."')
    print()
    print("=" * 70)
    print()

def print_phase_status():
    """Print status of all phases"""
    print("RENT Phase Status:")
    print("-" * 70)
    for phase in RENT_PHASES:
        status_symbol = {
            'implemented': '✓',
            'partial': '⚠',
            'planned': '○'
        }.get(phase['status'], '?')

        print(f"  Phase {phase['number']}: {phase['name']:40s} {status_symbol} {phase['status']}")
    print()

def run_phase(phase, mode='audit', interactive=True, stop_on_fail=False):
    """Run a single RENT phase with mode"""
    if phase['runner'] is None:
        print(f"⚠ Phase {phase['number']} ({phase['name']}) is not yet implemented")
        return {'phase': phase['number'], 'passed': None, 'skipped': True}

    runner_path = Path(phase['runner'])
    if not runner_path.exists():
        print(f"✗ ERROR: Runner script not found: {runner_path}")
        return {'phase': phase['number'], 'passed': False, 'skipped': False}

    print()
    print("=" * 70)
    print(f"PHASE {phase['number']}: {phase['name'].upper()}")
    print("=" * 70)
    print()

    cmd = ['python', str(runner_path), '--mode', mode]
    if not interactive:
        cmd.append('--no-interactive')

    result = subprocess.run(
        cmd,
        capture_output=False,
        text=True
    )

    passed = result.returncode == 0

    print()
    print("=" * 70)
    if passed:
        print(f"✓ PHASE {phase['number']}: PASS")
    else:
        print(f"✗ PHASE {phase['number']}: FAIL")
    print("=" * 70)

    if not passed and stop_on_fail:
        print()
        print("⚠ Stopping execution due to phase failure (--stop-on-fail)")
        return {'phase': phase['number'], 'passed': False, 'stopped': True}

    return {'phase': phase['number'], 'passed': passed, 'skipped': False}

def generate_final_report(results):
    """Generate final RENT validation report"""
    print()
    print("=" * 70)
    print("RENT VALIDATION: FINAL REPORT")
    print("=" * 70)
    print()

    total_phases = len([r for r in results if not r.get('skipped', False)])
    passed_phases = len([r for r in results if r.get('passed') == True])
    failed_phases = len([r for r in results if r.get('passed') == False])
    skipped_phases = len([r for r in results if r.get('skipped', False)])

    print("Summary:")
    print(f"  Total phases run: {total_phases}")
    print(f"  Passed:           {passed_phases}")
    print(f"  Failed:           {failed_phases}")
    print(f"  Skipped:          {skipped_phases}")
    print()

    print("Phase Results:")
    print("-" * 70)
    for result in results:
        phase_num = result['phase']
        phase_name = RENT_PHASES[phase_num - 1]['name']

        if result.get('skipped'):
            status = "○ SKIPPED"
        elif result.get('stopped'):
            status = "⚠ STOPPED"
        elif result['passed']:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"

        print(f"  Phase {phase_num}: {phase_name:40s} {status}")
    print()

    # Overall verdict
    print("=" * 70)

    if failed_phases == 0 and total_phases > 0:
        print("✓ RENT VALIDATION: COMPLETE PASS")
        print()
        print("All implemented phases passed validation.")
        print("The analysis is reproducible and adversarially tested.")
        verdict = 'PASS'
    elif failed_phases > 0:
        print("✗ RENT VALIDATION: FAILURES DETECTED")
        print()
        print(f"{failed_phases} phase(s) failed. Investigate:")
        for result in results:
            if result.get('passed') == False:
                phase_name = RENT_PHASES[result['phase'] - 1]['name']
                print(f"  - Phase {result['phase']}: {phase_name}")
        print()
        print("Check individual logs in outputs/logs/ for details.")
        verdict = 'FAIL'
    else:
        print("⚠ RENT VALIDATION: NO PHASES RUN")
        verdict = 'INCOMPLETE'

    print("=" * 70)
    print()

    # Save comprehensive report
    report = {
        'timestamp': datetime.now().isoformat(),
        'verdict': verdict,
        'summary': {
            'total_phases_run': total_phases,
            'passed': passed_phases,
            'failed': failed_phases,
            'skipped': skipped_phases
        },
        'phase_results': results,
        'philosophy': {
            'principle': 'If you\'re not trying to break it, you\'re not really testing it.',
            'core_principle': 'Spooky is fine. Unfalsifiable is not.'
        }
    }

    report_file = Path('outputs/logs/rent_validation_report.json')
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2))

    print(f"✓ Comprehensive RENT report saved: {report_file}")
    print()

    return verdict == 'PASS'

def main():
    """Main RENT validation runner"""
    parser = argparse.ArgumentParser(
        description='RENT: Rebuild Everything, Nothing Trusted - Master Validation Runner'
    )
    parser.add_argument(
        '--mode',
        choices=['strict', 'audit', 'dry-run', 'auto'],
        default='audit',
        help='Execution mode (default: audit)'
    )
    parser.add_argument(
        '--phase',
        type=int,
        choices=range(1, 8),
        help='Run only specific phase (1-7)'
    )
    parser.add_argument(
        '--stop-on-fail',
        action='store_true',
        help='Stop execution if any phase fails'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Skip interactive prompts'
    )
    parser.add_argument(
        '--output-json',
        type=str,
        help='Output JSON summary to file'
    )

    args = parser.parse_args()

    print_banner()
    print_phase_status()

    # Determine which phases to run
    if args.phase:
        phases_to_run = [RENT_PHASES[args.phase - 1]]
        print(f"Running Phase {args.phase} only")
    else:
        phases_to_run = [p for p in RENT_PHASES if p['status'] in ['implemented', 'partial']]
        print(f"Running all implemented phases ({len(phases_to_run)} phases)")

    print()

    if not args.quick:
        print("This will run comprehensive forensic validation.")
        print("All discrepancies will be logged to outputs/logs/")
        print()
        response = input("Continue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Validation cancelled.")
            return 1

    # Run phases with mode
    results = []
    for phase in phases_to_run:
        result = run_phase(
            phase,
            mode=args.mode if hasattr(args, 'mode') else 'audit',
            interactive=not args.quick,
            stop_on_fail=args.stop_on_fail
        )
        results.append(result)

        if result.get('stopped'):
            break

    # Generate final report
    passed = generate_final_report(results)

    # Output JSON if requested
    if args.output_json:
        json_summary = {
            'RENT_SPEC_VERSION': '1.0.0',
            'mode': args.mode,
            'status': 'PASS' if passed else 'FAIL',
            'phases': {str(r['phase']): 'pass' if r.get('passed') else 'fail' if r.get('passed') is False else 'skipped'
                      for r in results},
            'summary': {
                'total_phases': len(results),
                'passed': sum(1 for r in results if r.get('passed')),
                'failed': sum(1 for r in results if r.get('passed') is False),
                'skipped': sum(1 for r in results if r.get('skipped'))
            }
        }

        output_file = Path(args.output_json)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(json_summary, indent=2))
        print(f"✓ JSON summary: {output_file}")

    print()
    print("For detailed diagnostics, see:")
    print("  - outputs/logs/rent_validation_report.json")
    print("  - outputs/logs/phase*_*.json")
    print()
    print("Remember: 'Spooky is fine. Unfalsifiable is not.'")
    print()

    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
