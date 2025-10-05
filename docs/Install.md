# OpsArtisan Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip
- bash shell (for tab completion)

## Quick Install (Recommended)

### 1. Activate your virtual environment
```bash
source venv/bin/activate
```

### 2. Run the installation script
```bash
chmod +x install.sh
./install.sh
```

### 3. Reload your shell
```bash
exec bash
```

### 4. Test it!
```bash
opsartisan --version
opsartisan list
```

Try tab completion:
```bash
opsartisan <TAB><TAB>
```

---

## Manual Installation

If the automated script doesn't work, follow these steps:

### 1. Install the package

From your project directory with activated venv:

```bash
pip install --user -e .
```

Or for development mode:
```bash
pip install -e ".[dev,interactive]"
```

### 2. Add to PATH (if needed)

Check if `opsartisan` is in your PATH:
```bash
which opsartisan
```

If not found, add this to `~/.bashrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then reload:
```bash
source ~/.bashrc
```

### 3. Install Bash Completion

**Option A: Using the built-in command (Recommended)**
```bash
opsartisan completion install bash
```

**Option B: Manual installation**
```bash
# Generate completion script
_OPSARTISAN_COMPLETE=bash_source opsartisan > ~/.bash_completion.d/opsartisan

# Add to .bashrc
echo '[ -f ~/.bash_completion.d/opsartisan ] && source ~/.bash_completion.d/opsartisan' >> ~/.bashrc

# Reload shell
exec bash
```

### 4. Verify Installation

```bash
# Check version
opsartisan --version

# List commands
opsartisan --help

# Test completion (type opsartisan then press TAB twice)
opsartisan <TAB><TAB>
```

---

## Tab Completion Features

Once installed, you get auto-completion for:

- **Commands**: `opsartisan <TAB>` shows all available commands
- **Template IDs**: `opsartisan new <TAB>` shows available templates
- **Preset names**: `opsartisan new template-id --preset <TAB>`
- **Options**: `opsartisan new --<TAB>` shows all flags

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

## Configuration Directories

After installation, OpsArtisan creates:

- `~/.opsartisan/` - Main configuration directory
- `~/.opsartisan/templates/` - User templates
- `~/.opsartisan/plugins/` - Custom plugins
- `~/.opsartisan/presets.json` - Saved presets

---

## Troubleshooting

### Command not found after install

1. Check if it's installed:
   ```bash
   pip show opsartisan
   ```

2. Add `~/.local/bin` to PATH:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Tab completion not working

1. Ensure completion script exists:
   ```bash
   ls -la ~/.bash_completion.d/opsartisan
   ```

2. Check if it's sourced in .bashrc:
   ```bash
   grep "opsartisan" ~/.bashrc
   ```

3. Reinstall completion:
   ```bash
   opsartisan completion install bash
   exec bash
   ```

4. Try manual source:
   ```bash
   source ~/.bash_completion.d/opsartisan
   opsartisan <TAB>
   ```

### Permission denied on install.sh

```bash
chmod +x install.sh
```

### Missing dependencies

Install optional dependencies:
```bash
pip install questionary  # For better interactive prompts
```

---

## Uninstall

To remove OpsArtisan:

```bash
# Remove package
pip uninstall opsartisan

# Remove completion
rm ~/.bash_completion.d/opsartisan

# Remove config (optional)
rm -rf ~/.opsartisan

# Remove from .bashrc
sed -i '/opsartisan/d' ~/.bashrc
```

---

## Next Steps

1. **Create your first template:**
   ```bash
   opsartisan init
   ```

2. **View available templates:**
   ```bash
   opsartisan list
   ```

3. **Generate a project:**
   ```bash
   opsartisan new <template-id>
   ```

4. **View command help:**
   ```bash
   opsartisan --help
   opsartisan new --help
   ```