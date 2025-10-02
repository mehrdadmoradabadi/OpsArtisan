"""Shell completion support for bash, zsh, and fish."""

from pathlib import Path
from typing import Optional
import click


class CompletionManager:
    """Manages shell completion installation."""

    SHELLS = ['bash', 'zsh', 'fish']

    @staticmethod
    def get_completion_script(shell: str, command_name: str = 'opsartisan') -> str:
        """
        Get the completion script for a specific shell.

        Args:
            shell: Shell type (bash, zsh, fish)
            command_name: Command name to complete

        Returns:
            Completion script content
        """
        if shell == 'bash':
            return CompletionManager._get_bash_script(command_name)
        elif shell == 'zsh':
            return CompletionManager._get_zsh_script(command_name)
        elif shell == 'fish':
            return CompletionManager._get_fish_script(command_name)
        else:
            raise ValueError(f"Unsupported shell: {shell}")

    @staticmethod
    def _get_bash_script(cmd: str) -> str:
        """Generate bash completion script."""
        return f"""# {cmd} bash completion
_{cmd}_completion() {{
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${{COMP_WORDS[*]}}" \\
                  COMP_CWORD=$COMP_CWORD \\
                  _{cmd.upper()}_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=("$value")
        fi
    done

    return 0
}}

complete -F _{cmd}_completion -o nosort -o bashdefault -o default {cmd}
"""

    @staticmethod
    def _get_zsh_script(cmd: str) -> str:
        """Generate zsh completion script."""
        return f"""#compdef {cmd}

_{cmd}_completion() {{
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[{cmd}] )) && return 1

    response=("${{(@f)$(env COMP_WORDS="${{words[*]}}" \\
                       COMP_CWORD=$((CURRENT-1)) \\
                       _{cmd.upper()}_COMPLETE=zsh_complete {cmd})}}")

    for type value in ${{response[@]}}; do
        if [[ $type == 'plain' ]]; then
            if [[ $value == *:* ]]; then
                completions_with_descriptions+=("$value")
            else
                completions+=("$value")
            fi
        elif [[ $type == 'dir' ]]; then
            _path_files -/
        elif [[ $type == 'file' ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}}

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
    _{cmd}_completion "$@"
else
    compdef _{cmd}_completion {cmd}
fi
"""

    @staticmethod
    def _get_fish_script(cmd: str) -> str:
        """Generate fish completion script."""
        return f"""# {cmd} fish completion

function __{cmd}_completion
    set -l response (env _{cmd.upper()}_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) {cmd})

    for completion in $response
        set -l metadata (string split "," -- $completion)

        if test $metadata[1] = "dir"
            __fish_complete_directories $metadata[2]
        else if test $metadata[1] = "file"
            __fish_complete_path $metadata[2]
        else if test $metadata[1] = "plain"
            echo $metadata[2]
        end
    end
end

complete --no-files --command {cmd} --arguments '(__{cmd}_completion)'
"""

    @staticmethod
    def install_completion(shell: str, command_name: str = 'opsartisan') -> bool:
        """
        Install completion for a specific shell.

        Args:
            shell: Shell type (bash, zsh, fish)
            command_name: Command name

        Returns:
            True if successful
        """
        try:
            script = CompletionManager.get_completion_script(shell, command_name)

            # Determine installation location
            if shell == 'bash':
                completion_dir = Path.home() / '.bash_completion.d'
                completion_dir.mkdir(exist_ok=True)
                completion_file = completion_dir / command_name
            elif shell == 'zsh':
                completion_dir = Path.home() / '.zsh' / 'completion'
                completion_dir.mkdir(parents=True, exist_ok=True)
                completion_file = completion_dir / f'_{command_name}'
            elif shell == 'fish':
                completion_dir = Path.home() / '.config' / 'fish' / 'completions'
                completion_dir.mkdir(parents=True, exist_ok=True)
                completion_file = completion_dir / f'{command_name}.fish'
            else:
                return False

            # Write completion script
            completion_file.write_text(script)

            click.echo(f"Completion installed: {completion_file}")

            # Provide instructions
            if shell == 'bash':
                click.echo("\nAdd this to your ~/.bashrc:")
                click.echo(f"  source {completion_file}")
            elif shell == 'zsh':
                click.echo("\nAdd this to your ~/.zshrc:")
                click.echo(f"  fpath=({completion_dir} $fpath)")
                click.echo("  autoload -Uz compinit && compinit")
            elif shell == 'fish':
                click.echo("\nCompletion will be loaded automatically by fish.")

            click.echo("\nReload your shell or run:")
            click.echo(f"  exec {shell}")

            return True

        except Exception as e:
            click.echo(f"Failed to install completion: {e}", err=True)
            return False

    @staticmethod
    def show_completion_script(shell: str, command_name: str = 'opsartisan'):
        """Print completion script to stdout."""
        try:
            script = CompletionManager.get_completion_script(shell, command_name)
            click.echo(script)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)


def get_template_ids_for_completion() -> list:
    """Get list of template IDs for completion."""
    from opsartisan.core.template_manager import TemplateManager

    manager = TemplateManager()
    templates = manager.list_templates()
    return [t['id'] for t in templates]


def get_preset_names_for_completion() -> list:
    """Get list of preset names for completion."""
    from opsartisan.core.preset_manager import PresetManager

    presets = PresetManager.load_presets()
    return list(presets.keys())