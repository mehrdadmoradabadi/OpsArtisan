"""CLI commands and interface for OpsArtisan."""

import sys
import json
import subprocess
from pathlib import Path
from typing import Optional
import click

from opsartisan.config import __version__, HAS_QUESTIONARY
from opsartisan.core.cli_additions import *
from opsartisan.core.template_manager import TemplateManager
from opsartisan.core.preset_manager import PresetManager
from opsartisan.core.validator import Validator
from opsartisan.core.prompter import InteractivePrompter
from opsartisan.core.dependency_resolver import DependencyResolver
from opsartisan.core.marketplace import TemplateMarketplace
from opsartisan.core.hooks import HookExecutor
from opsartisan.utils.file_utils import copy_directory
from opsartisan.core.plugin_manager import PluginManager
from opsartisan.core.env_manager import EnvironmentManager
from opsartisan.utils.completion import CompletionManager

if HAS_QUESTIONARY:
    import questionary


@click.group()
@click.version_option(__version__)
def cli():
    """OpsArtisan - CLI assistant for sysadmins and DevOps engineers."""
    pass


@cli.command()
@click.option('--category', help='Filter by category')
@click.option('--tag', help='Filter by tag')
@click.option('--search', help='Search in title/description')
def list(category: Optional[str], tag: Optional[str], search: Optional[str]):
    """List available templates with optional filtering."""
    manager = TemplateManager()
    templates = manager.list_templates()

    if not templates:
        click.echo(
            "No templates found. Add templates to ./templates/ "
            "or ~/.opsartisan/templates/"
        )
        return

    # Apply filters
    if category:
        templates = [t for t in templates if t.get('category') == category]
    if tag:
        templates = [t for t in templates if tag in t.get('tags', [])]
    if search:
        search_lower = search.lower()
        templates = [
            t for t in templates
            if search_lower in t.get('title', '').lower()
            or search_lower in t.get('description', '').lower()
        ]

    if not templates:
        click.echo("No templates match your criteria.")
        return

    click.echo(f"Available templates ({len(templates)}):\n")

    # Group by category if available
    categorized = {}
    for template in templates:
        cat = template.get('category', 'Other')
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(template)

    for cat, tmpl_list in sorted(categorized.items()):
        click.echo(click.style(f"{cat}:", fg='cyan', bold=True))
        for template in tmpl_list:
            click.echo(f"  {template['id']}")
            click.echo(f"    {template.get('description', 'No description')}")

            # Show tags if present
            if template.get('tags'):
                tags_str = ', '.join(template['tags'])
                click.echo(click.style(f"    Tags: {tags_str}", fg='blue'))

            # Show popularity hint if available
            if template.get('usage_count'):
                click.echo(click.style(
                    f"    Used {template['usage_count']} times",
                    fg='green'
                ))
            click.echo()


@cli.command()
@click.argument('keyword')
def search(keyword: str):
    """Search for templates by keyword."""
    manager = TemplateManager()
    templates = manager.search_templates(keyword)

    if not templates:
        click.echo(f"No templates found matching '{keyword}'")
        return

    click.echo(f"Found {len(templates)} template(s) matching '{keyword}':\n")
    for template in templates:
        click.echo(f"  {click.style(template['id'], fg='green', bold=True)}")
        click.echo(f"    {template.get('description', 'No description')}")
        if template.get('tags'):
            click.echo(f"    Tags: {', '.join(template['tags'])}")
        click.echo()


@cli.command()
@click.argument('template_id')
def info(template_id: str):
    """Show detailed information about a template."""
    manager = TemplateManager()
    template = manager.get_template(template_id)

    if not template:
        click.echo(f"Error: Template '{template_id}' not found.", err=True)
        sys.exit(1)

    click.echo(click.style(f"\n{template['title']}", fg='cyan', bold=True))
    click.echo(f"ID: {template['id']}")
    click.echo(f"\n{template.get('description', 'No description')}\n")

    # Category and tags
    if template.get('category'):
        click.echo(f"Category: {template['category']}")
    if template.get('tags'):
        click.echo(f"Tags: {', '.join(template['tags'])}")

    # Dependencies
    if template.get('dependencies'):
        click.echo(f"\nDependencies:")
        for dep in template['dependencies']:
            click.echo(f"  - {dep}")

    # Required tools
    if template.get('required_tools'):
        click.echo(f"\nRequired tools:")
        for tool in template['required_tools']:
            click.echo(f"  - {tool}")

    # Prompts
    if template.get('prompts'):
        click.echo(f"\nConfiguration options ({len(template['prompts'])}):")
        for prompt in template['prompts']:
            prompt_type = prompt.get('type', 'string')
            default = prompt.get('default', '')
            click.echo(f"  - {prompt['label']} ({prompt_type})")
            if default:
                click.echo(f"    Default: {default}")

    # Outputs
    if template.get('outputs'):
        click.echo(f"\nGenerated files ({len(template['outputs'])}):")
        for output in template['outputs']:
            click.echo(f"  - {output['path']}")

    # Example usage
    if template.get('example_usage'):
        click.echo(f"\nExample usage:")
        click.echo(f"  {template['example_usage']}")

    # Next steps
    if template.get('next_steps'):
        click.echo(f"\nNext steps:")
        for step in template['next_steps']:
            click.echo(f"  • {step}")

    click.echo(f"\nGenerate with: opsartisan new {template_id}")


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
@click.option(
    '--merge',
    type=click.Choice(['skip', 'overwrite', 'prompt']),
    default='prompt',
    help='Strategy for handling existing files'
)
@click.option('--async-validation', is_flag=True, help='Run validators in parallel')
def new(
        template_id: str,
        yes: bool,
        preset: Optional[str],
        out_dir: str,
        validate: bool,
        test: bool,
        merge: str,
        async_validation: bool
):
    """Generate a new project from a template."""
    manager = TemplateManager()
    template = manager.get_template(template_id)

    if not template:
        click.echo(f"Error: Template '{template_id}' not found.", err=True)
        sys.exit(1)

    # Check and install dependencies
    if template.get('dependencies'):
        click.echo("Checking dependencies...")
        resolver = DependencyResolver(manager)
        missing = resolver.check_dependencies(template)

        if missing:
            click.echo(click.style(
                f"\nMissing dependencies: {', '.join(missing)}",
                fg='yellow'
            ))
            if yes or click.confirm("Generate missing dependencies first?"):
                for dep_id in missing:
                    click.echo(f"\nGenerating dependency: {dep_id}")
                    # Recursively generate dependencies
                    ctx = click.get_current_context()
                    ctx.invoke(new, template_id=dep_id, out_dir=out_dir, yes=True)
            else:
                click.echo("Cannot proceed without dependencies.")
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
        created_files = manager.render_template(
            template, answers, out_path, merge_strategy=merge
        )

        click.echo(click.style("\n✓ Generated files:", fg='green'))
        for file_path in created_files:
            click.echo(f"  {file_path}")

        # Run validators
        if validate:
            click.echo("\nRunning validators...")
            if async_validation:
                success = Validator.run_validators_async(template, out_path)
            else:
                success = Validator.run_validators(template, out_path)

            if not success:
                click.echo(click.style(
                    "\n⚠ Some validators failed. Check output above.",
                    fg='yellow'
                ))

        # Run tests
        if test:
            click.echo("\nRunning tests...")
            Validator.run_tests(template, out_path)

        # Execute post-generation hooks
        if template.get('hooks', {}).get('post_generation'):
            click.echo("\nRunning post-generation hooks...")
            HookExecutor.execute_hooks(
                template['hooks']['post_generation'],
                out_path,
                answers
            )

        # Show next steps
        next_steps = template.get('next_steps', [])
        if next_steps:
            click.echo("\nNext steps:")
            for step in next_steps:
                click.echo(f"  • {step}")

    except Exception as e:
        click.echo(f"\nError generating files: {e}", err=True)
        import traceback
        if '--debug' in sys.argv:
            traceback.print_exc()
        sys.exit(1)


# ============= Preset Management Commands =============

@cli.group()
def preset():
    """Manage saved presets."""
    pass


@preset.command('list')
def preset_list():
    """List all saved presets."""
    presets = PresetManager.load_presets()

    if not presets:
        click.echo("No presets saved yet.")
        click.echo("Create one with: opsartisan save-preset <name> <template_id>")
        return

    click.echo(f"Saved presets ({len(presets)}):\n")
    for name, data in presets.items():
        click.echo(f"  {click.style(name, fg='green', bold=True)}")
        click.echo(f"    Template: {data['template_id']}")
        click.echo(f"    Options: {len(data['answers'])} configured")
        click.echo()


@preset.command('show')
@click.argument('name')
def preset_show(name: str):
    """Show preset details."""
    preset_data = PresetManager.get_preset(name)

    if not preset_data:
        click.echo(f"Error: Preset '{name}' not found.", err=True)
        sys.exit(1)

    click.echo(f"Preset: {click.style(name, fg='green', bold=True)}")
    click.echo(f"Template: {preset_data['template_id']}\n")
    click.echo("Configuration:")
    for key, value in preset_data['answers'].items():
        click.echo(f"  {key}: {value}")


@preset.command('edit')
@click.argument('name')
def preset_edit(name: str):
    """Edit an existing preset."""
    preset_data = PresetManager.get_preset(name)

    if not preset_data:
        click.echo(f"Error: Preset '{name}' not found.", err=True)
        sys.exit(1)

    template_id = preset_data['template_id']
    manager = TemplateManager()
    template = manager.get_template(template_id)

    if not template:
        click.echo(
            f"Error: Template '{template_id}' not found. "
            f"Preset may be outdated.",
            err=True
        )
        sys.exit(1)

    click.echo(f"Editing preset '{name}' for {template['title']}\n")
    click.echo("Current values will be shown as defaults.\n")

    # Use current answers as defaults
    prompter = InteractivePrompter()
    new_answers = prompter.prompt(
        template.get('prompts', []),
        defaults=preset_data['answers']
    )

    PresetManager.save_preset(name, template_id, new_answers)
    click.echo(click.style(f"\n✓ Updated preset '{name}'", fg='green'))


@preset.command('delete')
@click.argument('name')
@click.option('--yes', is_flag=True, help='Skip confirmation')
def preset_delete(name: str, yes: bool):
    """Delete a preset."""
    preset_data = PresetManager.get_preset(name)

    if not preset_data:
        click.echo(f"Error: Preset '{name}' not found.", err=True)
        sys.exit(1)

    if not yes:
        if HAS_QUESTIONARY:
            confirm = questionary.confirm(
                f"Delete preset '{name}'?",
                default=False
            ).ask()
        else:
            confirm = input(
                f"Delete preset '{name}'? [y/N]: "
            ).lower() == 'y'

        if not confirm:
            click.echo("Cancelled.")
            return

    PresetManager.delete_preset(name)
    click.echo(click.style(f"✓ Deleted preset '{name}'", fg='green'))


# ============= Template Management Commands =============

@cli.group()
def template():
    """Manage templates."""
    pass


@template.command('search')
@click.argument('keyword')
def template_search(keyword: str):
    """Search for templates in the marketplace."""
    marketplace = TemplateMarketplace()

    click.echo(f"Searching marketplace for '{keyword}'...")
    results = marketplace.search(keyword)

    if not results:
        click.echo(f"No templates found matching '{keyword}'")
        return

    click.echo(f"\nFound {len(results)} template(s):\n")
    for result in results:
        installed = "✓ installed" if result.get('installed') else ""
        click.echo(
            f"  {click.style(result['id'], fg='green', bold=True)} {installed}"
        )
        click.echo(f"    {result['description']}")
        click.echo(f"    Author: {result.get('author', 'Unknown')}")
        if result.get('downloads'):
            click.echo(f"    Downloads: {result['downloads']}")
        click.echo()

    click.echo("Install with: opsartisan template install <template_id>")


@template.command('install')
@click.argument('source')
@click.option('--name', help='Custom template ID')
def template_install(source: str, name: Optional[str]):
    """Install a template from URL or marketplace."""
    marketplace = TemplateMarketplace()

    try:
        if source.startswith(('http://', 'https://', 'git@')):
            # Git URL
            click.echo(f"Installing template from {source}...")
            template_id = marketplace.install_from_git(source, custom_name=name)
        else:
            # Marketplace ID
            click.echo(f"Installing template '{source}' from marketplace...")
            template_id = marketplace.install_from_marketplace(source)

        click.echo(click.style(
            f"\n✓ Successfully installed template '{template_id}'",
            fg='green'
        ))
        click.echo(f"Use with: opsartisan new {template_id}")

    except Exception as e:
        click.echo(f"Error installing template: {e}", err=True)
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


@cli.command()
def init():
    """Interactive tutorial for creating your first template."""
    click.echo(click.style(
        "\n🎓 Welcome to OpsArtisan Template Creator!\n",
        fg='cyan',
        bold=True
    ))
    click.echo("This wizard will help you create a custom template.\n")

    # Guide through template creation
    if HAS_QUESTIONARY:
        template_id = questionary.text(
            "Template ID (lowercase, no spaces):",
            default="my-template"
        ).ask()

        title = questionary.text(
            "Template title:",
            default="My Custom Template"
        ).ask()

        description = questionary.text(
            "Short description:"
        ).ask()

        category = questionary.select(
            "Category:",
            choices=["Infrastructure", "Configuration", "CI/CD", "Other"]
        ).ask()
    else:
        template_id = input("Template ID (lowercase, no spaces): ") or "my-template"
        title = input("Template title: ") or "My Custom Template"
        description = input("Short description: ")
        category = input("Category [Infrastructure]: ") or "Infrastructure"

    # Create template structure
    from opsartisan.config import USER_TEMPLATES_DIR
    template_dir = USER_TEMPLATES_DIR / template_id
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "templates").mkdir(exist_ok=True)

    # Create descriptor
    descriptor = {
        "id": template_id,
        "title": title,
        "description": description,
        "category": category,
        "prompts": [
            {
                "id": "example_var",
                "type": "string",
                "label": "Example variable",
                "default": "value"
            }
        ],
        "outputs": [
            {
                "path": "output.txt",
                "template": "example.j2"
            }
        ],
        "next_steps": [
            "Review the generated file",
            "Customize as needed"
        ]
    }

    with open(template_dir / "descriptor.json", 'w') as f:
        json.dump(descriptor, f, indent=2)

    # Create example template
    with open(template_dir / "templates" / "example.j2", 'w') as f:
        f.write("# Generated by {{ title }}\n")
        f.write("Example variable: {{ example_var }}\n")

    click.echo(click.style(f"\n✓ Created template '{template_id}'!", fg='green'))
    click.echo(f"Location: {template_dir}")
    click.echo(f"\nTest it with: opsartisan new {template_id}")
    click.echo(f"Edit descriptor: {template_dir / 'descriptor.json'}")
    click.echo(f"Edit template: {template_dir / 'templates' / 'example.j2'}")


cli.add_command(completion)
cli.add_command(plugin)
cli.add_command(env)
cli.add_command(stats)
cli.add_command(validate_template, name='validate')
if __name__ == '__main__':
    cli()