"""Template discovery, loading, and rendering."""

import json
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
    """Manages template discovery, loading, and rendering."""

    def __init__(self):
        self.template_dirs = self._discover_template_dirs()

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

    def render_template(
        self,
        template: Dict[str, Any],
        answers: Dict[str, Any],
        out_dir: Path
    ) -> List[Path]:
        """Render template outputs with the given answers."""
        template_path = template['_path']
        templates_subdir = template_path / "templates"

        if not templates_subdir.exists():
            raise ValueError(
                f"Templates directory not found: {templates_subdir}"
            )

        env = Environment(loader=FileSystemLoader(str(templates_subdir)))
        created_files = []

        for output in template.get('outputs', []):
            output_path = out_dir / output['path']
            template_file = output['template']

            # Load and render template
            jinja_template = env.get_template(template_file)
            content = jinja_template.render(**answers)

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            output_path.write_text(content)
            created_files.append(output_path)

        return created_files
