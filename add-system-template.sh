#!/bin/bash
# Add a template to system templates directory

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   echo "Usage: sudo ./add-system-template.sh <template-directory>"
   exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: sudo ./add-system-template.sh <template-directory>"
    exit 1
fi

TEMPLATE_DIR="$1"
SYSTEM_DIR="/usr/share/opsartisan/templates"

if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "Error: Template directory not found: $TEMPLATE_DIR"
    exit 1
fi

if [ ! -f "$TEMPLATE_DIR/descriptor.json" ]; then
    echo "Error: No descriptor.json found in $TEMPLATE_DIR"
    exit 1
fi

# Get template ID from descriptor
TEMPLATE_ID=$(python3 -c "import json; print(json.load(open('$TEMPLATE_DIR/descriptor.json'))['id'])")

if [ -z "$TEMPLATE_ID" ]; then
    echo "Error: Could not read template ID from descriptor.json"
    exit 1
fi

DEST="$SYSTEM_DIR/$TEMPLATE_ID"

echo "Installing template '$TEMPLATE_ID' to system..."
echo "Source: $TEMPLATE_DIR"
echo "Destination: $DEST"

if [ -d "$DEST" ]; then
    read -p "Template '$TEMPLATE_ID' already exists. Overwrite? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    rm -rf "$DEST"
fi

cp -r "$TEMPLATE_DIR" "$DEST"
chmod -R 755 "$DEST"

echo "✓ Template '$TEMPLATE_ID' installed successfully!"
echo ""
echo "Available to all users via:"
echo "  opsartisan new $TEMPLATE_ID"