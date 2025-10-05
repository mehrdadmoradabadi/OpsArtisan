#!/bin/bash
# OpsArtisan Installation Script for Ubuntu (User-level)

set -e

echo "==============================================="
echo "  OpsArtisan Installation Script"
echo "==============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo -e "${GREEN}Virtual environment detected: $VIRTUAL_ENV${NC}"
    INSTALL_CMD="pip install -e ."
    BIN_PATH="$VIRTUAL_ENV/bin"
else
    echo -e "${YELLOW}Not in a virtual environment - installing to user site${NC}"
    INSTALL_CMD="pip install --user -e ."
    BIN_PATH="$HOME/.local/bin"
fi

# Step 1: Install the package
echo -e "${GREEN}[1/4]${NC} Installing OpsArtisan package..."
$INSTALL_CMD

# Check if installation was successful
if ! command -v opsartisan &> /dev/null; then
    echo -e "${YELLOW}Warning: 'opsartisan' command not found in PATH${NC}"

    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo ""
        echo "Add this to your ~/.bashrc:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        read -p "Add to ~/.bashrc now? [Y/n]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
                echo -e "${GREEN}✓${NC} Added to ~/.bashrc"
            else
                echo -e "${YELLOW}✓${NC} Already in ~/.bashrc"
            fi
            export PATH="$HOME/.local/bin:$PATH"
        fi
    fi
fi

# Step 2: Create config directories
echo -e "${GREEN}[2/4]${NC} Creating configuration directories..."
mkdir -p ~/.opsartisan/templates
mkdir -p ~/.opsartisan/plugins
mkdir -p ~/.bash_completion.d

echo -e "${GREEN}✓${NC} Created ~/.opsartisan/"

# Step 3: Install bash completion
echo -e "${GREEN}[3/4]${NC} Installing bash completion..."

# Generate completion script using Click's built-in completion
_OPSARTISAN_COMPLETE=bash_source opsartisan > ~/.bash_completion.d/opsartisan 2>/dev/null || {
    echo -e "${YELLOW}Warning: Could not generate completion automatically${NC}"
    echo "Run manually later: opsartisan completion install bash"
}

# Add completion sourcing to .bashrc if not already there
if ! grep -q "source ~/.bash_completion.d/opsartisan" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# OpsArtisan completion" >> ~/.bashrc
    echo "[ -f ~/.bash_completion.d/opsartisan ] && source ~/.bash_completion.d/opsartisan" >> ~/.bashrc
    echo -e "${GREEN}✓${NC} Added completion to ~/.bashrc"
else
    echo -e "${YELLOW}✓${NC} Completion already in ~/.bashrc"
fi

# Step 4: Verify installation
echo -e "${GREEN}[4/4]${NC} Verifying installation..."

if command -v opsartisan &> /dev/null; then
    VERSION=$(opsartisan --version 2>&1 | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
    echo -e "${GREEN}✓${NC} OpsArtisan ${VERSION} installed successfully!"
else
    echo -e "${RED}✗${NC} Installation verification failed"
    exit 1
fi

echo ""
echo "==============================================="
echo -e "${GREEN}  Installation Complete!${NC}"
echo "==============================================="
echo ""
echo "To start using OpsArtisan:"
echo "  1. Reload your shell: exec bash"
echo "  2. Test tab completion: opsartisan <TAB>"
echo "  3. View available commands: opsartisan --help"
echo "  4. Create your first template: opsartisan init"
echo ""
echo "Configuration directory: ~/.opsartisan/"
echo ""