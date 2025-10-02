# OpsArtisan Enhancement Integration Guide

This guide explains how to integrate all the new features into your OpsArtisan application.

## 📦 New Files Created

### Core Modules

1. **`opsartisan/core/dependency_resolver.py`** - Complete implementation
   - Dependency graph resolution with topological sort
   - Circular dependency detection
   - Dependency tree visualization

2. **`opsartisan/core/hooks.py`** - Complete implementation
   - Pre/post generation hooks
   - Shell, chmod, and git command execution
   - Common hook patterns library

3. **`opsartisan/core/marketplace.py`** - Complete implementation
   - Template marketplace search and discovery
   - Git-based template installation
   - Template updates with backup/rollback

4. **`opsartisan/core/plugin_manager.py`** - Complete implementation
   - Plugin system for validators, renderers, and filters
   - Dynamic plugin loading from directories
   - Example plugins included (YAMLLint, TOML validator, custom filters)

5. **`opsartisan/core/env_manager.py`** - Complete implementation
   - Environment-specific configurations (dev/staging/prod)
   - Configuration variants generation
   - .env file creation
   - Environment comparison reports

### Utility Modules

6. **`opsartisan/utils/validation_utils.py`** - Complete implementation
   - Enhanced error parsing with suggestions
   - Context-aware error messages with documentation links
   - Multi-file validation (Docker Compose + .env, K8s cross-resource)
   - Quick fixes for common errors

7. **`opsartisan/utils/async_utils.py`** - Complete implementation
   - Parallel validator execution
   - Progress indicators
   - Batch processing utilities

8. **`opsartisan/utils/completion.py`** - Complete implementation
   - Shell completion for bash, zsh, fish
   - Auto-installation scripts
   - Dynamic completion from templates and presets

### Enhanced Existing Files

9. **`opsartisan/core/validator.py`** (Enhanced)
   - Better error messages with context
   - Integration with validation_utils
   - Multi-file validation context
   - Async validation support

10. **`opsartisan/core/template_manager.py`** (Enhanced)
    - Merge strategies for incremental generation
    - Plugin filter integration
    - Template validation
    - Statistics gathering

11. **`opsartisan/core/preset_manager.py`** (Enhanced)
    - Added `delete_preset()` method
    - Added `list_presets()` method

### CLI Additions

12. **`cli_additions.py`** - New CLI commands
    - Completion management
    - Plugin management
    - Environment management
    - Statistics command
    - Enhanced validation

## 🔧 Integration Steps

### Step 1: Add New Files

Copy all new files to their respective locations:

```bash
# Core modules
cp dependency_resolver.py opsartisan/core/
cp hooks.py opsartisan/core/
cp marketplace.py opsartisan/core/
cp plugin_manager.py opsartisan/core/
cp env_manager.py opsartisan/core/

# Utility modules
cp validation_utils.py opsartisan/utils/
cp async_utils.py opsartisan/utils/
cp completion.py opsartisan/utils/
```

### Step 2: Update Existing Files

#### A. Update `validator.py`

Replace the entire file with the enhanced version.

#### B. Update `template_manager.py`

Replace with the enhanced version or merge the new methods:
- `render_template()` with merge_strategy support
- `_handle_existing_file()`
- `_show_diff()`
- `validate_template()`
- `get_template_stats()`

#### C. Update `preset_manager.py`

Add the missing methods:
```python
@staticmethod
def delete_preset(name: str) -> bool:
    # Implementation provided

@staticmethod
def list_presets() -> Dict[str, Any]:
    # Implementation provided
```

### Step 3: Update `cli.py`

Add imports at the top:

```python
from opsartisan.core.plugin_manager import PluginManager
from opsartisan.core.env_manager import EnvironmentManager
from opsartisan.utils.completion import CompletionManager
```

Add the new command groups before `if __name__ == '__main__':`:

```python
# Import commands from cli_additions
from opsartisan.cli_additions import (
    completion,
    plugin,
    env,
    stats,
    validate_template
)

# Add commands to CLI
cli.add_command(completion)
cli.add_command(plugin)
cli.add_command(env)
cli.add_command(stats)
cli.add_command(validate_template, name='validate')
```

### Step 4: Update `config.py`

Ensure these paths are defined:

```python
from pathlib import Path

# Version
__version__ = "2.0.0"

# Directories
USER_CONFIG_DIR = Path.home() / '.opsartisan'
USER_TEMPLATES_DIR = USER_CONFIG_DIR / 'templates'
LOCAL_TEMPLATES_DIR = Path.cwd() / 'templates'
SYSTEM_TEMPLATES_DIR = Path('/usr/share/opsartisan/templates')  # Optional

# Files
PRESETS_FILE = USER_CONFIG_DIR / 'presets.json'

# Feature flags
HAS_QUESTIONARY = True  # Set based on import success
```

### Step 5: Update `requirements.txt`

Add new dependencies:

```txt
click>=8.0
jinja2>=3.0
pyyaml>=6.0
questionary>=1.10  # Optional, for better prompts
tomli>=2.0  # For TOML plugin
```

## 🎯 Feature Usage Examples

### 1. Template Dependencies

```json
{
  "id": "kubernetes-app",
  "dependencies": ["dockerfile"],
  ...
}
```

Usage:
```bash
opsartisan new kubernetes-app  # Auto-checks and prompts for dependencies
```

### 2. Better Error Messages

Automatically provided when validators fail:
```bash
opsartisan new docker-compose --validate
# Shows enhanced errors with suggestions and doc links
```

### 3. Interactive Template Discovery

```bash
opsartisan list --category Infrastructure
opsartisan list --tag kubernetes
opsartisan search "nginx"
```

### 4. Preset Management

```bash
opsartisan preset list
opsartisan preset show my-preset
opsartisan preset edit my-preset
opsartisan preset delete my-preset
```

### 5. Incremental Generation

```bash
opsartisan new my-template --merge prompt  # Ask for each file
opsartisan new my-template --merge skip    # Skip existing
opsartisan new my-template --merge overwrite  # Overwrite all
```

### 6. Template Marketplace

```bash
opsartisan template search kubernetes
opsartisan template install advanced-k8s
opsartisan template install https://github.com/user/template.git
```

### 7. Multi-File Validation

Automatically validates cross-file references:
- Docker Compose + .env files
- Kubernetes Service -> Deployment selectors
- ConfigMap/Secret references

### 8. Environment-Specific Configurations

```bash
opsartisan env create my-template dev
opsartisan env create my-template prod --from-preset base
opsartisan env compare my-template dev staging prod
```

### 9. Post-Generation Hooks

In `descriptor.json`:
```json
{
  "hooks": {
    "post_generation": [
      {
        "type": "git",
        "command": "init",
        "description": "Initialize git repo"
      },
      {
        "type": "chmod",
        "command": "755 deploy.sh",
        "description": "Make script executable"
      }
    ]
  }
}
```

### 10. Async Validation

```bash
opsartisan new my-template --validate --async-validation
# Runs all validators in parallel
```

### 11. Plugin System

Create a plugin in `~/.opsartisan/plugins/my_validator.py`:

```python
from opsartisan.core.plugin_manager import ValidatorPlugin

class MyValidator(ValidatorPlugin):
    @property
    def name(self):
        return "my-validator"
    
    @property
    def version(self):
        return "1.0.0"
    
    def validate(self, file_path, content, context):
        errors = []
        # Your validation logic
        return errors
```

Usage:
```bash
opsartisan plugin list
opsartisan plugin info my-validator
```

### 12. Shell Completion

```bash
opsartisan completion install bash
opsartisan completion install zsh
opsartisan completion install fish
```

### 13. Enhanced Template Info

```bash
opsartisan info kubernetes-app
# Shows: dependencies, required tools, prompts, outputs, examples
```

### 14. Template Validation

```bash
opsartisan validate kubernetes-app --check-deps --check-tools
# Validates template definition and checks dependencies
```

### 15. Statistics

```bash
opsartisan stats
# Shows template counts by category, popular tags, directories
```

## 📝 Updating Existing Templates

To take advantage of new features, update your `descriptor.json`:

```json
{
  "id": "my-template",
  "title": "My Template",
  "version": "2.0.0",
  
  "dependencies": ["base-template"],
  "required_tools": ["docker", "kubectl"],
  
  "environment_defaults": {
    "dev": {
      "debug": true,
      "replicas": 1
    },
    "prod": {
      "debug": false,
      "replicas": 3
    }
  },
  
  "validators": [
    {
      "command": "validate-command",
      "description": "Validate generated files",
      "timeout": 30,
      "file": "output.yml"
    }
  ],
  
  "hooks": {
    "post_generation": [
      {
        "type": "shell",
        "command": "echo 'Done!'",
        "description": "Post-generation message",
        "on_failure": "warn"
      }
    ]
  }
}
```

## 🧪 Testing

Test each feature after integration:

```bash
# Basic functionality
opsartisan list
opsartisan new docker-compose

# New features
opsartisan completion install bash
opsartisan plugin list
opsartisan env create docker-compose dev
opsartisan stats
opsartisan validate docker-compose --check-tools

# Marketplace (mock for now)
opsartisan template search nginx

# Async validation
opsartisan new kubernetes --validate --async-validation

# Merge strategies
mkdir test && cd test
opsartisan new docker-compose
opsartisan new docker-compose --merge prompt  # Should ask about conflicts
```

## 🐛 Troubleshooting

### Import Errors

If you get import errors, check:
1. All files are in correct directories
2. `__init__.py` files exist in each package
3. Python path includes the project root

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### Plugin Not Loading

Check:
1. Plugin file is in `~/.opsartisan/plugins/`
2. Plugin class inherits from correct base class
3. Plugin has required `name` and `version` properties

## 🚀 Next Steps

1. Test all features individually
2. Update documentation
3. Create example templates using new features
4. Gather user feedback
5. Consider adding:
   - Web UI for template discovery
   - Template testing framework
   - CI/CD integration examples
   - Template versioning system

## 📚 Documentation

Update your README with:
- New command examples
- Plugin development guide
- Environment configuration guide
- Troubleshooting section

## ✅ Completion Checklist

- [ ] All new files added
- [ ] Existing files updated
- [ ] Dependencies installed
- [ ] CLI commands registered
- [ ] Basic tests pass
- [ ] Documentation updated
- [ ] Example templates created
- [ ] Shell completion tested