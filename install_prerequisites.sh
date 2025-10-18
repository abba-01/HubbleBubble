#!/bin/bash
#
# HubbleBubble - Install Prerequisites
#
# This script detects your OS and installs the required prerequisites:
#   - Python 3.10+
#   - Git
#   - Make (optional, but recommended)
#
# Usage:
#   bash install_prerequisites.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}HubbleBubble - Installing Prerequisites${NC}\n"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo -e "${RED}Cannot detect OS. Please install manually:${NC}"
    echo "  - Python 3.10+"
    echo "  - Git"
    exit 1
fi

echo -e "${BLUE}Detected OS: $PRETTY_NAME${NC}\n"

# Check if running as root/sudo for Linux
if [[ "$OSTYPE" == "linux-gnu"* ]] && [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}This script needs sudo privileges to install packages.${NC}"
    echo "Please run: sudo bash $0"
    exit 1
fi

# Install based on OS
case $OS in
    rocky|rhel|centos|fedora|almalinux)
        echo -e "${BLUE}Installing for RHEL-based system...${NC}\n"
        dnf install -y python3 python3-pip git make wget
        ;;

    ubuntu|debian|linuxmint)
        echo -e "${BLUE}Installing for Debian-based system...${NC}\n"
        apt update
        apt install -y python3 python3-pip python3-venv git make wget
        ;;

    arch|manjaro)
        echo -e "${BLUE}Installing for Arch-based system...${NC}\n"
        pacman -Sy --noconfirm python python-pip git make wget
        ;;

    opensuse*|sles)
        echo -e "${BLUE}Installing for openSUSE/SLES...${NC}\n"
        zypper install -y python3 python3-pip git make wget
        ;;

    alpine)
        echo -e "${BLUE}Installing for Alpine Linux...${NC}\n"
        apk add --no-cache python3 py3-pip git make wget
        ;;

    *)
        echo -e "${RED}Unsupported OS: $OS${NC}"
        echo "Please install manually:"
        echo "  - Python 3.10+"
        echo "  - Git"
        echo "  - Make"
        echo "  - wget"
        exit 1
        ;;
esac

# Verify installations
echo -e "\n${BLUE}Verifying installations...${NC}\n"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python installed: $PYTHON_VERSION${NC}"

    # Check version
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo -e "${GREEN}✓ Python version OK (>= 3.10)${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: Python 3.10+ recommended, found $PYTHON_VERSION${NC}"
    fi
else
    echo -e "${RED}✗ Python installation failed${NC}"
    exit 1
fi

if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    echo -e "${GREEN}✓ Git installed: $GIT_VERSION${NC}"
else
    echo -e "${RED}✗ Git installation failed${NC}"
    exit 1
fi

if command -v make &> /dev/null; then
    echo -e "${GREEN}✓ Make installed${NC}"
else
    echo -e "${YELLOW}⚠ Make not found (optional)${NC}"
fi

if command -v wget &> /dev/null; then
    echo -e "${GREEN}✓ wget installed${NC}"
else
    echo -e "${YELLOW}⚠ wget not found (optional)${NC}"
fi

# Check disk space
AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -ge 2 ]; then
    echo -e "${GREEN}✓ Disk space available: ${AVAILABLE_GB}GB${NC}"
else
    echo -e "${YELLOW}⚠ Low disk space: ${AVAILABLE_GB}GB (2GB recommended)${NC}"
fi

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Prerequisites installed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo "Next steps:"
echo ""
echo "1. Clone the repository:"
echo "   git clone https://github.com/abba-01/HubbleBubble.git"
echo "   cd HubbleBubble"
echo ""
echo "2. Run the setup script:"
echo "   bash setup_new_machine.sh"
echo ""
