"""Additional CLI commands to add to cli.py"""

import click
import sys
from pathlib import Path
from typing import Optional

from opsartisan.core.template_manager import TemplateManager
from opsartisan.core.preset_manager import PresetManager
from opsartisan.core.plugin_manager import PluginManager
from opsartisan.core.env_manager import EnvironmentManager
from opsartisan.utils.completion import CompletionManager
from opsartisan.config import USER_CONFIG_DIR, USER_TEMPLATES_DIR


# ============= Completion Commands =============

@click.group()
def completion():
    """Shell completion management."""
    pass


@completion.command('install')
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
def completion_install(shell: str):
    """Install shell completion for bash, zsh, or fish."""
    manager = CompletionManager()
    success = manager.install_completion(shell)

    if success:
        click.echo(click.style(f"\n✓ Completion installed for {shell}", fg='green'))
    else:
        click.echo(click.style(f"\n✗ Failed to install completion", fg='red'))
        sys.exit(1)


@completion.command('show')
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
def completion_show(shell: str):
    """Show completion script for manual installation."""
    manager = CompletionManager()
    manager.show_completion_script(shell)


# ============= Plugin Commands =============

@click.group()
def plugin():
    """Manage plugins."""
    pass


@plugin.command('list')
def plugin_list():
    """List all installed plugins."""
    plugin_manager = PluginManager([
        USER_CONFIG_DIR / 'plugins',
        USER_TEMPLATES_DIR / 'plugins'
    ])

    plugins = plugin_manager.list_plugins()

    total = sum(len(p) for p in plugins.values())

    if total == 0:
        click.echo("No plugins installed.")
        click.echo(f"\nAdd plugins to: {USER_CONFIG_DIR / 'plugins'}")
        return

    click.echo(f"Installed plugins ({total}):\n")

    if plugins['validators']:
        click.echo(click.style("Validators:", fg='cyan', bold=True))
        for name in plugins['validators']:
            click.echo(f"  • {name}")
        click.echo()

    if plugins['renderers']:
        click.echo(click.style("Renderers:", fg='cyan', bold=True))
        for name in plugins['renderers']:
            click.echo(f"  • {name}")
        click.echo()

    if plugins['filters']:
        click.echo(click.style("Jinja2 Filters:", fg='cyan', bold=True))
        for name in plugins['filters']:
            click.echo(f"  • {name}")


@plugin.command('info')
@click.argument('plugin_name')
def plugin_info(plugin_name: str):
    """Show information about a specific plugin."""
    plugin_manager = PluginManager([
        USER_CONFIG_DIR / 'plugins',
        USER_TEMPLATES_DIR / 'plugins'
    ])

    # Try to find the plugin
    validator = plugin_manager.get_validator(plugin_name)
    renderer = plugin_manager.get_renderer(plugin_name)
    filter_plugin = plugin_manager.filters.get(plugin_name)

    plugin = validator or renderer or filter_plugin

    if not plugin:
        click.echo(f"Plugin '{plugin_name}' not found.", err=True)
        sys.exit(1)

    click.echo(click.style(f"\n{plugin.name}", fg='cyan', bold=True))
    click.echo(f"Version: {plugin.version}")

    if validator:
        click.echo("Type: Validator")
    elif renderer:
        click.echo("Type: Renderer")
    elif filter_plugin:
        click.echo("Type: Jinja2 Filters")
        filters = filter_plugin.get_filters()
        click.echo(f"\nProvides {len(filters)} filter(s):")
        for filter_name in filters.keys():
            click.echo(f"  • {filter_name}")


# ============= Environment Commands =============

@click.group()
def env():
    """Manage environment configurations."""
    pass


@env.command('create')
@click.argument('template_id')
@click.argument('env_name')
@click.option('--from-preset', help='Base configuration from preset')
@click.option('--out-dir', type=click.Path(), default='.', help='Output directory')
def env_create(template_id: str, env_name: str, from_preset: Optional[str], out_dir: str):
    """Create environment-specific configuration."""
    manager = TemplateManager()
    template = manager.get_template(template_id)

    if not template:
        click.echo(f"Error: Template '{template_id}' not found.", err=True)
        sys.exit(1)

    # Get base configuration
    if from_preset:
        preset_data = PresetManager.get_preset(from_preset)
        if not preset_data:
            click.echo(f"Error: Preset '{from_preset}' not found.", err=True)
            sys.exit(1)
        base_config = preset_data['answers']
    else:
        from opsartisan.core.prompter import InteractivePrompter
        prompter = InteractivePrompter()
        base_config = prompter.prompt(template.get('prompts', []))

    # Apply environment defaults
    env_defaults = template.get('environment_defaults', {}).get(env_name, {})

    click.echo(f"\nEnvironment-specific overrides for '{env_name}':")
    for key, value in env_defaults.items():
        click.echo(f"  {key}: {value}")

    # Create environment manager and save
    env_manager = EnvironmentManager(Path(out_dir))
    env_file = env_manager.create_environment(env_name, base_config, env_defaults)

    # Also create .env file
    env_manager.create_env_file(env_name, {**base_config, **env_defaults})

    click.echo(click.style(f"\n✓ Created environment '{env_name}'", fg='green'))
    click.echo(f"Config: {env_file}")
    click.echo(f"Env file: {Path(out_dir) / f'.env.{env_name}'}")


@env.command('list')
@click.option('--out-dir', type=click.Path(), default='.', help='Output directory')
def env_list(out_dir: str):
    """List all environment configurations."""
    env_manager = EnvironmentManager(Path(out_dir))
    environments = env_manager.list_environments()

    if not environments:
        click.echo("No environment configurations found.")
        click.echo(f"\nCreate one with: opsartisan env create <template> <env-name>")
        return

    click.echo(f"Available environments ({len(environments)}):\n")
    for env_name in environments:
        config = env_manager.load_environment(env_name)
        click.echo(f"  {click.style(env_name, fg='green', bold=True)}")
        if config:
            click.echo(f"    {len(config)} configuration values")


@env.command('compare')
@click.argument('template_id')
@click.argument('environments', nargs=-1, required=True)
@click.option('--out-dir', type=click.Path(), default='.', help='Output directory')
def env_compare(template_id: str, environments: tuple, out_dir: str):
    """Compare configurations across environments."""
    manager = TemplateManager()
    template = manager.get_template(template_id)

    if not template:
        click.echo(f"Error: Template '{template_id}' not found.", err=True)
        sys.exit(1)

    env_manager = EnvironmentManager(Path(out_dir))

    # Load configurations for each environment
    variants = {}
    for env_name in environments:
        config = env_manager.load_environment(env_name)
        if config:
            variants[env_name] = config
        else:
            click.echo(f"Warning: Environment '{env_name}' not found", err=True)

    if not variants:
        click.echo("No environments to compare.", err=True)
        sys.exit(1)

    # Generate comparison report
    report = env_manager.create_comparison_report(variants)
    click.echo(report)


# ============= Statistics Command =============

@click.command()
def stats():
    """Show template statistics and usage info."""
    manager = TemplateManager()
    stats = manager.get_template_stats()

    click.echo(click.style("\n📊 OpsArtisan Statistics\n", fg='cyan', bold=True))

    click.echo(f"Total templates: {click.style(str(stats['total_templates']), fg='green', bold=True)}")

    if stats['categories']:
        click.echo("\nBy category:")
        for category, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
            click.echo(f"  {category}: {count}")

    if stats['tags']:
        click.echo("\nPopular tags:")
        top_tags = sorted(stats['tags'].items(), key=lambda x: -x[1])[:10]
        for tag, count in top_tags:
            click.echo(f"  {tag}: {count}")

    click.echo("\nTemplate directories:")
    for directory in stats['template_dirs']:
        click.echo(f"  • {directory}")

    # Preset statistics
    presets = PresetManager.load_presets()
    click.echo(f"\nSaved presets: {len(presets)}")


# ============= Validate Command Enhancement =============

@click.command('validate')
@click.argument('template_id')
@click.option('--check-deps', is_flag=True, help='Check dependencies')
@click.option('--check-tools', is_flag=True, help='Check required tools')
def validate_template(template_id: str, check_deps: bool, check_tools: bool):
    """Validate a template definition."""
    manager = TemplateManager()
    template = manager.get_template(template_id)

    if not template:
        click.echo(f"Error: Template '{template_id}' not found.", err=True)
        sys.exit(1)

    click.echo(f"Validating template: {template['title']}\n")

    # Basic validation
    result = manager.validate_template(template)

    if result['errors']:
        click.echo(click.style("❌ Errors:", fg='red', bold=True))
        for error in result['errors']:
            click.echo(f"  • {error}")

    if result['warnings']:
        click.echo(click.style("\n⚠️  Warnings:", fg='yellow', bold=True))
        for warning in result['warnings']:
            click.echo(f"  • {warning}")

    # Check dependencies
    if check_deps and template.get('dependencies'):
        from opsartisan.core.dependency_resolver import DependencyResolver

        click.echo(click.style("\n🔗 Dependencies:", fg='cyan', bold=True))
        resolver = DependencyResolver(manager)

        dep_result = resolver.validate_all_dependencies(template)
        if dep_result['valid']:
            click.echo(click.style("  ✓ All dependencies valid", fg='green'))
        else:
            for error in dep_result['errors']:
                click.echo(click.style(f"  ✗ {error}", fg='red'))

        # Show dependency tree
        click.echo("\nDependency tree:")
        tree = resolver.get_dependency_tree(template)
        click.echo(tree)

    # Check required tools
    if check_tools and template.get('required_tools'):
        import shutil

        click.echo(click.style("\n🔧 Required Tools:", fg='cyan', bold=True))
        for tool in template['required_tools']:
            if shutil.which(tool):
                click.echo(click.style(f"  ✓ {tool} found", fg='green'))
            else:
                click.echo(click.style(f"  ✗ {tool} not found", fg='red'))

    # Summary
    click.echo()
    if result['valid'] and not result['errors']:
        click.echo(click.style("✓ Template is valid", fg='green', bold=True))
    else:
        click.echo(click.style("✗ Template has issues", fg='red', bold=True))
        sys.exit(1)

# ============= Export these to add to main CLI =============

# Add these to cli.py:
# cli.add_command(completion)
# cli.add_command(plugin)
# cli.add_command(env)
# cli.add_command(stats)
# cli.add_command(validate_template)