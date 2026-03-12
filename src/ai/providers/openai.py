"""OpenAI Provider for GPT models"""

import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp

from ai.providers.base import AICapability, AIProvider, AIProviderError, AIResponse


class OpenAIProvider(AIProvider):
    """Provider for OpenAI's GPT models"""

    def __init__(self, config: Dict[str, Any]):
        # Set default config values
        default_config = {
            "model": "gpt-4",
            "max_tokens": 4096,
            "temperature": 0.1,
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": "https://api.openai.com/v1",
        }
        default_config.update(config)
        super().__init__(default_config)

        if not self.config.get("api_key"):
            raise AIProviderError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable."
            )

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self.config["model"]

    def _get_capabilities(self) -> List[AICapability]:
        return [
            AICapability.TEXT_GENERATION,
            AICapability.FUNCTION_CALLING,
            AICapability.STRUCTURED_OUTPUT,
            AICapability.STREAMING,
        ]

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate response using OpenAI API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config['api_key']}",
            }

            # Prepare messages with system prompt if provided
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})

            # Add user messages (skip any existing system messages if system_prompt provided)
            for msg in messages:
                if system_prompt and msg["role"] == "system":
                    continue
                formatted_messages.append(msg)

            # Format request
            request_data = {
                "model": self.model,
                "messages": formatted_messages,
                "max_tokens": kwargs.get("max_tokens", self.config["max_tokens"]),
                "temperature": kwargs.get("temperature", self.config["temperature"]),
            }

            if tools and self.supports_capability(AICapability.FUNCTION_CALLING):
                request_data["tools"] = tools
                request_data["tool_choice"] = kwargs.get("tool_choice", "auto")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/chat/completions",
                    headers=headers,
                    json=request_data,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AIProviderError(f"OpenAI API error: {error_text}")

                    result = await response.json()

                    if "error" in result:
                        raise AIProviderError(
                            f"OpenAI API error: {result['error']['message']}"
                        )

                    choice = result["choices"][0]
                    message = choice["message"]

                    content = message.get("content", "")
                    function_calls = []

                    # Handle function calls
                    if "tool_calls" in message:
                        for tool_call in message["tool_calls"]:
                            function_calls.append(
                                {
                                    "name": tool_call["function"]["name"],
                                    "arguments": json.loads(
                                        tool_call["function"]["arguments"]
                                    ),
                                    "id": tool_call["id"],
                                }
                            )

                    return AIResponse(
                        content=content,
                        usage=result.get("usage", {}),
                        function_calls=function_calls,
                        metadata={"model": self.model, "provider": "openai"},
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
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream response using OpenAI API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config['api_key']}",
            }

            # Prepare messages
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})

            for msg in messages:
                if system_prompt and msg["role"] == "system":
                    continue
                formatted_messages.append(msg)

            request_data = {
                "model": self.model,
                "messages": formatted_messages,
                "max_tokens": kwargs.get("max_tokens", self.config["max_tokens"]),
                "temperature": kwargs.get("temperature", self.config["temperature"]),
                "stream": True,
            }

            if tools and self.supports_capability(AICapability.FUNCTION_CALLING):
                request_data["tools"] = tools

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/chat/completions",
                    headers=headers,
                    json=request_data,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AIProviderError(f"OpenAI API error: {error_text}")

                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue

        except aiohttp.ClientError as e:
            raise AIProviderError(f"Network error: {e}")
        except Exception as e:
            raise AIProviderError(f"Unexpected error: {e}")

    def format_workflow_context(self, context: Dict[str, Any]) -> str:
        """Format workflow context optimized for OpenAI models"""
        formatted = ["# Conductor Workflow Assistant"]

        if "current_workflow" in context:
            workflow = context["current_workflow"]
            formatted.append(
                f"\n## Current Workflow: {workflow.get('title', 'Untitled')}"
            )
            formatted.append(f"Status: {workflow.get('status', 'unknown')}")
            formatted.append(f"Priority: {workflow.get('priority', 'medium')}")

            if "actions" in workflow:
                completed = sum(
                    1 for action in workflow["actions"] if action.get("completed")
                )
                total = len(workflow["actions"])
                formatted.append(f"Progress: {completed}/{total} actions completed")

                formatted.append("\n### Actions:")
                for i, action in enumerate(workflow["actions"], 1):
                    status = "✓" if action.get("completed") else "○"
                    formatted.append(
                        f"{status} {i}. {action.get('description', 'No description')}"
                    )

        if "schedule" in context and context["schedule"]:
            formatted.append("\n## Today's Schedule:")
            for item in context["schedule"]:
                formatted.append(
                    f"• {item.get('time', 'No time')}: {item.get('description', 'No description')}"
                )

        if "related_workflows" in context and context["related_workflows"]:
            formatted.append("\n## Related Workflows:")
            for workflow in context["related_workflows"]:
                formatted.append(
                    f"• {workflow.get('title', 'Untitled')} ({workflow.get('status', 'unknown')})"
                )

        return "\n".join(formatted)
