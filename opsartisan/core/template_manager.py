"""Enhanced template discovery, loading, and rendering with merge strategies."""

import json
import difflib
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader
import click

from opsartisan.config import (
    LOCAL_TEMPLATES_DIR,
    USER_TEMPLATES_DIR,
    SYSTEM_TEMPLATES_DIR
)


class TemplateManager:
    """Manages template discovery, loading, and rendering with advanced features."""

    def __init__(self, plugin_manager=None):
        self.template_dirs = self._discover_template_dirs()
        self.plugin_manager = plugin_manager

    def _discover_template_dirs(self) -> List[Path]:
        """Find all template directories."""
        dirs = []
        if LOCAL_TEMPLATES_DIR.exists():
            dirs.append(LOCAL_TEMPLATES_DIR)
        if USER_TEMPLATES_DIR.exists():
            dirs.append(USER_TEMPLATES_DIR)
        if SYSTEM_TEMPLATES_DIR.exists():
            dirs.append(SYSTEM_TEMPLATES_DIR)
        return dirs

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates with metadata."""
        templates = []
        for template_dir in self.template_dirs:
            if not template_dir.is_dir():
                continue
            for subdir in template_dir.iterdir():
                if not subdir.is_dir():
                    continue
                descriptor_path = subdir / "descriptor.json"
                if descriptor_path.exists():
                    try:
                        with open(descriptor_path) as f:
                            descriptor = json.load(f)
                            descriptor['_path'] = subdir
                            templates.append(descriptor)
                    except Exception as e:
                        click.echo(
                            f"Warning: Failed to load {descriptor_path}: {e}",
                            err=True
                        )
        return templates

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID."""
        for template in self.list_templates():
            if template.get('id') == template_id:
                return template
        return None

    def search_templates(self, keyword: str) -> List[Dict[str, Any]]:
        """Search templates by keyword in id, title, description, or tags."""
        keyword_lower = keyword.lower()
        templates = self.list_templates()

        results = []
        for template in templates:
            # Search in multiple fields
            searchable = [
                template.get('id', ''),
                template.get('title', ''),
                template.get('description', ''),
                ' '.join(template.get('tags', []))
            ]

            if any(keyword_lower in field.lower() for field in searchable):
                results.append(template)

        return results

    def render_template(
        self,
        template: Dict[str, Any],
        answers: Dict[str, Any],
        out_dir: Path,
        merge_strategy: str = 'prompt'
    ) -> List[Path]:
        """
        Render template outputs with the given answers.

        Args:
            template: Template definition
            answers: User answers for template variables
            out_dir: Output directory
            merge_strategy: How to handle existing files ('skip', 'overwrite', 'prompt')

        Returns:
            List of created/updated file paths
        """
        template_path = template['_path']
        templates_subdir = template_path / "templates"

        if not templates_subdir.exists():
            raise ValueError(
                f"Templates directory not found: {templates_subdir}"
            )

        # Setup Jinja2 environment with custom filters
        env = Environment(loader=FileSystemLoader(str(templates_subdir)))

        # Add plugin filters if available
        if self.plugin_manager:
            custom_filters = self.plugin_manager.get_all_filters()
            env.filters.update(custom_filters)

        created_files = []

        for output in template.get('outputs', []):
            # Render output path (supports template variables)
            output_path_template = env.from_string(output['path'])
            output_path = out_dir / output_path_template.render(**answers)

            template_file = output['template']

            # Check if file exists and handle merge strategy
            if output_path.exists():
                action = self._handle_existing_file(
                    output_path,
                    merge_strategy
                )

                if action == 'skip':
                    click.echo(f"  Skipped (already exists): {output_path}")
                    continue
                elif action == 'backup':
                    backup_path = output_path.with_suffix(output_path.suffix + '.backup')
                    output_path.rename(backup_path)
                    click.echo(f"  Backed up to: {backup_path}")

            # Load and render template
            jinja_template = env.get_template(template_file)
            content = jinja_template.render(**answers)

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            output_path.write_text(content)
            created_files.append(output_path)

        return created_files

    def _handle_existing_file(
        self,
        file_path: Path,
        merge_strategy: str
    ) -> str:
        """
        Handle an existing file based on merge strategy.

        Returns:
            Action to take: 'overwrite', 'skip', or 'backup'
        """
        if merge_strategy == 'overwrite':
            return 'overwrite'
        elif merge_strategy == 'skip':
            return 'skip'
        elif merge_strategy == 'prompt':
            click.echo(f"\n  File already exists: {file_path}")
            click.echo("  Options:")
            click.echo("    o - Overwrite")
            click.echo("    s - Skip")
            click.echo("    b - Backup and create new")
            click.echo("    d - Show diff")

            while True:
                choice = input("  Choose [o/s/b/d]: ").lower()

                if choice == 'o':
                    return 'overwrite'
                elif choice == 's':
                    return 'skip'
                elif choice == 'b':
                    return 'backup'
                elif choice == 'd':
                    self._show_diff(file_path)
                else:
                    click.echo("  Invalid choice. Please enter o, s, b, or d.")

        return 'skip'

    def _show_diff(self, file_path: Path):
        """Show diff between existing file and what would be generated."""
        try:
            existing_content = file_path.read_text().splitlines(keepends=True)
            click.echo("\n  Current file content (first 20 lines):")
            for i, line in enumerate(existing_content[:20], 1):
                click.echo(f"    {i:3d}: {line}", nl=False)

            if len(existing_content) > 20:
                click.echo(f"    ... ({len(existing_content) - 20} more lines)")
            click.echo()
        except Exception as e:
            click.echo(f"  Could not show diff: {e}")

    def validate_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a template definition.

        Returns:
            Dict with 'valid' bool and 'errors'/'warnings' lists
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Required fields
        required = ['id', 'title', 'outputs']
        for field in required:
            if field not in template:
                result['valid'] = False
                result['errors'].append(f"Missing required field: {field}")

        # Validate outputs
        for output in template.get('outputs', []):
            if 'path' not in output:
                result['valid'] = False
                result['errors'].append("Output missing 'path' field")
            if 'template' not in output:
                result['valid'] = False
                result['errors'].append("Output missing 'template' field")

        # Validate prompts
        for prompt in template.get('prompts', []):
            if 'id' not in prompt:
                result['valid'] = False
                result['errors'].append("Prompt missing 'id' field")
            if 'type' not in prompt:
                result['warnings'].append(f"Prompt '{prompt.get('id')}' missing 'type', defaulting to 'string'")

        # Check template files exist
        template_path = template.get('_path')
        if template_path:
            templates_dir = template_path / 'templates'
            if not templates_dir.exists():
                result['valid'] = False
                result['errors'].append(f"Templates directory not found: {templates_dir}")
            else:
                for output in template.get('outputs', []):
                    template_file = templates_dir / output.get('template', '')
                    if not template_file.exists():
                        result['valid'] = False
                        result['errors'].append(f"Template file not found: {template_file}")

        return result

    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about available templates."""
        templates = self.list_templates()

        categories = {}
        tags = {}

        for template in templates:
            # Count categories
            category = template.get('category', 'Other')
            categories[category] = categories.get(category, 0) + 1

            # Count tags
            for tag in template.get('tags', []):
                tags[tag] = tags.get(tag, 0) + 1

        return {
            'total_templates': len(templates),
            'categories': categories,
            'tags': tags,
            'template_dirs': [str(d) for d in self.template_dirs]
        }