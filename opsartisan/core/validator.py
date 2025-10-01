"""Validation and testing of generated files."""

import subprocess
from pathlib import Path
from typing import Dict, Any
import click


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
                    click.echo(
                        click.style(f"  ✓ {description} passed", fg='green')
                    )
                else:
                    click.echo(
                        click.style(f"  ✗ {description} failed", fg='red')
                    )
                    if result.stderr:
                        click.echo(f"    {result.stderr}")
                    all_passed = False
            except subprocess.TimeoutExpired:
                click.echo(
                    click.style(f"  ✗ {description} timed out", fg='red')
                )
                all_passed = False
            except Exception as e:
                click.echo(
                    click.style(f"  ✗ {description} error: {e}", fg='red')
                )
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
                    click.echo(
                        click.style(f"  ✓ {description} passed", fg='green')
                    )
                else:
                    click.echo(
                        click.style(f"  ✗ {description} failed", fg='red')
                    )
                    if result.stderr:
                        click.echo(f"    {result.stderr}")
                    all_passed = False
            except subprocess.TimeoutExpired:
                click.echo(
                    click.style(f"  ✗ {description} timed out", fg='red')
                )
                all_passed = False
            except Exception as e:
                click.echo(
                    click.style(f"  ✗ {description} error: {e}", fg='red')
                )
                all_passed = False

        return all_passed
