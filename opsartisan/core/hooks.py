"""Hook execution for pre and post generation actions."""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List
import click


class HookExecutor:
    """Executes pre and post generation hooks."""

    @staticmethod
    def execute_hooks(
            hooks: List[Dict[str, Any]],
            working_dir: Path,
            context: Dict[str, Any]
    ) -> bool:
        """
        Execute a list of hooks.

        Args:
            hooks: List of hook definitions
            working_dir: Directory to execute hooks in
            context: Template context (answers) for variable substitution

        Returns:
            True if all hooks succeeded, False otherwise
        """
        if not hooks:
            return True

        all_passed = True

        for hook in hooks:
            hook_type = hook.get('type', 'shell')
            description = hook.get('description', 'Running hook')
            command = hook.get('command', '')
            on_failure = hook.get('on_failure', 'warn')  # warn, fail, ignore
            env = hook.get('env', {})

            click.echo(f"  • {description}")

            try:
                success = HookExecutor._execute_hook(
                    hook_type,
                    command,
                    working_dir,
                    context,
                    env
                )

                if success:
                    click.echo(click.style(f"    ✓ Completed", fg='green'))
                else:
                    msg = f"    ✗ Failed"
                    if on_failure == 'fail':
                        click.echo(click.style(msg, fg='red'))
                        all_passed = False
                    elif on_failure == 'warn':
                        click.echo(click.style(msg, fg='yellow'))
                    # ignore: don't report at all

            except Exception as e:
                msg = f"    ✗ Error: {e}"
                if on_failure == 'fail':
                    click.echo(click.style(msg, fg='red'))
                    all_passed = False
                elif on_failure == 'warn':
                    click.echo(click.style(msg, fg='yellow'))

        return all_passed

    @staticmethod
    def _execute_hook(
            hook_type: str,
            command: str,
            working_dir: Path,
            context: Dict[str, Any],
            extra_env: Dict[str, str]
    ) -> bool:
        """Execute a single hook."""

        # Substitute variables in command
        for key, value in context.items():
            command = command.replace(f"{{{{{key}}}}}", str(value))

        # Prepare environment
        env = os.environ.copy()
        env.update(extra_env)

        if hook_type == 'shell':
            return HookExecutor._execute_shell(command, working_dir, env)
        elif hook_type == 'chmod':
            return HookExecutor._execute_chmod(command, working_dir)
        elif hook_type == 'git':
            return HookExecutor._execute_git(command, working_dir, env)
        else:
            click.echo(f"Unknown hook type: {hook_type}", err=True)
            return False

    @staticmethod
    def _execute_shell(command: str, working_dir: Path, env: Dict) -> bool:
        """Execute a shell command."""
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(working_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0

    @staticmethod
    def _execute_chmod(mode_and_file: str, working_dir: Path) -> bool:
        """Execute chmod command."""
        parts = mode_and_file.split()
        if len(parts) != 2:
            return False

        mode, filename = parts
        filepath = working_dir / filename

        if not filepath.exists():
            return False

        try:
            os.chmod(filepath, int(mode, 8))
            return True
        except Exception:
            return False

    @staticmethod
    def _execute_git(command: str, working_dir: Path, env: Dict) -> bool:
        """Execute a git command."""
        full_command = f"git {command}"
        result = subprocess.run(
            full_command,
            shell=True,
            cwd=str(working_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0

    @staticmethod
    def get_common_hooks() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get a dictionary of common hook patterns.
        Templates can reference these by name.
        """
        return {
            'git_init': [
                {
                    'type': 'git',
                    'command': 'init',
                    'description': 'Initialize git repository',
                    'on_failure': 'warn'
                },
                {
                    'type': 'git',
                    'command': 'add .',
                    'description': 'Stage all files',
                    'on_failure': 'warn'
                }
            ],
            'make_executable': [
                {
                    'type': 'chmod',
                    'command': '755 {{filename}}',
                    'description': 'Make file executable',
                    'on_failure': 'warn'
                }
            ],
            'docker_build': [
                {
                    'type': 'shell',
                    'command': 'docker build -t {{image_name}} .',
                    'description': 'Build Docker image',
                    'on_failure': 'fail'
                }
            ]
        }