"""File operation utilities."""

import shutil
from pathlib import Path


def copy_directory(source: Path, dest: Path, overwrite: bool = False):
    """Copy a directory tree."""
    if dest.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists: {dest}")

    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(source, dest)


def ensure_directory(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)
