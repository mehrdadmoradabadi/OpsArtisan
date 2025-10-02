"""Enhanced validation and testing of generated files with better error messages."""

import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import click

from opsartisan.utils.validation_utils import ValidationParser, MultiFileValidator, ValidationError
from opsartisan.utils.async_utils import AsyncValidator


class Validator:
    """Handles validation and testing of generated files with enhanced error reporting."""

    @staticmethod
    def run_validators(template: Dict[str, Any], out_dir: Path, context: Dict[str, Any] = None) -> bool:
        """Run validators for a template with enhanced error messages."""
        validators = template.get('validators', [])
        if not validators:
            click.echo("No validators defined for this template.")
            return True

        all_passed = True
        template_type = template.get('id', '').split('-')[0]  # e.g., 'docker' from 'docker-compose'

        # Multi-file validation context
        multi_validator = MultiFileValidator()

        # Add files to context for cross-file validation
        if context:
            for key, value in context.items():
                if isinstance(value, str) and value.endswith(('.yml', '.yaml', '.json')):
                    file_path = out_dir / value
                    if file_path.exists():
                        multi_validator.add_file_context(str(file_path), file_path.read_text())

        for validator in validators:
            cmd = validator.get('command', '')
            description = validator.get('description', cmd)
            file_path = validator.get('file')

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
                    click.echo(
                        click.style(f"  ✓ {description} passed", fg='green')
                    )
                else:
                    click.echo(
                        click.style(f"  ✗ {description} failed", fg='red')
                    )

                    # Parse and enhance error messages
                    if result.stderr:
                        errors = ValidationParser.parse_error(
                            result.stderr,
                            template_type,
                            file_path
                        )

                        if errors:
                            click.echo(click.style("\n  Detailed errors:", fg='yellow'))
                            for error in errors:
                                formatted = error.format()
                                for line in formatted.split('\n'):
                                    click.echo(f"    {line}")
                        else:
                            # Fallback to raw stderr
                            click.echo(f"    {result.stderr}")

                        # Show quick fixes
                        quick_fixes = ValidationParser.get_quick_fixes(template_type)
                        if quick_fixes:
                            click.echo(click.style("\n  Quick fixes:", fg='cyan'))
                            for fix in quick_fixes[:3]:  # Show top 3
                                click.echo(f"    • {fix}")

                    all_passed = False

            except subprocess.TimeoutExpired:
                click.echo(
                    click.style(f"  ✗ {description} timed out", fg='red')
                )
                click.echo(click.style(
                    "    💡 Suggestion: Check for infinite loops or increase timeout",
                    fg='yellow'
                ))
                all_passed = False
            except FileNotFoundError:
                click.echo(
                    click.style(f"  ✗ {description} - command not found", fg='red')
                )
                # Extract command name
                cmd_name = cmd.split()[0]
                click.echo(click.style(
                    f"    💡 Suggestion: Install '{cmd_name}' or check PATH",
                    fg='yellow'
                ))
                click.echo(f"    📚 Check: https://command-not-found.com/{cmd_name}")
                all_passed = False
            except Exception as e:
                click.echo(
                    click.style(f"  ✗ {description} error: {e}", fg='red')
                )
                all_passed = False

        return all_passed

    @staticmethod
    def run_validators_async(template: Dict[str, Any], out_dir: Path, context: Dict[str, Any] = None) -> bool:
        """Run validators in parallel for faster feedback."""
        validators = template.get('validators', [])
        if not validators:
            click.echo("No validators defined for this template.")
            return True

        # Run async validation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            all_passed, results = loop.run_until_complete(
                AsyncValidator.run_validators_async(validators, out_dir)
            )

            # Process results with enhanced error messages
            template_type = template.get('id', '').split('-')[0]

            for result in results:
                if not result['success'] and result.get('error'):
                    errors = ValidationParser.parse_error(
                        result['error'],
                        template_type,
                        result.get('file')
                    )

                    if errors:
                        click.echo(click.style("\n  Enhanced error details:", fg='yellow'))
                        for error in errors:
                            formatted = error.format()
                            for line in formatted.split('\n'):
                                click.echo(f"    {line}")

            return all_passed

        finally:
            loop.close()

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
                    click.echo(
                        click.style(f"  ✓ {description} passed", fg='green')
                    )
                    if result.stdout:
                        # Show test output summary
                        lines = result.stdout.strip().split('\n')
                        if len(lines) <= 5:
                            for line in lines:
                                click.echo(f"    {line}")
                        else:
                            click.echo(f"    ... {len(lines)} lines of output")
                else:
                    click.echo(
                        click.style(f"  ✗ {description} failed", fg='red')
                    )
                    if result.stderr:
                        click.echo(f"    {result.stderr}")
                    elif result.stdout:
                        click.echo(f"    {result.stdout}")
                    all_passed = False
            except subprocess.TimeoutExpired:
                click.echo(
                    click.style(f"  ✗ {description} timed out (60s)", fg='red')
                )
                click.echo(click.style(
                    "    💡 Tests taking too long? Consider optimizing or increasing timeout",
                    fg='yellow'
                ))
                all_passed = False
            except Exception as e:
                click.echo(
                    click.style(f"  ✗ {description} error: {e}", fg='red')
                )
                all_passed = False

        return all_passed

    @staticmethod
    def validate_multi_file_context(
        template: Dict[str, Any],
        out_dir: Path,
        generated_files: List[Path]
    ) -> List[ValidationError]:
        """
        Validate multiple files with context awareness.
        Checks cross-file references and dependencies.
        """
        multi_validator = MultiFileValidator()
        errors = []

        template_type = template.get('id', '')

        # Docker Compose + .env validation
        if 'docker-compose' in template_type:
            compose_file = None
            env_file = None

            for file in generated_files:
                if 'docker-compose' in file.name:
                    compose_file = file
                elif file.name == '.env':
                    env_file = file

            if compose_file:
                compose_content = compose_file.read_text()
                env_content = env_file.read_text() if env_file else None

                errors.extend(
                    multi_validator.validate_docker_compose_with_env(
                        compose_content,
                        env_content
                    )
                )

        # Kubernetes multi-resource validation
        elif 'kubernetes' in template_type or 'k8s' in template_type:
            import yaml
            resources = []

            for file in generated_files:
                if file.suffix in ['.yaml', '.yml']:
                    try:
                        with open(file) as f:
                            docs = yaml.safe_load_all(f)
                            for doc in docs:
                                if doc:
                                    resources.append(doc)
                    except Exception:
                        pass

            if resources:
                errors.extend(
                    multi_validator.validate_kubernetes_resources(resources)
                )

        return errors

    @staticmethod
    def show_validation_summary(
        all_passed: bool,
        template: Dict[str, Any],
        errors: List[ValidationError] = None
    ):
        """Show a summary of validation results."""
        click.echo()

        if all_passed and not errors:
            click.echo(click.style("✓ All validations passed!", fg='green', bold=True))
            click.echo(click.style(
                "  Your generated files are ready to use.",
                fg='green'
            ))
        else:
            click.echo(click.style("⚠ Some validations failed", fg='yellow', bold=True))

            if errors:
                click.echo(click.style(f"\nFound {len(errors)} issue(s):", fg='yellow'))
                for error in errors:
                    formatted = error.format()
                    for line in formatted.split('\n'):
                        click.echo(f"  {line}")

            click.echo(click.style("\n💡 Tips:", fg='cyan'))
            click.echo("  • Review the error messages above")
            click.echo("  • Check the documentation links provided")
            click.echo("  • Run with --debug for more details")

            # Offer to show template info
            template_id = template.get('id')
            if template_id:
                click.echo(f"  • Run 'opsartisan info {template_id}' for template details")