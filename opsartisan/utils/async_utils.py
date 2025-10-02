"""Async utilities for parallel validation and operations."""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import click
from concurrent.futures import ThreadPoolExecutor, as_completed


class AsyncValidator:
    """Run validators in parallel for faster feedback."""

    @staticmethod
    async def run_validators_async(
            validators: List[Dict[str, Any]],
            working_dir: Path,
            max_workers: int = 4
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Run multiple validators in parallel.

        Returns:
            (all_passed, results) tuple
        """
        if not validators:
            return True, []

        click.echo("Running validators in parallel...")

        # Create progress indicator
        total = len(validators)
        completed = 0

        def update_progress():
            nonlocal completed
            completed += 1
            click.echo(f"  Progress: {completed}/{total}", nl=False)
            click.echo('\r', nl=False)

        loop = asyncio.get_event_loop()

        # Run validators in thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for validator in validators:
                future = loop.run_in_executor(
                    executor,
                    AsyncValidator._run_single_validator,
                    validator,
                    working_dir
                )
                futures.append(future)

            # Wait for all to complete
            results = []
            for future in asyncio.as_completed(futures):
                result = await future
                results.append(result)
                update_progress()

        click.echo()  # New line after progress

        # Display results
        all_passed = True
        for result in results:
            if result['success']:
                click.echo(click.style(f"  ✓ {result['description']}", fg='green'))
            else:
                click.echo(click.style(f"  ✗ {result['description']}", fg='red'))
                if result.get('error'):
                    click.echo(f"    {result['error']}")
                all_passed = False

        return all_passed, results

    @staticmethod
    def _run_single_validator(
            validator: Dict[str, Any],
            working_dir: Path
    ) -> Dict[str, Any]:
        """Run a single validator synchronously."""
        cmd = validator.get('command', '')
        description = validator.get('description', cmd)
        timeout = validator.get('timeout', 30)

        result = {
            'description': description,
            'command': cmd,
            'success': False,
            'output': '',
            'error': ''
        }

        try:
            proc_result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(working_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            result['success'] = proc_result.returncode == 0
            result['output'] = proc_result.stdout
            result['error'] = proc_result.stderr

        except subprocess.TimeoutExpired:
            result['error'] = f"Timed out after {timeout}s"
        except Exception as e:
            result['error'] = str(e)

        return result


class ProgressIndicator:
    """Show progress for long-running operations."""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_index = 0

    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        self._render()

    def _render(self):
        """Render progress bar."""
        if self.total > 0:
            percent = int((self.current / self.total) * 100)
            bar_length = 30
            filled = int(bar_length * self.current / self.total)
            bar = '█' * filled + '░' * (bar_length - filled)

            spinner = self.spinner_chars[self.spinner_index % len(self.spinner_chars)]
            self.spinner_index += 1

            click.echo(
                f"\r{spinner} {self.description}: [{bar}] {percent}% ({self.current}/{self.total})",
                nl=False
            )
        else:
            spinner = self.spinner_chars[self.spinner_index % len(self.spinner_chars)]
            self.spinner_index += 1
            click.echo(f"\r{spinner} {self.description}...", nl=False)

    def finish(self):
        """Complete the progress indicator."""
        click.echo()  # New line


class BatchProcessor:
    """Process multiple templates or operations in batches."""

    @staticmethod
    async def process_batch(
            items: List[Any],
            processor_func,
            batch_size: int = 5,
            description: str = "Processing"
    ) -> List[Any]:
        """
        Process items in batches asynchronously.

        Args:
            items: List of items to process
            processor_func: Async function to process each item
            batch_size: Number of items to process concurrently
            description: Description for progress indicator

        Returns:
            List of results
        """
        results = []
        progress = ProgressIndicator(len(items), description)

        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[processor_func(item) for item in batch],
                return_exceptions=True
            )

            results.extend(batch_results)
            progress.update(len(batch))

        progress.finish()
        return results