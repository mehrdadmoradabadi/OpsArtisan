"""Preset management for saving and loading configurations."""

import json
from typing import Dict, Any, Optional

from opsartisan.config import PRESETS_FILE, USER_CONFIG_DIR


class PresetManager:
    """Manages saved presets."""

    @staticmethod
    def load_presets() -> Dict[str, Any]:
        """Load presets from file."""
        if not PRESETS_FILE.exists():
            return {}
        try:
            with open(PRESETS_FILE) as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def save_preset(name: str, template_id: str, answers: Dict[str, Any]):
        """Save a preset."""
        presets = PresetManager.load_presets()
        presets[name] = {
            'template_id': template_id,
            'answers': answers
        }
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(PRESETS_FILE, 'w') as f:
            json.dump(presets, f, indent=2)

    @staticmethod
    def get_preset(name: str) -> Optional[Dict[str, Any]]:
        """Get a specific preset."""
        presets = PresetManager.load_presets()
        return presets.get(name)

    @staticmethod
    def delete_preset(name: str) -> bool:
        """Delete a preset."""
        presets = PresetManager.load_presets()
        if name not in presets:
            return False

        del presets[name]

        with open(PRESETS_FILE, 'w') as f:
            json.dump(presets, f, indent=2)

        return True

    @staticmethod
    def list_presets() -> Dict[str, Any]:
        """List all presets with their metadata."""
        return PresetManager.load_presets()
