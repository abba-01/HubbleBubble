"""
RENT SSOT Integration Template

Common patterns for integrating acceptability tree and discovery tree
into RENT phase scripts.

This module provides reusable functions for standardized SSOT integration.
"""
import sys
import argparse
from pathlib import Path

# Ensure parent directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acceptability_tree import AcceptabilityTree
from lib.discovery_tree import DiscoveryTree

def create_ssot_parser(description):
    """
    Create standard argument parser for RENT scripts.

    Args:
        description: Script description

    Returns:
        ArgumentParser with standard RENT arguments
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--mode', choices=['strict', 'audit', 'dry-run', 'auto'],
                        default='audit', help='Execution mode (default: audit)')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false',
                        default=True, help='Disable interactive prompts')
    return parser

def initialize_ssot_modules(args):
    """
    Initialize acceptability tree and discovery tree.

    Args:
        args: Parsed arguments from create_ssot_parser()

    Returns:
        (accept_tree, discovery_tree)
    """
    accept_tree = AcceptabilityTree(mode=args.mode, interactive=args.interactive)
    discovery_tree = DiscoveryTree()
    return accept_tree, discovery_tree

def save_ssot_logs(accept_tree, discovery_tree=None):
    """
    Save all SSOT logs.

    Args:
        accept_tree: AcceptabilityTree instance
        discovery_tree: DiscoveryTree instance (optional)

    Returns:
        List of log file paths
    """
    logs = []

    accept_log = accept_tree.save_log()
    logs.append(accept_log)
    print(f"✓ Acceptability tree log: {accept_log}")

    if discovery_tree:
        discovery_log = discovery_tree.save_log()
        logs.append(discovery_log)
        print(f"✓ Discovery tree log: {discovery_log}")

    return logs

def get_exit_code(args, passed):
    """
    Get exit code based on mode and pass/fail status.

    Args:
        args: Parsed arguments
        passed: Boolean indicating if validation passed

    Returns:
        Exit code (0 or 1)
    """
    if args.mode in ['audit', 'dry-run']:
        return 0  # Always succeed in observational modes
    else:
        return 0 if passed else 1
