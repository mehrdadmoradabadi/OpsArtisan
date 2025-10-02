"""Plugin system for custom validators and renderers."""

import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional, Type
import click
from abc import ABC, abstractmethod


class PluginBase(ABC):
    """Base class for all plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass


class ValidatorPlugin(PluginBase):
    """Base class for validator plugins."""

    @abstractmethod
    def validate(self, file_path: Path, content: str, context: Dict[str, Any]) -> List[str]:
        """
        Validate a file.

        Args:
            file_path: Path to the file being validated
            content: File content
            context: Additional context (template answers, related files, etc.)

        Returns:
            List of validation error messages (empty if valid)
        """
        pass


class RendererPlugin(PluginBase):
    """Base class for renderer plugins."""

    @abstractmethod
    def render(self, template_content: str, context: Dict[str, Any]) -> str:
        """
        Render a template.

        Args:
            template_content: Template content
            context: Rendering context (variables)

        Returns:
            Rendered content
        """
        pass


class FilterPlugin(PluginBase):
    """Base class for Jinja2 filter plugins."""

    @abstractmethod
    def get_filters(self) -> Dict[str, Callable]:
        """
        Get custom Jinja2 filters.

        Returns:
            Dict mapping filter name to filter function
        """
        pass


class PluginManager:
    """Manages plugin discovery, loading, and execution."""

    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        self.plugin_dirs = plugin_dirs or []
        self.validators: Dict[str, ValidatorPlugin] = {}
        self.renderers: Dict[str, RendererPlugin] = {}
        self.filters: Dict[str, FilterPlugin] = {}
        self._loaded = False

    def add_plugin_dir(self, directory: Path):
        """Add a directory to search for plugins."""
        if directory.exists() and directory.is_dir():
            self.plugin_dirs.append(directory)

    def discover_plugins(self):
        """Discover and load all plugins from plugin directories."""
        if self._loaded:
            return

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue

            # Find all Python files
            for plugin_file in plugin_dir.glob('*.py'):
                if plugin_file.name.startswith('_'):
                    continue

                try:
                    self._load_plugin_file(plugin_file)
                except Exception as e:
                    click.echo(
                        f"Warning: Failed to load plugin {plugin_file.name}: {e}",
                        err=True
                    )

        self._loaded = True

    def _load_plugin_file(self, plugin_file: Path):
        """Load a single plugin file."""
        # Import the module
        spec = importlib.util.spec_from_file_location(
            f"opsartisan_plugin_{plugin_file.stem}",
            plugin_file
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj in [PluginBase, ValidatorPlugin, RendererPlugin, FilterPlugin]:
                    continue

                if issubclass(obj, ValidatorPlugin):
                    instance = obj()
                    self.validators[instance.name] = instance
                    click.echo(f"Loaded validator plugin: {instance.name} v{instance.version}")

                elif issubclass(obj, RendererPlugin):
                    instance = obj()
                    self.renderers[instance.name] = instance
                    click.echo(f"Loaded renderer plugin: {instance.name} v{instance.version}")

                elif issubclass(obj, FilterPlugin):
                    instance = obj()
                    self.filters[instance.name] = instance
                    click.echo(f"Loaded filter plugin: {instance.name} v{instance.version}")

    def get_validator(self, name: str) -> Optional[ValidatorPlugin]:
        """Get a validator plugin by name."""
        if not self._loaded:
            self.discover_plugins()
        return self.validators.get(name)

    def get_renderer(self, name: str) -> Optional[RendererPlugin]:
        """Get a renderer plugin by name."""
        if not self._loaded:
            self.discover_plugins()
        return self.renderers.get(name)

    def get_all_filters(self) -> Dict[str, Callable]:
        """Get all custom Jinja2 filters from plugins."""
        if not self._loaded:
            self.discover_plugins()

        all_filters = {}
        for plugin in self.filters.values():
            all_filters.update(plugin.get_filters())

        return all_filters

    def list_plugins(self) -> Dict[str, List[str]]:
        """List all loaded plugins by type."""
        if not self._loaded:
            self.discover_plugins()

        return {
            'validators': list(self.validators.keys()),
            'renderers': list(self.renderers.keys()),
            'filters': list(self.filters.keys())
        }

    def validate_with_plugin(
            self,
            plugin_name: str,
            file_path: Path,
            content: str,
            context: Dict[str, Any]
    ) -> List[str]:
        """Run validation using a specific plugin."""
        validator = self.get_validator(plugin_name)
        if not validator:
            raise ValueError(f"Validator plugin '{plugin_name}' not found")

        return validator.validate(file_path, content, context)


# Example plugin implementations

class YAMLLintValidator(ValidatorPlugin):
    """Example validator plugin for YAML files."""

    @property
    def name(self) -> str:
        return "yamllint"

    @property
    def version(self) -> str:
        return "1.0.0"

    def validate(self, file_path: Path, content: str, context: Dict[str, Any]) -> List[str]:
        """Validate YAML syntax and style."""
        errors = []

        try:
            import yaml
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")

        # Check for tabs (YAML should use spaces)
        if '\t' in content:
            errors.append("YAML files should use spaces, not tabs")

        # Check line length
        for i, line in enumerate(content.split('\n'), 1):
            if len(line) > 120:
                errors.append(f"Line {i} exceeds 120 characters")

        return errors


class TomlValidator(ValidatorPlugin):
    """Example validator plugin for TOML files."""

    @property
    def name(self) -> str:
        return "toml"

    @property
    def version(self) -> str:
        return "1.0.0"

    def validate(self, file_path: Path, content: str, context: Dict[str, Any]) -> List[str]:
        """Validate TOML syntax."""
        errors = []

        try:
            import tomli
            tomli.loads(content)
        except Exception as e:
            errors.append(f"TOML syntax error: {e}")

        return errors


class CustomFilters(FilterPlugin):
    """Example filter plugin with custom Jinja2 filters."""

    @property
    def name(self) -> str:
        return "custom_filters"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_filters(self) -> Dict[str, Callable]:
        """Provide custom filters."""
        return {
            'to_env_var': self._to_env_var,
            'to_yaml_safe': self._to_yaml_safe,
            'base64_encode': self._base64_encode,
            'slugify': self._slugify
        }

    @staticmethod
    def _to_env_var(text: str) -> str:
        """Convert text to environment variable format."""
        return text.upper().replace('-', '_').replace(' ', '_')

    @staticmethod
    def _to_yaml_safe(text: str) -> str:
        """Make text safe for YAML keys."""
        import re
        return re.sub(r'[^a-zA-Z0-9_-]', '_', text)

    @staticmethod
    def _base64_encode(text: str) -> str:
        """Base64 encode text."""
        import base64
        return base64.b64encode(text.encode()).decode()

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to URL-friendly slug."""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')