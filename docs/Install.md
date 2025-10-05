# OpsArtisan Installation Guide

## Prerequisites

- Ubuntu/Debian-based Linux distribution
- Python 3.8 or higher (will be installed automatically)
- bash shell (for tab completion)

---

## Installation Methods

### Method 1: System-wide Installation via .deb Package (Recommended)

This method installs OpsArtisan system-wide, making it available to all users without needing Python virtual environments.

#### Step 1: Install Dependencies

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv fakeroot
```

#### Step 2: Build the .deb Package

```bash
cd /path/to/opsartisan
chmod +x build-deb.sh
./build-deb.sh
```

This will create `opsartisan_2.0.0_all.deb` in the current directory.

#### Step 3: Install the Package

```bash
sudo dpkg -i opsartisan_2.0.0_all.deb
```

If you get dependency errors, run:
```bash
sudo apt-get install -f
```

#### Step 4: Verify Installation

```bash
# Check version
opsartisan --version

# List available templates
opsartisan list

# Reload shell for tab completion
exec bash

# Test tab completion
opsartisan <TAB><TAB>
```

**Installation Locations:**
- **Command:** `/usr/local/bin/opsartisan`
- **Application:** `/opt/opsartisan/`
- **System Templates:** `/usr/share/opsartisan/templates/`
- **User Templates:** `~/.opsartisan/templates/`
- **Bash Completion:** `/etc/bash_completion.d/opsartisan`

---

### Method 2: User-level Installation (Development)

For developers or users who want to modify OpsArtisan.

#### Step 1: Clone and Setup Virtual Environment

```bash
git clone https://github.com/<your-username>/opsartisan.git
cd opsartisan
python3 -m venv venv
source venv/bin/activate
```

#### Step 2: Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

#### Step 3: Reload Shell

```bash
exec bash
```

#### Step 4: Verify

```bash
opsartisan --version
opsartisan list
opsartisan <TAB><TAB>
```

**Installation Locations:**
- **Command:** `venv/bin/opsartisan` or `~/.local/bin/opsartisan`
- **User Templates:** `~/.opsartisan/templates/`
- **Bash Completion:** `~/.bash_completion.d/opsartisan`

---

## Tab Completion Features

Once installed, you get auto-completion for:

- **Commands:** `opsartisan <TAB>` → shows all available commands
- **Template IDs:** `opsartisan new <TAB>` → shows available templates
- **Preset names:** `opsartisan new template-id --preset <TAB>` → shows saved presets
- **Options:** `opsartisan new --<TAB>` → shows all flags

### Example Usage:
```bash
# Complete commands
$ opsartisan l<TAB>
list

# Complete template names
$ opsartisan new doc<TAB>
docker-compose  dockerfile

# Complete options
$ opsartisan new --<TAB>
--async-validation  --merge  --out-dir  --preset  --test  --validate  --yes
```

---

## Template Locations

OpsArtisan searches for templates in multiple locations (in order):

1. **Current directory:** `./templates/`
2. **User templates:** `~/.opsartisan/templates/`
3. **System templates:** `/usr/share/opsartisan/templates/` (system-wide installation only)

### Adding System Templates (requires root)

```bash
sudo ./add-system-template.sh /path/to/your-template
```

### Adding User Templates

```bash
opsartisan add-template /path/to/your-template
```

Or manually:
```bash
cp -r /path/to/your-template ~/.opsartisan/templates/
```

---

## Configuration Directories

After installation, OpsArtisan creates:

- `~/.opsartisan/` - Main user configuration directory
- `~/.opsartisan/templates/` - User-specific templates
- `~/.opsartisan/plugins/` - Custom plugins
- `~/.opsartisan/presets.json` - Saved presets

System-wide installation also creates:
- `/usr/share/opsartisan/templates/` - System templates (all users)

---

## Troubleshooting

### Command not found after .deb install

Check if installed:
```bash
dpkg -l | grep opsartisan
```

Verify binary exists:
```bash
ls -la /usr/local/bin/opsartisan
```

Try running directly:
```bash
/usr/local/bin/opsartisan --version
```

### Tab completion not working

1. Verify completion file exists:
   ```bash
   # For system install:
   ls -la /etc/bash_completion.d/opsartisan
   
   # For user install:
   ls -la ~/.bash_completion.d/opsartisan
   ```

2. Manually source it:
   ```bash
   # For system install:
   source /etc/bash_completion.d/opsartisan
   
   # For user install:
   source ~/.bash_completion.d/opsartisan
   ```

3. Reload shell:
   ```bash
   exec bash
   ```

4. Reinstall completion:
   ```bash
   opsartisan completion install bash
   ```

### No templates showing up

Check template locations:
```bash
# System templates (if installed via .deb)
ls /usr/share/opsartisan/templates/

# User templates
ls ~/.opsartisan/templates/

# Local templates
ls ./templates/
```

Verify with:
```bash
opsartisan list
```

### Permission errors with .deb build

The build directory might have wrong permissions. Try:
```bash
umask 0022
./build-deb-fixed.sh
```

### Dependencies missing

Install all required packages:
```bash
sudo apt-get install python3 python3-pip python3-venv fakeroot
```

---

## Uninstall

### Uninstall .deb Package

```bash
sudo apt-get remove opsartisan
sudo apt-get purge opsartisan  # Also removes config files
```

### Uninstall User Installation

```bash
pip uninstall opsartisan
rm ~/.bash_completion.d/opsartisan
rm -rf ~/.opsartisan
sed -i '/opsartisan/d' ~/.bashrc
```

---

## Post-Installation Steps

### 1. Create Your First Template

```bash
opsartisan init
```

Follow the interactive wizard to create a custom template.

### 2. Explore Available Templates

```bash
# List all templates
opsartisan list

# Search for specific templates
opsartisan search docker

# View template details
opsartisan info docker-compose
```

### 3. Generate a Project

```bash
# Interactive mode
opsartisan new <template-id>

# With preset
opsartisan new <template-id> --preset my-preset

# Non-interactive (use defaults)
opsartisan new <template-id> --yes
```

### 4. Save Presets

```bash
# Create a preset
opsartisan save-preset my-config docker-compose

# List saved presets
opsartisan preset list

# Use a preset
opsartisan new docker-compose --preset my-config
```

---

## Advanced Configuration

### Installing Additional Plugins

```bash
# User plugins
mkdir -p ~/.opsartisan/plugins
cp your-plugin.py ~/.opsartisan/plugins/

# System plugins (requires root)
sudo mkdir -p /usr/share/opsartisan/plugins
sudo cp your-plugin.py /usr/share/opsartisan/plugins/
```

### Environment-Specific Configurations

```bash
# Create environment configs
opsartisan env create <template-id> production
opsartisan env create <template-id> staging

# Compare environments
opsartisan env compare <template-id> production staging
```

### Shell Completion for Other Shells

```bash
# For zsh
opsartisan completion install zsh

# For fish
opsartisan completion install fish

# Show completion script (for manual installation)
opsartisan completion show bash
```

---

## Getting Help

```bash
# General help
opsartisan --help

# Command-specific help
opsartisan new --help
opsartisan preset --help

# Show statistics
opsartisan stats

# Validate a template
opsartisan validate <template-id> --check-deps --check-tools
```

---

## Distribution Notes

### For Package Maintainers

The `.deb` package includes:
- Python virtual environment at `/opt/opsartisan/venv/`
- Wrapper script at `/usr/local/bin/opsartisan`
- System templates at `/usr/share/opsartisan/templates/`
- Bash completion at `/etc/bash_completion.d/opsartisan`

### For End Users

The system-wide installation:
- Works without activating virtual environments
- Is available to all users on the system
- Includes prebuilt templates
- Supports user-specific customizations

---

## Next Steps

For advanced usage, template development, and integration with CI/CD pipelines, see the [Integration Guide](Integration.md).