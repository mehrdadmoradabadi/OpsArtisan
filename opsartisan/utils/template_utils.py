"""Template-related utility functions."""

import json
from pathlib import Path
from typing import Dict, Any


def load_descriptor(path: Path) -> Dict[str, Any]:
    """Load a template descriptor file."""
    with open(path) as f:
        return json.load(f)


def validate_descriptor(descriptor: Dict[str, Any]) -> bool:
    """Validate a template descriptor has required fields."""
    required_fields = ['id', 'title', 'prompts', 'outputs']
    return all(field in descriptor for field in required_fields)
