#!/usr/bin/env python3
"""
RENT Acceptability Tree

Graceful failure handling for RENT validation.
Implements policy-driven decision making for environment drift, missing data, etc.

SSOT Compliance: RENT_SPEC_VERSION 1.0.0
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class AcceptabilityTree:
    """
    Acceptability tree for graceful RENT validation failures.

    Reads policy from rent/config/policy.json and logs all decisions
    to outputs/logs/accept_tree_log.json.
    """

    def __init__(self, mode: str = 'audit', interactive: bool = True):
        """
        Initialize acceptability tree.

        Args:
            mode: Execution mode (strict, audit, dry-run, auto)
            interactive: Whether to prompt user for decisions
        """
        self.mode = mode
        self.interactive = interactive
        self.policy = self._load_policy()
        self.log_file = Path('outputs/logs/accept_tree_log.json')
        self.decisions = []

    def _load_policy(self) -> Dict:
        """Load policy configuration"""
        policy_file = Path('rent/config/policy.json')
        if not policy_file.exists():
            print(f"⚠ WARNING: Policy file not found: {policy_file}")
            return self._default_policy()

        with open(policy_file) as f:
            return json.load(f)

    def _default_policy(self) -> Dict:
        """Default policy if config file missing"""
        return {
            'execution_modes': {
                'audit': {
                    'environment_minor': 'log_and_continue',
                    'environment_major': 'log_drift',
                    'data_missing': 'log_and_skip',
                    'hash_mismatch': 'log_and_continue',
                    'logic_error': 'abort',
                    'security_flag': 'abort'
                }
            }
        }

    def handle(self, issue_type: str, details: Dict[str, Any]) -> str:
        """
        Handle an issue using the acceptability tree.

        Args:
            issue_type: Type of issue (environment_minor, environment_major, etc.)
            details: Issue details for logging

        Returns:
            Action to take ('continue', 'skip', 'abort', etc.)
        """
        # Get policy action for this issue type and mode
        mode_policy = self.policy['execution_modes'].get(self.mode, {})
        action = mode_policy.get(issue_type, 'abort')

        # Log decision
        decision = {
            'timestamp': datetime.now().isoformat(),
            'issue_type': issue_type,
            'mode': self.mode,
            'policy_action': action,
            'details': details,
            'interactive': self.interactive
        }

        # Interactive override
        if self.interactive and action in ['prompt_rebuild', 'fetch_or_abort']:
            user_action = self._prompt_user(issue_type, action, details)
            decision['user_override'] = user_action
            action = user_action

        # Map actions to return codes
        action_map = {
            'log_drift': 'continue',
            'log_and_continue': 'continue',
            'log_and_skip': 'skip',
            'log_only': 'continue',
            'log_and_skip_phase': 'skip',
            'fetch': 'fetch',
            'fetch_or_abort': 'fetch',
            'fetch_from_discovery_tree': 'fetch',
            'skip': 'skip',
            'abort': 'abort',
            'override': 'continue',
            'prompt_rebuild': 'skip',  # Default to skip if not interactive
            'verify_source': 'retry'
        }

        decision['resolved_action'] = action_map.get(action, 'abort')
        self.decisions.append(decision)

        return decision['resolved_action']

    def _prompt_user(self, issue_type: str, suggested_action: str, details: Dict) -> str:
        """Prompt user for decision"""
        print()
        print("=" * 70)
        print(f"ACCEPTABILITY TREE: {issue_type.upper()}")
        print("=" * 70)
        print()
        print(f"Suggested action: {suggested_action}")
        print()
        print("Details:")
        for key, value in details.items():
            print(f"  {key}: {value}")
        print()

        if issue_type == 'environment_major':
            print("Options:")
            print("  [c] Continue anyway (log risk)")
            print("  [s] Skip computationally intensive phases")
            print("  [a] Abort validation")
            choice = input("Choice [c/s/a]: ").lower()

            if choice == 'c':
                return 'override'
            elif choice == 's':
                return 'log_and_skip_phase'
            else:
                return 'abort'

        elif issue_type == 'data_missing':
            print("Options:")
            print("  [f] Fetch from discovery tree")
            print("  [s] Skip phases requiring this data")
            print("  [a] Abort validation")
            choice = input("Choice [f/s/a]: ").lower()

            if choice == 'f':
                return 'fetch'
            elif choice == 's':
                return 'skip'
            else:
                return 'abort'

        else:
            choice = input("Continue? [y/N]: ").lower()
            return 'override' if choice == 'y' else 'abort'

    def save_log(self):
        """Save decision log to outputs/logs/accept_tree_log.json"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        log = {
            'RENT_SPEC_VERSION': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'mode': self.mode,
            'interactive': self.interactive,
            'total_decisions': len(self.decisions),
            'decisions': self.decisions
        }

        self.log_file.write_text(json.dumps(log, indent=2))
        return self.log_file

    def get_summary(self) -> Dict:
        """Get summary of decisions made"""
        summary = {
            'total': len(self.decisions),
            'by_type': {},
            'by_action': {}
        }

        for decision in self.decisions:
            issue_type = decision['issue_type']
            action = decision['resolved_action']

            summary['by_type'][issue_type] = summary['by_type'].get(issue_type, 0) + 1
            summary['by_action'][action] = summary['by_action'].get(action, 0) + 1

        return summary
