"""Interactive prompting with questionary or fallback."""

from typing import Dict, List, Any
import click

from opsartisan.config import HAS_QUESTIONARY

if HAS_QUESTIONARY:
    import questionary


class InteractivePrompter:
    """Handles interactive prompts using questionary or fallback."""

    @staticmethod
    def prompt(
        prompts: List[Dict[str, Any]],
        use_defaults: bool = False
    ) -> Dict[str, Any]:
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
                    answer = questionary.text(
                        label,
                        default=str(default)
                    ).ask()
                elif prompt_type == 'confirm':
                    answer = questionary.confirm(
                        label,
                        default=bool(default)
                    ).ask()
                elif prompt_type == 'select':
                    answer = questionary.select(
                        label,
                        choices=choices,
                        default=default
                    ).ask()
                elif prompt_type == 'number':
                    answer = questionary.text(
                        label,
                        default=str(default)
                    ).ask()
                    try:
                        answer = int(answer)
                    except ValueError:
                        answer = default
                else:
                    answer = questionary.text(
                        label,
                        default=str(default)
                    ).ask()
            else:
                # Fallback to input()
                if prompt_type == 'confirm':
                    answer = input(
                        f"{label} [y/N]: "
                    ).lower() in ('y', 'yes')
                elif prompt_type == 'select':
                    click.echo(f"{label}")
                    for i, choice in enumerate(choices, 1):
                        click.echo(f"  {i}. {choice}")
                    choice_idx = input(
                        f"Select (1-{len(choices)}) [1]: "
                    ) or "1"
                    try:
                        answer = choices[int(choice_idx) - 1]
                    except (ValueError, IndexError):
                        answer = choices[0] if choices else default
                else:
                    answer = input(f"{label} [{default}]: ") or default

            answers[prompt_id] = answer

        return answers
