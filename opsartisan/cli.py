"""CLI commands and interface for OpsArtisan."""

import sys
import json
import subprocess
from pathlib import Path
from typing import Optional
import click

from opsartisan.config import __version__, HAS_QUESTIONARY
from opsartisan.core.template_manager import TemplateManager
from opsartisan.core.preset_manager import PresetManager
from opsartisan.core.validator import Validator
from opsartisan.core.prompter import InteractivePrompter
from opsartisan.utils.file_utils import copy_directory

if HAS_QUESTIONARY:
    import questionary


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
        click.echo(
            "No templates found. Add templates to ./templates/ "
            "or ~/.opsartisan/templates/"
        )
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
@click.option(
    '--out-dir',
    type=click.Path(),
    default='.',
    help='Output directory'
)
@click.option('--validate', is_flag=True, help='Run validators after generation')
@click.option('--test', is_flag=True, help='Run tests after generation')
def new(
        template_id: str,
        yes: bool,
        preset: Optional[str],
        out_dir: str,
        validate: bool,
        test: bool
):
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
            click.echo(
                f"Warning: Preset is for template "
                f"'{preset_data['template_id']}', not '{template_id}'",
                err=True
            )
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
            confirm = questionary.confirm(
                "Proceed with generation?",
                default=True
            ).ask()
        else:
            confirm = input(
                "Proceed with generation? [Y/n]: "
            ).lower() != 'n'

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
    from opsartisan.config import USER_TEMPLATES_DIR

    source = Path(path)

    if not (source / "descriptor.json").exists():
        click.echo(
            "Error: No descriptor.json found in template directory.",
            err=True
        )
        sys.exit(1)

    # Load descriptor to get ID
    with open(source / "descriptor.json") as f:
        descriptor = json.load(f)

    template_id = descriptor.get('id')
    if not template_id:
        click.echo(
            "Error: Template descriptor missing 'id' field.",
            err=True
        )
        sys.exit(1)

    # Copy to user templates
    dest = USER_TEMPLATES_DIR / template_id

    if dest.exists():
        if HAS_QUESTIONARY:
            overwrite = questionary.confirm(
                f"Template '{template_id}' already exists. Overwrite?"
            ).ask()
        else:
            overwrite = input(
                f"Template '{template_id}' already exists. Overwrite? [y/N]: "
            ).lower() == 'y'

        if not overwrite:
            click.echo("Cancelled.")
            return

    # Copy directory
    copy_directory(source, dest, overwrite=True)

    click.echo(
        click.style(
            f"✓ Added template '{template_id}' to {dest}",
            fg='green'
        )
    )


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
    click.echo(
        f"Validating '{file_path}' against template '{template_id}'...\n"
    )

    # Map template IDs to validation commands
    validators = {
        "dockerfile": lambda path: [
            "docker", "build", "-f", str(path), "."
        ],
        "docker-compose": lambda path: [
            "docker", "compose", "config", "-q"
        ],
        "kubernetes": lambda path: [
            "kubectl", "apply", "--dry-run=client", "-f", str(path)
        ],
        "ansible": lambda path: [
            "ansible-playbook", "--syntax-check", str(path)
        ],
        "systemd": lambda path: [
            "systemd-analyze", "verify", str(path)
        ],
        "terraform": lambda path: ["terraform", "validate"]
    }

    validator_func = validators.get(template_id)
    if not validator_func:
        click.echo(
            f"No validator configured for template '{template_id}'",
            err=True
        )
        sys.exit(1)

    cmd = validator_func(file_path)
    try:
        click.echo(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        click.echo(
            click.style(
                f"\n✅ File '{file_path}' is valid for "
                f"template '{template_id}'",
                fg="green"
            )
        )
    except subprocess.CalledProcessError as e:
        click.echo(
            click.style(f"\n❌ Validation failed for '{file_path}'", fg="red")
        )
        if e.stderr:
            click.echo(e.stderr)
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"\n❌ Error during validation: {e}", fg="red")
        )
        sys.exit(1)


if __name__ == '__main__':
    cli()