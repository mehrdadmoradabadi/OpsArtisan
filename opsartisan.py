#!/usr/bin/env python3
"""
OpsArtisan - CLI-first assistant for sysadmins and DevOps engineers.
Generates validated skeletons and config files through interactive wizards.
"""

import click
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template

# Try to import questionary, fallback to input()
try:
    import questionary

    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False

__version__ = "0.1.0"

# Configuration paths
USER_CONFIG_DIR = Path.home() / ".opsartisan"
USER_TEMPLATES_DIR = USER_CONFIG_DIR / "templates"
PRESETS_FILE = USER_CONFIG_DIR / "presets.json"
LOCAL_TEMPLATES_DIR = Path("./templates")
SYSTEM_TEMPLATES_DIR = Path("/usr/share/opsartisan/templates")

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
                        click.echo(f"Warning: Failed to load {descriptor_path}: {e}", err=True)
        return templates

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID."""
        for template in self.list_templates():
            if template.get('id') == template_id:
                return template
        return None

    def render_template(self, template: Dict[str, Any], answers: Dict[str, Any], out_dir: Path) -> List[Path]:
        """Render template outputs with the given answers."""
        template_path = template['_path']
        templates_subdir = template_path / "templates"

        if not templates_subdir.exists():
            raise ValueError(f"Templates directory not found: {templates_subdir}")

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


class InteractivePrompter:
    """Handles interactive prompts using questionary or fallback."""

    @staticmethod
    def prompt(prompts: List[Dict[str, Any]], use_defaults: bool = False) -> Dict[str, Any]:
        """Run interactive prompts and return answers."""
        answers = {}

        for prompt in prompts:
            prompt_id = prompt['id']
            prompt_type = prompt.get('type', 'text')
            label = prompt.get('label', prompt_id)
            default = prompt.get('default', '')
            choices = prompt.get('choices', [])

            if use_defaults:
                answers[prompt_id] = default
                continue

            if HAS_QUESTIONARY:
                if prompt_type == 'text':
                    answer = questionary.text(label, default=str(default)).ask()
                elif prompt_type == 'confirm':
                    answer = questionary.confirm(label, default=bool(default)).ask()
                elif prompt_type == 'select':
                    answer = questionary.select(label, choices=choices, default=default).ask()
                elif prompt_type == 'number':
                    answer = questionary.text(label, default=str(default)).ask()
                    try:
                        answer = int(answer)
                    except ValueError:
                        answer = default
                else:
                    answer = questionary.text(label, default=str(default)).ask()
            else:
                # Fallback to input()
                if prompt_type == 'confirm':
                    answer = input(f"{label} [y/N]: ").lower() in ('y', 'yes')
                elif prompt_type == 'select':
                    click.echo(f"{label}")
                    for i, choice in enumerate(choices, 1):
                        click.echo(f"  {i}. {choice}")
                    choice_idx = input(f"Select (1-{len(choices)}) [1]: ") or "1"
                    try:
                        answer = choices[int(choice_idx) - 1]
                    except (ValueError, IndexError):
                        answer = choices[0] if choices else default
                else:
                    answer = input(f"{label} [{default}]: ") or default

            answers[prompt_id] = answer

        return answers


class PresetManager:
    """Manages saved presets."""

    @staticmethod
    def load_presets() -> Dict[str, Any]:
        """Load presets from file."""
        if not PRESETS_FILE.exists():
            return {}
        try:
            with open(PRESETS_FILE) as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def save_preset(name: str, template_id: str, answers: Dict[str, Any]):
        """Save a preset."""
        presets = PresetManager.load_presets()
        presets[name] = {
            'template_id': template_id,
            'answers': answers
        }
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(PRESETS_FILE, 'w') as f:
            json.dump(presets, f, indent=2)

    @staticmethod
    def get_preset(name: str) -> Optional[Dict[str, Any]]:
        """Get a specific preset."""
        presets = PresetManager.load_presets()
        return presets.get(name)


class Validator:
    """Handles validation and testing of generated files."""

    @staticmethod
    def run_validators(template: Dict[str, Any], out_dir: Path) -> bool:
        """Run validators for a template."""
        validators = template.get('validators', [])
        if not validators:
            click.echo("No validators defined for this template.")
            return True

        all_passed = True
        for validator in validators:
            cmd = validator.get('command', '')
            description = validator.get('description', cmd)

            click.echo(f"Running validator: {description}")

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(out_dir),
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    click.echo(click.style(f"  ✓ {description} passed", fg='green'))
                else:
                    click.echo(click.style(f"  ✗ {description} failed", fg='red'))
                    if result.stderr:
                        click.echo(f"    {result.stderr}")
                    all_passed = False
            except subprocess.TimeoutExpired:
                click.echo(click.style(f"  ✗ {description} timed out", fg='red'))
                all_passed = False
            except Exception as e:
                click.echo(click.style(f"  ✗ {description} error: {e}", fg='red'))
                all_passed = False

        return all_passed

    @staticmethod
    def run_tests(template: Dict[str, Any], out_dir: Path) -> bool:
        """Run tests for a template."""
        tests = template.get('tests', [])
        if not tests:
            click.echo("No tests defined for this template.")
            return True

        all_passed = True
        for test in tests:
            cmd = test.get('command', '')
            description = test.get('description', cmd)

            click.echo(f"Running test: {description}")

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(out_dir),
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    click.echo(click.style(f"  ✓ {description} passed", fg='green'))
                else:
                    click.echo(click.style(f"  ✗ {description} failed", fg='red'))
                    if result.stderr:
                        click.echo(f"    {result.stderr}")
                    all_passed = False
            except subprocess.TimeoutExpired:
                click.echo(click.style(f"  ✗ {description} timed out", fg='red'))
                all_passed = False
            except Exception as e:
                click.echo(click.style(f"  ✗ {description} error: {e}", fg='red'))
                all_passed = False

        return all_passed


@click.group()
@click.version_option(__version__)
def cli():
    """OpsArtisan - CLI assistant for sysadmins and DevOps engineers."""
    pass


@cli.command()
def list():
    """List available templates."""
    manager = TemplateManager()
    templates = manager.list_templates()

    if not templates:
        click.echo("No templates found. Add templates to ./templates/ or ~/.opsartisan/templates/")
        return

    click.echo(f"Available templates ({len(templates)}):\n")
    for template in templates:
        click.echo(f"  {template['id']}")
        click.echo(f"    {template.get('description', 'No description')}")
        click.echo()


@cli.command()
@click.argument('template_id')
@click.option('--yes', is_flag=True, help='Use defaults without prompting')
@click.option('--preset', help='Use saved preset')
@click.option('--out-dir', type=click.Path(), default='.', help='Output directory')
@click.option('--validate', is_flag=True, help='Run validators after generation')
@click.option('--test', is_flag=True, help='Run tests after generation')
def new(template_id: str, yes: bool, preset: Optional[str], out_dir: str, validate: bool, test: bool):
    """Generate a new project from a template."""
    manager = TemplateManager()
    template = manager.get_template(template_id)

    if not template:
        click.echo(f"Error: Template '{template_id}' not found.", err=True)
        sys.exit(1)

    click.echo(f"Creating {template['title']}")
    click.echo(f"  {template.get('description', '')}\n")

    # Get answers
    if preset:
        preset_data = PresetManager.get_preset(preset)
        if not preset_data:
            click.echo(f"Error: Preset '{preset}' not found.", err=True)
            sys.exit(1)
        if preset_data['template_id'] != template_id:
            click.echo(f"Warning: Preset is for template '{preset_data['template_id']}', not '{template_id}'", err=True)
        answers = preset_data['answers']
    else:
        prompter = InteractivePrompter()
        answers = prompter.prompt(template.get('prompts', []), use_defaults=yes)

    # Show summary
    click.echo("\nConfiguration:")
    for key, value in answers.items():
        click.echo(f"  {key}: {value}")

    if not yes and not preset:
        if HAS_QUESTIONARY:
            confirm = questionary.confirm("Proceed with generation?", default=True).ask()
        else:
            confirm = input("Proceed with generation? [Y/n]: ").lower() != 'n'

        if not confirm:
            click.echo("Cancelled.")
            return

    # Generate files
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    try:
        created_files = manager.render_template(template, answers, out_path)

        click.echo(click.style("\n✓ Generated files:", fg='green'))
        for file_path in created_files:
            click.echo(f"  {file_path}")

        # Run validators
        if validate:
            click.echo("\nRunning validators...")
            Validator.run_validators(template, out_path)

        # Run tests
        if test:
            click.echo("\nRunning tests...")
            Validator.run_tests(template, out_path)

        # Show next steps
        next_steps = template.get('next_steps', [])
        if next_steps:
            click.echo("\nNext steps:")
            for step in next_steps:
                click.echo(f"  • {step}")

    except Exception as e:
        click.echo(f"\nError generating files: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def add_template(path: str):
    """Add a template directory to user templates."""
    source = Path(path)

    if not (source / "descriptor.json").exists():
        click.echo("Error: No descriptor.json found in template directory.", err=True)
        sys.exit(1)

    # Load descriptor to get ID
    with open(source / "descriptor.json") as f:
        descriptor = json.load(f)

    template_id = descriptor.get('id')
    if not template_id:
        click.echo("Error: Template descriptor missing 'id' field.", err=True)
        sys.exit(1)

    # Copy to user templates
    USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    dest = USER_TEMPLATES_DIR / template_id

    if dest.exists():
        if HAS_QUESTIONARY:
            overwrite = questionary.confirm(f"Template '{template_id}' already exists. Overwrite?").ask()
        else:
            overwrite = input(f"Template '{template_id}' already exists. Overwrite? [y/N]: ").lower() == 'y'

        if not overwrite:
            click.echo("Cancelled.")
            return

    # Copy directory
    import shutil
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)

    click.echo(click.style(f"✓ Added template '{template_id}' to {dest}", fg='green'))


@cli.command()
@click.argument('name')
@click.argument('template_id')
def save_preset(name: str, template_id: str):
    """Save current answers as a preset (interactive)."""
    manager = TemplateManager()
    template = manager.get_template(template_id)

    if not template:
        click.echo(f"Error: Template '{template_id}' not found.", err=True)
        sys.exit(1)

    click.echo(f"Creating preset '{name}' for {template['title']}\n")

    prompter = InteractivePrompter()
    answers = prompter.prompt(template.get('prompts', []))

    PresetManager.save_preset(name, template_id, answers)
    click.echo(click.style(f"\n✓ Saved preset '{name}'", fg='green'))
    click.echo(f"Use with: opsartisan new {template_id} --preset {name}")

@cli.command("validate-file")
@click.argument("template_id")
@click.argument("file_path", type=click.Path(exists=True))
def validate_file_cli(template_id: str, file_path: str):
    """
    Validate a user-provided file against a template's expected syntax.
    Example: opsartisan validate-file docker-compose ./docker-compose.yml
    """
    template = TemplateManager().get_template(template_id)
    if not template:
        click.echo(f"Error: Template '{template_id}' not found.", err=True)
        sys.exit(1)

    file_path = Path(file_path)
    click.echo(f"Validating '{file_path}' against template '{template_id}'...\n")

    # Map template IDs to validation commands
    validators = {
        "dockerfile": lambda path: ["docker", "build", "-f", str(path), "."],
        "docker-compose": lambda path: ["docker", "compose", "config", "-q"],
        "kubernetes": lambda path: ["kubectl", "apply", "--dry-run=client", "-f", str(path)],
        "ansible": lambda path: ["ansible-playbook", "--syntax-check", str(path)],
        "systemd": lambda path: ["systemd-analyze", "verify", str(path)],
        "terraform": lambda path: ["terraform", "validate"]
    }

    validator_func = validators.get(template_id)
    if not validator_func:
        click.echo(f"No validator configured for template '{template_id}'", err=True)
        sys.exit(1)

    cmd = validator_func(file_path)
    try:
        click.echo(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        click.echo(click.style(f"\n✅ File '{file_path}' is valid for template '{template_id}'", fg="green"))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"\n❌ Validation failed for '{file_path}'", fg="red"))
        if e.stderr:
            click.echo(e.stderr)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"\n❌ Error during validation: {e}", fg="red"))
        sys.exit(1)


if __name__ == '__main__':
    cli()