#!/usr/bin/env python3
"""
RENT Discovery Tree

Data fetching hierarchy: check → primary → mirror → local fallback → prompt

SSOT Compliance: RENT_SPEC_VERSION 1.0.0
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class DiscoveryTree:
    """
    Discovery tree for RENT data fetching.

    Execution order: check → primary → mirror → local → prompt
    All attempts logged to outputs/logs/discovery_tree.json
    """

    def __init__(self):
        """Initialize discovery tree"""
        self.config = self._load_config()
        self.endpoints = self._load_endpoints()
        self.log_file = Path('outputs/logs/discovery_tree.json')
        self.attempts = []

    def _load_config(self) -> Dict:
        """Load discovery tree configuration"""
        config_file = Path('rent/config/discovery_tree.json')
        if not config_file.exists():
            print(f"⚠ WARNING: Discovery tree config not found: {config_file}")
            return {'datasets': {}}

        with open(config_file) as f:
            return json.load(f)

    def _load_endpoints(self) -> Dict:
        """Load endpoint configurations"""
        endpoints_file = Path('rent/config/data_endpoints.json')
        if not endpoints_file.exists():
            return {}

        with open(endpoints_file) as f:
            return json.load(f)

    def discover(self, dataset_name: str) -> Tuple[bool, Optional[Path]]:
        """
        Discover and fetch dataset using discovery tree.

        Args:
            dataset_name: Name of dataset from discovery_tree.json

        Returns:
            (success, path_to_file)
        """
        if dataset_name not in self.config['datasets']:
            print(f"✗ Dataset '{dataset_name}' not in discovery tree")
            return False, None

        dataset = self.config['datasets'][dataset_name]

        # Log discovery attempt
        attempt_log = {
            'timestamp': datetime.now().isoformat(),
            'dataset': dataset_name,
            'required': dataset.get('required', False),
            'attempts': []
        }

        # Step 1: Check if file exists locally
        check_path = Path(dataset['check'])
        if check_path.exists():
            print(f"✓ Found {dataset_name} at {check_path}")
            attempt_log['status'] = 'found_local'
            attempt_log['path'] = str(check_path)
            self.attempts.append(attempt_log)
            return True, check_path

        print(f"⚠ {dataset_name} not found at {check_path}")

        # Step 2: Try primary sources
        for source in dataset.get('sources', []):
            success, path = self._fetch_from_url(source, check_path, dataset_name)
            attempt_log['attempts'].append({
                'type': 'primary_source',
                'url': source,
                'success': success
            })

            if success:
                attempt_log['status'] = 'fetched_from_primary'
                attempt_log['path'] = str(path)
                self.attempts.append(attempt_log)
                return True, path

        # Step 3: Try local fallback
        fallback = dataset.get('local_fallback')
        if fallback:
            fallback_path = Path(fallback)
            if fallback_path.exists():
                print(f"✓ Using local fallback: {fallback_path}")
                # Copy to expected location
                check_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy(fallback_path, check_path)

                attempt_log['status'] = 'used_local_fallback'
                attempt_log['path'] = str(check_path)
                self.attempts.append(attempt_log)
                return True, check_path
            else:
                attempt_log['attempts'].append({
                    'type': 'local_fallback',
                    'path': str(fallback_path),
                    'success': False
                })

        # Step 4: Failed
        attempt_log['status'] = 'failed'
        self.attempts.append(attempt_log)

        if dataset.get('required', False):
            print(f"✗ CRITICAL: Required dataset '{dataset_name}' could not be found")
        else:
            print(f"⚠ Optional dataset '{dataset_name}' not available")

        return False, None

    def _fetch_from_url(self, url: str, destination: Path, dataset_name: str) -> Tuple[bool, Optional[Path]]:
        """
        Fetch file from URL.

        Args:
            url: Source URL
            destination: Where to save file
            dataset_name: Dataset name for logging

        Returns:
            (success, path)
        """
        print(f"⚠ Attempting to fetch {dataset_name} from {url}")

        try:
            # Get retry policy
            retry_policy = self.endpoints.get('retry_policy', {})
            max_attempts = retry_policy.get('max_attempts', 1)
            timeout = self.endpoints.get('endpoints', {}).get('timeout_seconds', 30)

            for attempt in range(max_attempts):
                try:
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'RENT/1.0.0 (HubbleBubble Validation Suite)')

                    with urllib.request.urlopen(req, timeout=timeout) as response:
                        data = response.read()

                    # Save to destination
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)

                    print(f"✓ Successfully fetched {dataset_name}")
                    return True, destination

                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                    if attempt < max_attempts - 1:
                        print(f"  ⚠ Attempt {attempt + 1} failed: {e}, retrying...")
                    else:
                        print(f"  ✗ Fetch failed after {max_attempts} attempts: {e}")

            return False, None

        except Exception as e:
            print(f"✗ ERROR fetching from {url}: {e}")
            return False, None

    def save_log(self):
        """Save discovery log to outputs/logs/discovery_tree.json"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        log = {
            'RENT_SPEC_VERSION': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'total_attempts': len(self.attempts),
            'attempts': self.attempts
        }

        self.log_file.write_text(json.dumps(log, indent=2))
        return self.log_file

    def get_summary(self) -> Dict:
        """Get summary of discovery attempts"""
        summary = {
            'total': len(self.attempts),
            'found_local': 0,
            'fetched': 0,
            'fallback': 0,
            'failed': 0
        }

        for attempt in self.attempts:
            status = attempt.get('status', 'failed')
            if status == 'found_local':
                summary['found_local'] += 1
            elif status == 'fetched_from_primary':
                summary['fetched'] += 1
            elif status == 'used_local_fallback':
                summary['fallback'] += 1
            else:
                summary['failed'] += 1

        return summary
