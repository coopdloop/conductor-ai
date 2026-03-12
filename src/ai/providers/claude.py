"""Claude Provider for Anthropic's Claude models"""

import os
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp
import asyncio

from ai.providers.base import AIProvider, AIResponse, AIProviderError, AICapability


class ClaudeProvider(AIProvider):
    """Provider for Anthropic's Claude models"""

    def __init__(self, config: Dict[str, Any]):
        # Set default config values
        default_config = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 4096,
            "temperature": 0.1,
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "base_url": "https://api.anthropic.com/v1"
        }
        default_config.update(config)
        super().__init__(default_config)

        if not self.config.get("api_key"):
            raise AIProviderError("Claude API key not provided. Set ANTHROPIC_API_KEY environment variable.")

    @property
    def name(self) -> str:
        return "claude"

    @property
    def model(self) -> str:
        return self.config["model"]

    def _get_capabilities(self) -> List[AICapability]:
        return [
            AICapability.TEXT_GENERATION,
            # AICapability.FUNCTION_CALLING,  # Temporarily disabled due to API format changes
            AICapability.STRUCTURED_OUTPUT,
            AICapability.STREAMING,
            AICapability.CONTEXT_EXTENSION
        ]

    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for Claude API"""
        formatted = []
        for msg in messages:
            # Claude expects specific roles
            role = msg["role"]
            if role == "system":
                # System messages are handled separately in Claude
                continue
            elif role in ["user", "assistant"]:
                formatted.append({
                    "role": role,
                    "content": msg["content"]
                })
        return formatted

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response using Claude API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.config["api_key"],
                "anthropic-version": "2023-06-01"
            }

            # Extract system message if present
            system_message = system_prompt
            if not system_message:
                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                        break

            # Format request
            request_data = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", self.config["max_tokens"]),
                "temperature": kwargs.get("temperature", self.config["temperature"]),
                "messages": self._format_messages(messages)
            }

            if system_message:
                request_data["system"] = system_message

            if tools and self.supports_capability(AICapability.FUNCTION_CALLING):
                request_data["tools"] = tools

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/messages",
                    headers=headers,
                    json=request_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AIProviderError(f"Claude API error: {error_text}")

                    result = await response.json()

                    # Extract content
                    content = ""
                    function_calls = []

                    if "content" in result:
                        for item in result["content"]:
                            if item["type"] == "text":
                                content += item["text"]
                            elif item["type"] == "tool_use":
                                function_calls.append({
                                    "name": item["name"],
                                    "arguments": item["input"],
                                    "id": item.get("id")
                                })

                    return AIResponse(
                        content=content,
                        usage=result.get("usage", {}),
                        function_calls=function_calls,
                        metadata={"model": self.model, "provider": "claude"}
                    )

        except aiohttp.ClientError as e:
            raise AIProviderError(f"Network error: {e}")
        except Exception as e:
            raise AIProviderError(f"Unexpected error: {e}")

    async def stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response using Claude API"""
        # For now, fall back to regular generation and yield the result
        # TODO: Implement proper streaming when Claude streaming API is stable
        response = await self.generate(messages, tools, system_prompt, **kwargs)
        yield response.content

    def format_workflow_context(self, context: Dict[str, Any]) -> str:
        """Format workflow context optimized for Claude"""
        formatted = ["# Conductor Workflow Context"]

        if "current_workflow" in context:
            workflow = context["current_workflow"]
            formatted.append(f"\n## Active Workflow: {workflow.get('title', 'Untitled')}")
            formatted.append(f"- **Status:** {workflow.get('status', 'unknown')}")
            formatted.append(f"- **Priority:** {workflow.get('priority', 'medium')}")
            formatted.append(f"- **ID:** {workflow.get('id', 'unknown')}")

            if workflow.get("description"):
                formatted.append(f"- **Description:** {workflow['description']}")

            if "actions" in workflow:
                formatted.append("\n### Current Actions:")
                for i, action in enumerate(workflow["actions"], 1):
                    status = "✅ Completed" if action.get("completed") else "⏳ Pending"
                    formatted.append(f"{i}. **{status}** - {action.get('description', 'No description')}")
                    if action.get("notes"):
                        formatted.append(f"   *Notes: {action['notes']}*")

        if "recent_activity" in context:
            formatted.append("\n## Recent Activity:")
            for activity in context["recent_activity"][-5:]:  # Last 5 activities
                formatted.append(f"- {activity.get('timestamp', 'Unknown time')}: {activity.get('description', 'No description')}")

        if "schedule" in context and context["schedule"]:
            formatted.append("\n## Today's Schedule:")
            for item in context["schedule"]:
                time_str = item.get('time', 'No time')
                desc = item.get('description', 'No description')
                priority = item.get('priority', 'normal')
                formatted.append(f"- **{time_str}** ({priority} priority): {desc}")

        if "related_workflows" in context and context["related_workflows"]:
            formatted.append("\n## Related Workflows:")
            for workflow in context["related_workflows"]:
                title = workflow.get('title', 'Untitled')
                status = workflow.get('status', 'unknown')
                formatted.append(f"- **{title}** - Status: {status}")

        return "\n".join(formatted)