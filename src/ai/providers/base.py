"""Base AI Provider Interface

Defines the contract that all AI providers must implement to work with Conductor.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional


class AICapability(Enum):
    """AI provider capabilities"""

    TEXT_GENERATION = "text_generation"
    FUNCTION_CALLING = "function_calling"
    STRUCTURED_OUTPUT = "structured_output"
    STREAMING = "streaming"
    CONTEXT_EXTENSION = "context_extension"


@dataclass
class AIResponse:
    """Response from AI provider"""

    content: str
    usage: Dict[str, int] = None
    function_calls: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content": self.content,
            "usage": self.usage or {},
            "function_calls": self.function_calls or [],
            "metadata": self.metadata or {},
        }


class AIProviderError(Exception):
    """Base exception for AI provider errors"""

    pass


class AIProvider(ABC):
    """Base class for AI providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._capabilities = self._get_capabilities()

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Current model being used"""
        pass

    @abstractmethod
    def _get_capabilities(self) -> List[AICapability]:
        """Get provider capabilities"""
        pass

    @property
    def capabilities(self) -> List[AICapability]:
        """Available capabilities"""
        return self._capabilities

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate response from messages"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream response from messages"""
        pass

    async def test_connection(self) -> Dict[str, Any]:
        """Test provider connection"""
        try:
            response = await self.generate(
                [{"role": "user", "content": "Test connection"}]
            )
            return {
                "success": True,
                "provider": self.name,
                "model": self.model,
                "capabilities": [cap.value for cap in self.capabilities],
            }
        except Exception as e:
            return {"success": False, "provider": self.name, "error": str(e)}

    def supports_capability(self, capability: AICapability) -> bool:
        """Check if provider supports capability"""
        return capability in self.capabilities

    def format_workflow_context(self, context: Dict[str, Any]) -> str:
        """Format workflow context for this provider"""
        # Default implementation - can be overridden by providers
        formatted = []

        if "current_workflow" in context:
            workflow = context["current_workflow"]
            formatted.append(
                f"## Current Workflow: {workflow.get('title', 'Untitled')}"
            )
            formatted.append(f"Status: {workflow.get('status', 'unknown')}")
            formatted.append(f"Priority: {workflow.get('priority', 'medium')}")

            if "actions" in workflow:
                formatted.append("### Actions:")
                for i, action in enumerate(workflow["actions"], 1):
                    status = "✅" if action.get("completed") else "⏳"
                    formatted.append(
                        f"{i}. {status} {action.get('description', 'No description')}"
                    )

        if "related_workflows" in context:
            formatted.append("### Related Workflows:")
            for workflow in context["related_workflows"]:
                formatted.append(
                    f"- {workflow.get('title', 'Untitled')} ({workflow.get('status', 'unknown')})"
                )

        if "schedule" in context:
            formatted.append("### Today's Schedule:")
            for item in context["schedule"]:
                formatted.append(
                    f"- {item.get('time', 'No time')}: {item.get('description', 'No description')}"
                )

        return "\n".join(formatted)


class WorkflowAction:
    """Represents an action the AI can take on workflows"""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters

    def to_tool_definition(self) -> Dict[str, Any]:
        """Convert to tool definition for AI providers"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
