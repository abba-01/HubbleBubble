#!/bin/bash
#
# HubbleBubble Validation Suite - Automated Execution
#
# Usage:
#   ./run.sh              # Run full validation suite
#   ./run.sh verify       # Run verification protocol only
#   ./run.sh clean        # Clean outputs and rerun
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════════════════"
echo "  HubbleBubble Validation Suite"
echo "  Hubble Tension Concordance Validation Framework"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Parse command
CMD="${1:-full}"

case "$CMD" in
    clean)
        echo "Cleaning outputs..."
        rm -rf outputs/results/*.json
        rm -rf outputs/figures/*
        rm -rf outputs/tables/*
        echo -e "${GREEN}✓ Outputs cleaned${NC}"
        exit 0
        ;;
    verify)
        MODE="verify"
        ;;
    full)
        MODE="full"
        ;;
    *)
        echo -e "${RED}Unknown command: $CMD${NC}"
        echo "Usage: ./run.sh [full|verify|clean]"
        exit 1
        ;;
esac

# Setup virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo "Using existing virtual environment..."
    source .venv/bin/activate
fi

echo ""

# Create output directories
mkdir -p outputs/results outputs/figures outputs/tables outputs/logs outputs/reproducibility

if [ "$MODE" == "full" ]; then
    echo "════════════════════════════════════════════════════════════════════════"
    echo "  FULL VALIDATION SUITE"
    echo "════════════════════════════════════════════════════════════════════════"
    echo ""

    # 1. LOAO
    echo "1. Running LOAO (Leave-One-Anchor-Out)..."
    python3 src/validation/loao.py --out outputs/results/loao.json
    echo -e "${GREEN}✓ LOAO complete${NC}"
    echo ""

    # 2. Grid-Scan
    echo "2. Running Grid-Scan (289 configurations)..."
    python3 src/validation/grids.py --out outputs/results/grids.json
    echo -e "${GREEN}✓ Grid-Scan complete${NC}"
    echo ""

    # 3. Bootstrap (note: using 100 iterations for speed, increase to 10000 for paper)
    echo "3. Running Bootstrap (100 iterations - test run)..."
    python3 src/validation/bootstrap.py --iters 100 --out outputs/results/bootstrap.json
    echo -e "${YELLOW}⚠ Using 100 iterations (test mode). For publication, use --iters 10000${NC}"
    echo -e "${GREEN}✓ Bootstrap complete${NC}"
    echo ""

    # 4. Synthetic Injection
    echo "4. Running Synthetic Injection (100 trials - test run)..."
    python3 src/validation/inject.py --trials 100 --out outputs/results/inject.json
    echo -e "${YELLOW}⚠ Using 100 trials (test mode). For publication, use --trials 2000${NC}"
    echo -e "${GREEN}✓ Injection complete${NC}"
    echo ""

    echo "════════════════════════════════════════════════════════════════════════"
    echo "  FULL VALIDATION COMPLETE"
    echo "════════════════════════════════════════════════════════════════════════"
    echo ""
fi

# Verification Protocol
echo "════════════════════════════════════════════════════════════════════════"
echo "  VERIFICATION PROTOCOL"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# 1. JSON Schema Validation
echo "1. Validating JSON schemas..."
python3 tests/validate_schemas.py
echo ""

# 2. Mathematical Verification
echo "2. Verifying mathematical correctness..."
python3 tests/verify_math.py
echo ""

# 3. LOAO Dual-Gate Check
echo "3. Checking LOAO dual-gate compliance..."
python3 << 'PYEOF'
import json
from scipy.stats import norm

with open("outputs/results/loao.json") as f:
    loao = json.load(f)

print(f"Maximum z_Planck: {loao['max_z_planck']:.4f}σ")
print()
print(f"Gate A (Engineering): {loao['gate_a_engineering']['threshold']}σ")
print(f"  Status: {'✓ PASS' if loao['gate_a_engineering']['passed'] else '✗ MARGINAL'}")
print()
print(f"Gate B (Šidák): {loao['gate_b_sidak']['threshold']:.4f}σ")
print(f"  Status: {'✓ PASS' if loao['gate_b_sidak']['passed'] else '✗ FAIL'}")
PYEOF
echo ""

# 4. Asset Integrity Check
echo "4. Verifying asset integrity..."
if [ -f "outputs/reproducibility/ASSETS_SHASUMS256.txt" ]; then
    cd assets
    sha256sum -c ../outputs/reproducibility/ASSETS_SHASUMS256.txt --quiet && \
        echo -e "${GREEN}✓ All asset checksums verified${NC}" || \
        echo -e "${RED}✗ Asset checksum mismatch${NC}"
    cd ..
else
    echo -e "${YELLOW}⚠ No checksums found, creating...${NC}"
    find assets -type f -print0 | xargs -0 sha256sum | sort > outputs/reproducibility/ASSETS_SHASUMS256.txt
    echo -e "${GREEN}✓ Asset checksums created${NC}"
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════════════"
echo "  EXECUTION SUMMARY"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Results saved to: outputs/results/"
echo "Verification logs: outputs/reproducibility/"
echo ""
echo "Key files:"
echo "  - outputs/results/loao.json       (LOAO scenarios & gates)"
echo "  - outputs/results/grids.json      (Grid-scan 289 configs)"
echo "  - outputs/results/bootstrap.json  (Bootstrap resampling)"
echo "  - outputs/results/inject.json     (Synthetic injection)"
echo "  - VERIFICATION_REPORT.md          (Complete audit trail)"
echo ""
echo -e "${GREEN}✓ HubbleBubble validation complete${NC}"
echo "════════════════════════════════════════════════════════════════════════"

exit 0
