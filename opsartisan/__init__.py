"""
OpsArtisan - CLI-first assistant for sysadmins and DevOps engineers.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from opsartisan.core.template_manager import TemplateManager
from opsartisan.core.preset_manager import PresetManager
from opsartisan.core.validator import Validator
from opsartisan.core.prompter import InteractivePrompter

__all__ = [
    "TemplateManager",
    "PresetManager",
    "Validator",
    "InteractivePrompter",
]
