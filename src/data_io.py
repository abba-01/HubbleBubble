"""
Data Acquisition and Checksumming
"""
import os
import json
import hashlib
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
from config import Paths, Seeds

def sha256_file(filepath):
    """Compute SHA-256 hash of file"""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def link_paper3_data():
    """
    Link to existing Paper 3 data instead of re-downloading
    """
    paper3_base = Path("/direction/north/paper-3")

    links = {
        # Planck chains
        "planck/planck_samples_key_params.npz": paper3_base / "results/planck_samples_key_params.npz",
        "planck/planck_chain_statistics.json": paper3_base / "results/planck_chain_statistics.json",
        "planck/planck_uncertainty_decomposition.json": paper3_base / "results/planck_uncertainty_decomposition.json",

        # SH0ES data
        "vizier/shoes_systematic_grid_summary.json": paper3_base / "results/shoes_systematic_grid_summary.json",
        "vizier/shoes_uncertainty_decomposition.json": paper3_base / "results/shoes_uncertainty_decomposition.json",
        "vizier/riess_2016_systematic_grid_210.csv": paper3_base / "data/shoes_data/riess_2016_systematic_grid_210.csv",

        # Systematic analyses
        "external/total_systematic_bias_estimate.json": paper3_base / "results/total_systematic_bias_estimate.json",
        "external/systematic_corrections_applied.json": paper3_base / "results/systematic_corrections_applied.json",
        "external/concordance_h0.json": paper3_base / "results/concordance_h0.json",
        "external/final_tension_analysis.json": paper3_base / "results/final_tension_analysis.json",
    }

    assets_dir = Path(Paths.cache)
    checksums = {}

    print("Linking Paper 3 data to HubbleBubble assets...")

    for rel_path, source in links.items():
        dest = assets_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        if source.exists():
            # Copy file (symlinks don't work well in containers)
            shutil.copy2(source, dest)
            checksum = sha256_file(dest)
            checksums[str(rel_path)] = checksum
            print(f"  ✓ {rel_path}")
        else:
            print(f"  ✗ {rel_path} (source not found: {source})")

    # Save checksums
    repro_dir = Path(Paths.repro)
    repro_dir.mkdir(parents=True, exist_ok=True)

    checksum_file = repro_dir / "SHASUMS256.json"
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    print(f"\n✓ Checksums saved to {checksum_file}")
    print(f"✓ Linked {len(checksums)} files from Paper 3")

    return checksums

def load_planck_stats():
    """Load Planck statistics from cached data"""
    stats_file = Path(Paths.cache) / "planck/planck_chain_statistics.json"
    with open(stats_file) as f:
        return json.load(f)

def load_shoes_grid():
    """Load SH0ES systematic grid (210 configs)"""
    grid_file = Path(Paths.cache) / "vizier/riess_2016_systematic_grid_210.csv"
    return pd.read_csv(grid_file)

def load_shoes_stats():
    """Load SH0ES statistics from cached data"""
    stats_file = Path(Paths.cache) / "vizier/shoes_uncertainty_decomposition.json"
    with open(stats_file) as f:
        return json.load(f)

def load_systematic_corrections():
    """Load systematic correction results"""
    corr_file = Path(Paths.cache) / "external/systematic_corrections_applied.json"
    with open(corr_file) as f:
        return json.load(f)

def verify_checksums():
    """Verify data integrity against stored checksums"""
    checksum_file = Path(Paths.repro) / "SHASUMS256.json"

    if not checksum_file.exists():
        print("⚠ No checksums found. Run with --fetch first.")
        return False

    with open(checksum_file) as f:
        stored = json.load(f)

    assets_dir = Path(Paths.cache)
    verified = 0
    failed = []

    for rel_path, stored_hash in stored.items():
        filepath = assets_dir / rel_path
        if filepath.exists():
            current_hash = sha256_file(filepath)
            if current_hash == stored_hash:
                verified += 1
            else:
                failed.append((rel_path, "hash mismatch"))
        else:
            failed.append((rel_path, "file missing"))

    print(f"\nChecksum verification: {verified}/{len(stored)} passed")

    if failed:
        print("\n✗ FAILED:")
        for path, reason in failed:
            print(f"  {path}: {reason}")
        return False

    print("✓ All checksums verified")
    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Data acquisition for HubbleBubble")
    parser.add_argument("--fetch", action="store_true", help="Link Paper 3 data")
    parser.add_argument("--verify", action="store_true", help="Verify checksums")
    parser.add_argument("--cache-dir", default="assets", help="Cache directory")

    args = parser.parse_args()

    if args.fetch:
        checksums = link_paper3_data()
        print(f"\n✓ Data acquisition complete ({len(checksums)} files)")

    if args.verify:
        success = verify_checksums()
        exit(0 if success else 1)

    if not (args.fetch or args.verify):
        print("Use --fetch to link data or --verify to check checksums")
