"""Skills System for AI-Callable Workflows

Skills are reusable workflow patterns that the AI can invoke to accomplish
common tasks and workflows. They encapsulate domain knowledge and best practices.
"""

from .base import Skill, SkillExecutionResult, SkillRegistry
from .daily_ops import DailyOperationsSkills
from .documentation import DocumentationSkills
from .project_mgmt import ProjectManagementSkills

__all__ = [
    "Skill",
    "SkillRegistry",
    "SkillExecutionResult",
    "DocumentationSkills",
    "ProjectManagementSkills",
    "DailyOperationsSkills",
]
