"""Configuration and constants for OpsArtisan."""

from pathlib import Path
# Version
__version__ = "0.1.0"

# Configuration paths
USER_CONFIG_DIR = Path.home() / ".opsartisan"
USER_TEMPLATES_DIR = USER_CONFIG_DIR / "templates"
PRESETS_FILE = USER_CONFIG_DIR / "presets.json"
LOCAL_TEMPLATES_DIR = Path("./templates")
SYSTEM_TEMPLATES_DIR = Path("/usr/share/opsartisan/templates")

# Questionary availability
try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False