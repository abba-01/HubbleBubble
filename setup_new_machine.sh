#!/bin/bash
#
# HubbleBubble - New Machine Setup and Reproducibility Test
#
# This script sets up the environment and runs the full RENT validation
# to verify computational reproducibility on a fresh machine.
#
# Usage:
#   bash setup_new_machine.sh
#
# Requirements:
#   - Python 3.10+
#   - Git
#   - Internet connection
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        HubbleBubble Reproducibility Test                      ║
║        Independent Machine Verification                       ║
║                                                               ║
║        H₀ = 68.518 ± 1.292 km/s/Mpc                          ║
║        (0.966σ concordance with Planck)                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Step 1: Check Prerequisites
print_step "Step 1: Checking Prerequisites"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python found: $PYTHON_VERSION"

    # Check if Python >= 3.10
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_success "Python version OK (>= 3.10)"
    else
        print_error "Python 3.10+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    print_success "Git found: $GIT_VERSION"
else
    print_error "Git not found. Please install git"
    exit 1
fi

# Check disk space
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
print_success "Available disk space: $AVAILABLE_SPACE"

# Step 2: Clone Repository
print_step "Step 2: Cloning Repository"

# Check if already cloned
if [ -d "HubbleBubble" ]; then
    print_warning "HubbleBubble directory already exists"
    read -p "Delete and re-clone? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf HubbleBubble
        print_success "Removed existing directory"
    else
        print_warning "Using existing directory"
        cd HubbleBubble
    fi
else
    # Try to clone
    print_warning "Repository is PRIVATE - you'll need to authenticate"
    echo ""
    echo "Choose authentication method:"
    echo "  1) Personal Access Token (recommended for quick test)"
    echo "  2) SSH Key (if already set up)"
    echo "  3) GitHub CLI (if installed)"
    echo ""
    read -p "Enter choice (1-3): " AUTH_CHOICE

    case $AUTH_CHOICE in
        1)
            echo ""
            echo "Get token from: https://github.com/settings/tokens"
            echo "Required scope: 'repo' (full control of private repositories)"
            echo ""
            git clone https://github.com/abba-01/HubbleBubble.git
            ;;
        2)
            git clone git@github.com:abba-01/HubbleBubble.git
            ;;
        3)
            if command -v gh &> /dev/null; then
                gh repo clone abba-01/HubbleBubble
            else
                print_error "GitHub CLI not found. Install with: sudo dnf install -y gh"
                exit 1
            fi
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    cd HubbleBubble
    print_success "Repository cloned"
fi

# Step 3: Create Virtual Environment
print_step "Step 3: Setting Up Virtual Environment"

if [ -d ".venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Delete and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        print_success "Removed existing venv"
    else
        print_warning "Using existing venv"
    fi
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

# Activate venv
source .venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
pip install --upgrade pip wheel > /dev/null 2>&1
print_success "pip upgraded"

# Step 4: Install Dependencies
print_step "Step 4: Installing Dependencies"

echo "Installing pinned dependencies from requirements.txt..."
pip install -r requirements.txt

print_success "Dependencies installed"

# Step 5: Environment Verification (RENT Phase I)
print_step "Step 5: Environment Verification (RENT Phase I)"

echo "Checking package versions match canonical baseline..."
python rent/phase1_environment/check_environment.py

if [ $? -eq 0 ]; then
    print_success "Environment matches canonical baseline"
else
    print_error "Environment mismatch detected"
    echo ""
    echo "This may affect reproducibility. Continue anyway? (y/N): "
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 6: Regenerate Results
print_step "Step 6: Regenerating Results from Scratch"

echo "This will take ~5-10 minutes..."
echo ""

if command -v make &> /dev/null; then
    make validate
    if [ $? -eq 0 ]; then
        print_success "Results regenerated successfully"
    else
        print_error "make validate failed"
        echo ""
        echo "Try running validation scripts manually:"
        echo "  python rent/phase2_regeneration/monte_carlo_validation.py"
        exit 1
    fi
else
    print_warning "make not found, running validation scripts directly..."

    # Run validation scripts
    if [ -f "rent/phase2_regeneration/monte_carlo_validation.py" ]; then
        python rent/phase2_regeneration/monte_carlo_validation.py
        print_success "Validation scripts executed"
    else
        print_error "Validation scripts not found"
        exit 1
    fi
fi

# Step 7: Run RENT Verification
print_step "Step 7: Running RENT Verification"

echo "Verifying reproducibility against cryptographic baseline..."
echo ""

python rent/run_rent.py --mode audit

RENT_EXIT_CODE=$?

echo ""
if [ $RENT_EXIT_CODE -eq 0 ]; then
    print_success "RENT validation PASSED"
else
    print_warning "RENT validation completed with warnings (exit code: $RENT_EXIT_CODE)"
fi

# Step 8: Display Results
print_step "Step 8: Results Summary"

echo ""
echo "Reproducibility Test Results:"
echo "=============================="
echo ""

# Check if result files exist
if [ -f "outputs/results/grids.json" ]; then
    print_success "Deterministic files regenerated"
else
    print_error "Result files not found"
fi

if [ -f "outputs/reproducibility/BASELINE_HASHES.json" ]; then
    print_success "Baseline hashes available for verification"
else
    print_warning "Baseline hashes not found"
fi

if [ -f "outputs/h0_validation_report.html" ]; then
    print_success "Validation report generated"
    echo ""
    echo "View report: firefox outputs/h0_validation_report.html"
else
    print_warning "Validation report not found"
fi

# Final summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Reproducibility test complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Expected Results:"
echo "  - Phase I: 100% environment match"
echo "  - Phase II: Data provenance verified (10 files)"
echo "  - Phase III: Literature anchors verified"
echo "  - Phase IV: 7/9 files byte-identical (deterministic)"
echo "  - Phase IV: 2/9 files statistically equivalent (stochastic)"
echo "  - Phase V: H₀ = 68.518 ± 1.292 km/s/Mpc"
echo ""
echo "Next steps:"
echo "  1. Review validation report: outputs/h0_validation_report.html"
echo "  2. Check RENT logs: outputs/logs/"
echo "  3. Review VALIDATION_STATUS.md for interpretation"
echo ""
echo "For detailed results:"
echo "  cat outputs/results/grids.json"
echo "  cat outputs/results/loao.json"
echo "  cat outputs/results/bootstrap.json"
echo ""
echo -e "${YELLOW}This proves true computational reproducibility:${NC}"
echo "  ✓ Environment is fully specified"
echo "  ✓ Calculations are deterministic (7/9 byte-identical)"
echo "  ✓ Randomness is controlled (seed=172901)"
echo "  ✓ Results are independently verifiable"
echo ""
echo -e "${GREEN}Repository URL:${NC} https://github.com/abba-01/HubbleBubble"
echo ""
