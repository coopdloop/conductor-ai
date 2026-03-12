"""Base Skill System

Provides the foundation for AI-callable workflow skills that can be
composed and chained together to accomplish complex tasks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import json
from datetime import datetime


class SkillStatus(Enum):
    """Skill execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SkillExecutionResult:
    """Result of skill execution"""
    skill_name: str
    status: SkillStatus
    output: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class SkillParameter:
    """Parameter definition for a skill"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    options: List[str] = None

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format"""
        schema = {
            "type": self.type,
            "description": self.description
        }

        if self.options:
            schema["enum"] = self.options

        if self.default is not None:
            schema["default"] = self.default

        return schema


class Skill(ABC):
    """Base class for all skills"""

    def __init__(self):
        self.execution_history: List[SkillExecutionResult] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """Skill name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Skill description"""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Skill category (e.g., 'documentation', 'project_mgmt')"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[SkillParameter]:
        """Skill parameters"""
        pass

    @property
    def dependencies(self) -> List[str]:
        """Other skills this skill depends on"""
        return []

    @abstractmethod
    async def execute(
        self,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None
    ) -> SkillExecutionResult:
        """Execute the skill"""
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize parameters"""
        validated = {}
        errors = []

        for param in self.parameters:
            value = parameters.get(param.name)

            if value is None:
                if param.required:
                    errors.append(f"Required parameter '{param.name}' is missing")
                    continue
                else:
                    value = param.default

            # Basic type checking
            if param.type == "string" and not isinstance(value, str):
                try:
                    value = str(value)
                except:
                    errors.append(f"Parameter '{param.name}' must be a string")
                    continue

            elif param.type == "integer" and not isinstance(value, int):
                try:
                    value = int(value)
                except:
                    errors.append(f"Parameter '{param.name}' must be an integer")
                    continue

            elif param.type == "boolean" and not isinstance(value, bool):
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    errors.append(f"Parameter '{param.name}' must be a boolean")
                    continue

            # Check options
            if param.options and value not in param.options:
                errors.append(f"Parameter '{param.name}' must be one of: {param.options}")
                continue

            validated[param.name] = value

        if errors:
            raise ValueError(f"Parameter validation failed: {'; '.join(errors)}")

        return validated

    def to_schema(self) -> Dict[str, Any]:
        """Convert skill to JSON schema for AI providers"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    async def _log_execution(self, result: SkillExecutionResult):
        """Log skill execution for learning and debugging"""
        self.execution_history.append(result)
        # Keep only recent executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-50:]


class CompositeSkill(Skill):
    """Skill that combines multiple sub-skills"""

    def __init__(self, sub_skills: List[Skill]):
        super().__init__()
        self.sub_skills = sub_skills

    async def execute(
        self,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None
    ) -> SkillExecutionResult:
        """Execute all sub-skills in sequence"""
        start_time = datetime.now()
        results = []
        combined_output = {}

        try:
            for skill in self.sub_skills:
                # Pass context and accumulated output to each skill
                skill_context = {**context, "previous_outputs": combined_output}
                result = await skill.execute(skill_context, parameters, orchestrator)
                results.append(result)

                if result.status == SkillStatus.FAILED:
                    # Stop execution on first failure
                    raise Exception(f"Sub-skill {skill.name} failed: {result.error}")

                combined_output[skill.name] = result.output

            execution_time = (datetime.now() - start_time).total_seconds()

            result = SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.COMPLETED,
                output=combined_output,
                execution_time=execution_time,
                metadata={"sub_skill_results": [r.to_dict() for r in results]}
            )

            await self._log_execution(result)
            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            result = SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                output=combined_output,
                execution_time=execution_time,
                error=str(e),
                metadata={"sub_skill_results": [r.to_dict() for r in results]}
            )

            await self._log_execution(result)
            return result


class SkillRegistry:
    """Registry for managing available skills"""

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.skill_categories: Dict[str, List[str]] = {}

    def register(self, skill: Skill):
        """Register a skill"""
        self.skills[skill.name] = skill

        category = skill.category
        if category not in self.skill_categories:
            self.skill_categories[category] = []

        if skill.name not in self.skill_categories[category]:
            self.skill_categories[category].append(skill.name)

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self.skills.get(name)

    def list_skills(self, category: str = None) -> List[Dict[str, Any]]:
        """List available skills"""
        skills = []

        for skill_name, skill in self.skills.items():
            if category and skill.category != category:
                continue

            skills.append({
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required
                    }
                    for p in skill.parameters
                ]
            })

        return skills

    def get_categories(self) -> List[str]:
        """Get available skill categories"""
        return list(self.skill_categories.keys())

    def get_skills_for_ai(self) -> List[Dict[str, Any]]:
        """Get skills formatted as AI tool definitions"""
        return [skill.to_schema() for skill in self.skills.values()]

    async def execute_skill(
        self,
        skill_name: str,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None
    ) -> SkillExecutionResult:
        """Execute a skill by name"""
        skill = self.get_skill(skill_name)
        if not skill:
            return SkillExecutionResult(
                skill_name=skill_name,
                status=SkillStatus.FAILED,
                output={},
                execution_time=0,
                error=f"Skill '{skill_name}' not found"
            )

        try:
            # Validate parameters
            validated_params = skill.validate_parameters(parameters)

            # Execute skill
            result = await skill.execute(context, validated_params, orchestrator)
            return result

        except Exception as e:
            return SkillExecutionResult(
                skill_name=skill_name,
                status=SkillStatus.FAILED,
                output={},
                execution_time=0,
                error=str(e)
            )

    def create_composite_skill(
        self,
        name: str,
        description: str,
        category: str,
        skill_names: List[str]
    ) -> Optional[CompositeSkill]:
        """Create a composite skill from existing skills"""
        skills = []
        for skill_name in skill_names:
            skill = self.get_skill(skill_name)
            if not skill:
                return None
            skills.append(skill)

        class DynamicCompositeSkill(CompositeSkill):
            @property
            def name(self) -> str:
                return name

            @property
            def description(self) -> str:
                return description

            @property
            def category(self) -> str:
                return category

            @property
            def parameters(self) -> List[SkillParameter]:
                # Combine parameters from all sub-skills
                all_params = []
                for skill in skills:
                    all_params.extend(skill.parameters)
                return all_params

        composite = DynamicCompositeSkill(skills)
        self.register(composite)
        return composite