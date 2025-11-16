"""Template system for issue creation."""

from .instruction_template import (
    InstructionTemplate,
    InstructionTemplateManager,
    InstructionTemplateParser,
    TaskDefinition,
)
from .template_manager import Template, TemplateManager

__all__ = [
    "Template",
    "TemplateManager",
    "InstructionTemplate",
    "InstructionTemplateManager",
    "InstructionTemplateParser",
    "TaskDefinition",
]
