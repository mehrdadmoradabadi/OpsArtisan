# OpsArtisan Enhancement & Integration Guide

This guide explains how to integrate, extend, and use all new and advanced features in OpsArtisan v2.0+.

---

## New Features Summary

### Core Modules

- **Dependency Resolver:**  
  Handles template dependencies, detects cycles, shows dependency trees
- **Hooks System:**  
  Pre/post generation hooks (shell, chmod, git, info)
- **Marketplace:**  
  Template search, install, update, backup/rollback
- **Plugin Manager:**  
  Extensible system for validators, renderers, Jinja2 filters
- **Environment Manager:**  
  Environment-specific config, variants, .env files, comparison
- **Enhanced Validation:**  
  Context-aware, async, multi-file validation, better error messages

### CLI Additions

- **completion**: Shell completion management
- **plugin**: Plugin management (list, info)
- **env**: Environment config (create, list, compare)
- **stats**: Template and preset statistics
- **validate**: Template validation (deps, tools, tree)

---

## Integration Steps

### 1. Add/Update Files

- Place all new `opsartisan/core` and `opsartisan/utils` modules as described.
- Replace/merge enhancements to `template_manager.py`, `validator.py`, `preset_manager.py`.

### 2. Update CLI

- Import and register new commands from `cli_additions.py` in `cli.py`:
  ```python
  from opsartisan.core.cli_additions import (
      completion, plugin, env, stats, validate_template
  )
  cli.add_command(completion)
  cli.add_command(plugin)
  cli.add_command(env)
  cli.add_command(stats)
  cli.add_command(validate_template, name='validate')
  ```

### 3. Update Config

- Ensure `config.py` defines:
  ```python
  USER_CONFIG_DIR = Path.home() / '.opsartisan'
  USER_TEMPLATES_DIR = USER_CONFIG_DIR / 'templates'
  LOCAL_TEMPLATES_DIR = Path.cwd() / 'templates'
  SYSTEM_TEMPLATES_DIR = Path('/usr/share/opsartisan/templates')
  PRESETS_FILE = USER_CONFIG_DIR / 'presets.json'
  HAS_QUESTIONARY = True # (set based on import)
  ```
- Add new dependencies to `requirements.txt` / `pyproject.toml`:
  - click, jinja2, pyyaml, questionary (optional), tomli (optional for TOML validation)

---

## Feature Usage Examples

### Template Dependencies
```json
{
  "id": "kubernetes-app",
  "dependencies": ["dockerfile"]
}
```
```bash
opsartisan new kubernetes-app
```

### Plugin System
- Place plugin in `~/.opsartisan/plugins/`:
  ```python
  from opsartisan.core.plugin_manager import ValidatorPlugin
  class MyValidator(ValidatorPlugin):
      ...
  ```
- List and inspect plugins:
  ```bash
  opsartisan plugin list
  opsartisan plugin info my-validator
  ```

### Marketplace
```bash
opsartisan template search nginx
opsartisan template install advanced-k8s
opsartisan template install https://github.com/user/template.git
```

### Environment Management
```bash
opsartisan env create my-template dev
opsartisan env compare my-template dev prod
```

### Shell Completion
```bash
opsartisan completion install bash
```

### Preset Management
```bash
opsartisan preset list
opsartisan preset show my-preset
opsartisan preset edit my-preset
opsartisan preset delete my-preset
```

### Incremental Generation
```bash
opsartisan new my-template --merge prompt
```

### Enhanced Validation
```bash
opsartisan new my-template --validate --async-validation
```

### Statistics
```bash
opsartisan stats
```

---

## Advanced Template Usage

- Add `environment_defaults`, `validators`, `hooks`, etc. to your `descriptor.json` for richer template behaviors.
- Use conditions in prompts and outputs for dynamic generation.

---

## Testing & Troubleshooting

- Test each command and feature as described in the CLI and doc usage examples.
- For import/plugin errors: ensure paths, plugin inheritance, and presence of `__init__.py`.
- For missing commands or completion: check PATH, reload shell, and verify installation.
- For validation issues: view enhanced suggestions and documentation links.

---

## Documentation Checklist

- [x] All new files added
- [x] Existing files updated
- [x] Dependencies installed
- [x] CLI commands registered
- [x] Basic tests pass
- [x] Documentation updated
- [x] Example templates created
- [x] Shell completion tested

---

For further details, see the in-code docstrings and the [README.md](../README.md).

**Questions or contributions?**  
Open an issue or PR at:  
https://github.com/yourusername/opsartisan
