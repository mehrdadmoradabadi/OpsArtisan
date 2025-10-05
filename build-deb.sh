#!/bin/bash
# Build a .deb package for OpsArtisan - Fixed for permission issues

set -e

VERSION="2.0.0"
ARCH="all"
PACKAGE_NAME="opsartisan"
BUILD_DIR="deb-pkg"

echo "Building OpsArtisan .deb package v${VERSION}..."

# Clean previous builds with sudo to ensure removal
sudo rm -rf "$BUILD_DIR" 2>/dev/null || true
rm -f *.deb 2>/dev/null || true

# Create build directory in /tmp to avoid permission issues
TEMP_BUILD="/tmp/opsartisan-build-$$"
rm -rf "$TEMP_BUILD"
mkdir -p "$TEMP_BUILD"

# Create package structure with explicit permissions
mkdir -m 0755 "$TEMP_BUILD/DEBIAN"
mkdir -pm 0755 "$TEMP_BUILD/opt/opsartisan"
mkdir -pm 0755 "$TEMP_BUILD/usr/local/bin"
mkdir -pm 0755 "$TEMP_BUILD/etc/bash_completion.d"
mkdir -pm 0755 "$TEMP_BUILD/usr/share/opsartisan/templates"

echo "Copying application files..."
cp -r opsartisan "$TEMP_BUILD/opt/opsartisan/"
cp setup.py "$TEMP_BUILD/opt/opsartisan/"
cp pyproject.toml "$TEMP_BUILD/opt/opsartisan/"
cp requirements.txt "$TEMP_BUILD/opt/opsartisan/"
[ -f README.md ] && cp README.md "$TEMP_BUILD/opt/opsartisan/" || echo "# OpsArtisan" > "$TEMP_BUILD/opt/opsartisan/README.md"

# Copy templates if they exist
if [ -d "templates" ]; then
    echo "Copying templates to /usr/share/opsartisan/templates..."
    TEMPLATE_COUNT=$(find templates -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo "Found $TEMPLATE_COUNT template(s) in templates/"

    if [ "$TEMPLATE_COUNT" -gt 0 ]; then
        cp -rv templates/* "$TEMP_BUILD/usr/share/opsartisan/templates/"
        echo "Templates copied successfully"
    else
        echo "Warning: templates/ directory is empty"
    fi
else
    echo "Warning: No templates directory found in $(pwd)"
    echo "Expected to find: $(pwd)/templates/"
fi

# Create control file
cat > "$TEMP_BUILD/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3 (>= 3.8), python3-pip, python3-venv
Maintainer: Your Name <your.email@example.com>
Description: CLI-first assistant for sysadmins and DevOps engineers
 OpsArtisan helps you generate validated skeletons, configuration files,
 and infrastructure templates quickly through interactive wizards or presets.
EOF

# Create postinst script
cat > "$TEMP_BUILD/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "Setting up OpsArtisan..."

cd /opt/opsartisan
python3 -m venv venv
venv/bin/pip install --upgrade pip > /dev/null 2>&1
venv/bin/pip install -e . > /dev/null 2>&1

cat > /usr/local/bin/opsartisan << 'WRAPPER'
#!/bin/bash
exec /opt/opsartisan/venv/bin/python -m opsartisan.cli "$@"
WRAPPER

chmod +x /usr/local/bin/opsartisan
_OPSARTISAN_COMPLETE=bash_source /usr/local/bin/opsartisan > /etc/bash_completion.d/opsartisan 2>/dev/null || true

echo ""
echo "✓ OpsArtisan installed successfully!"
echo "Run: opsartisan --help"
echo ""
EOF

# Create prerm script
cat > "$TEMP_BUILD/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
rm -f /usr/local/bin/opsartisan
rm -f /etc/bash_completion.d/opsartisan
EOF

# Set permissions using chmod with absolute paths
echo "Setting permissions..."
chmod -R u+rwX,go+rX,go-w "$TEMP_BUILD"
chmod 0755 "$TEMP_BUILD/DEBIAN"
chmod 0644 "$TEMP_BUILD/DEBIAN/control"
chmod 0755 "$TEMP_BUILD/DEBIAN/postinst"
chmod 0755 "$TEMP_BUILD/DEBIAN/prerm"

# Verify
echo "Verifying permissions..."
ls -ld "$TEMP_BUILD/DEBIAN"

# Build the package
echo "Building package..."
fakeroot dpkg-deb --build "$TEMP_BUILD" "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

# Cleanup
rm -rf "$TEMP_BUILD"

echo ""
echo "✓ Package built: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "To install:"
echo "  sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "To verify the package:"
echo "  dpkg-deb --info ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "  dpkg-deb --contents ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""