"""AI Orchestrator

The main AI orchestration engine that coordinates workflow management,
context engineering, and AI provider interactions.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from ai.context.memory import ConversationMemory
from ai.context.workflow_context import WorkflowContextEngine
from ai.providers.base import AIProvider, AIResponse, WorkflowAction
from ai.providers.claude import ClaudeProvider
from ai.providers.openai import OpenAIProvider
from core.doc_processor import DocumentProcessor
from core.mcp_manager import MCPManager
from core.scheduler import Scheduler
from core.workflow_engine import WorkflowEngine
from mcp import MCPClient, MCPToolCall

logger = logging.getLogger(__name__)


@dataclass
class AISession:
    """Represents an active AI conversation session"""

    session_id: str
    provider_name: str
    user_id: str
    created_at: str
    last_activity: str
    context_hash: Optional[str] = None


class AIOrchestrator:
    """Main AI orchestration engine"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Initialize core components
        self.workflow_engine = WorkflowEngine()
        self.scheduler = Scheduler()
        self.doc_processor = DocumentProcessor()
        self.mcp_manager = MCPManager()
        self.mcp_client = MCPClient()

        # Initialize AI components
        self.context_engine = WorkflowContextEngine(
            self.workflow_engine, self.scheduler
        )
        self.memory = ConversationMemory()

        # Initialize AI providers
        self.providers: Dict[str, AIProvider] = {}
        self._init_providers()

        # Active sessions
        self.active_sessions: Dict[str, AISession] = {}

        # Define available workflow actions
        self.workflow_actions = self._define_workflow_actions()

    def _init_providers(self):
        """Initialize AI providers based on configuration"""
        provider_configs = self.config.get("providers", {})

        # Claude provider
        if "claude" in provider_configs or not provider_configs:
            try:
                self.providers["claude"] = ClaudeProvider(
                    provider_configs.get("claude", {})
                )
            except Exception as e:
                # Graceful fallback
                pass

        # OpenAI provider
        if "openai" in provider_configs:
            try:
                self.providers["openai"] = OpenAIProvider(
                    provider_configs.get("openai", {})
                )
            except Exception as e:
                # Graceful fallback
                pass

    def _define_workflow_actions(self) -> List[WorkflowAction]:
        """Define actions the AI can take on workflows"""
        return [
            WorkflowAction(
                name="create_workflow",
                description="Create a new workflow from a template or custom content",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Workflow title"},
                        "template": {
                            "type": "string",
                            "description": "Template name (optional)",
                        },
                        "content": {
                            "type": "string",
                            "description": "Custom workflow content (optional)",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Priority level 1-5",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date in ISO format (optional)",
                        },
                    },
                    "required": ["title"],
                },
            ),
            WorkflowAction(
                name="update_workflow_status",
                description="Update the status of a workflow",
                parameters={
                    "type": "object",
                    "properties": {
                        "workflow_id": {"type": "string", "description": "Workflow ID"},
                        "status": {
                            "type": "string",
                            "enum": [
                                "pending",
                                "active",
                                "in_progress",
                                "completed",
                                "cancelled",
                            ],
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional notes about the status change",
                        },
                    },
                    "required": ["workflow_id", "status"],
                },
            ),
            WorkflowAction(
                name="update_action_status",
                description="Mark an action in a workflow as completed or add notes",
                parameters={
                    "type": "object",
                    "properties": {
                        "workflow_id": {"type": "string", "description": "Workflow ID"},
                        "action_index": {
                            "type": "integer",
                            "description": "Action index (0-based)",
                        },
                        "completed": {
                            "type": "boolean",
                            "description": "Whether action is completed",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Notes about the action",
                        },
                    },
                    "required": ["workflow_id", "action_index"],
                },
            ),
            WorkflowAction(
                name="schedule_reminder",
                description="Schedule a reminder or follow-up",
                parameters={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Reminder message",
                        },
                        "scheduled_for": {
                            "type": "string",
                            "description": "When to remind (e.g., 'tomorrow 2pm', '2024-01-15T14:00:00')",
                        },
                        "recurring": {
                            "type": "boolean",
                            "description": "Whether this is a recurring reminder",
                        },
                        "workflow_id": {
                            "type": "string",
                            "description": "Associated workflow ID (optional)",
                        },
                    },
                    "required": ["message", "scheduled_for"],
                },
            ),
            WorkflowAction(
                name="create_document",
                description="Create and version a new document",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Document title"},
                        "content": {
                            "type": "string",
                            "description": "Document content in markdown",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["html", "docx"],
                            "description": "Output format",
                        },
                        "workflow_id": {
                            "type": "string",
                            "description": "Associated workflow ID (optional)",
                        },
                    },
                    "required": ["title", "content"],
                },
            ),
            WorkflowAction(
                name="publish_to_service",
                description="Publish content to an integrated service (JIRA, Confluence, GitHub)",
                parameters={
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "enum": ["jira", "confluence", "github", "slack"],
                        },
                        "action": {
                            "type": "string",
                            "description": "Service-specific action (e.g., 'update_issue', 'publish_page')",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Service-specific parameters",
                        },
                    },
                    "required": ["service", "action", "parameters"],
                },
            ),
        ]

    async def start_conversation(
        self, user_id: str = "default", provider: str = "claude"
    ) -> str:
        """Start a new AI conversation session"""
        if provider not in self.providers:
            available = list(self.providers.keys())
            if available:
                provider = available[0]  # Use first available provider
            else:
                raise ValueError(
                    "No AI providers available. Please configure at least one provider."
                )

        session_id = str(uuid.uuid4())
        session = AISession(
            session_id=session_id,
            provider_name=provider,
            user_id=user_id,
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
        )

        self.active_sessions[session_id] = session
        return session_id

    async def chat(
        self, session_id: str, user_input: str, stream: bool = False
    ) -> Union[AsyncGenerator[str, None], AIResponse]:
        """Engage in conversation with AI"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        session = self.active_sessions[session_id]
        provider = self.providers[session.provider_name]

        # Get current context
        context_snapshot = self.context_engine.get_current_context()
        ai_context = self.context_engine.get_ai_optimized_context(session.provider_name)

        # Get conversation history
        conversation_history = self.memory.get_conversation_history(session_id, limit=5)

        # Build messages
        messages = []

        # Add recent conversation history
        for turn in conversation_history:
            messages.append({"role": "user", "content": turn.user_input})
            messages.append({"role": "assistant", "content": turn.ai_response})

        # Add current user input
        messages.append({"role": "user", "content": user_input})

        # System prompt
        system_prompt = self._build_system_prompt(ai_context, session.user_id)

        # Workflow actions as tools
        tools = [action.to_tool_definition() for action in self.workflow_actions]

        # Add MCP tools
        tools.extend(await self._get_mcp_tools())

        try:
            if stream:
                return self._stream_conversation(
                    provider,
                    messages,
                    tools,
                    system_prompt,
                    session,
                    context_snapshot,
                    user_input,
                )
            else:
                response = await provider.generate(messages, tools, system_prompt)

                # Execute any function calls (including MCP tool calls)
                if response.function_calls:
                    response = await self._execute_function_calls(response, session)

                # Store conversation in memory
                self.memory.add_conversation_turn(
                    session_id,
                    user_input,
                    response.content,
                    context_snapshot.context_hash,
                    actions_taken=(
                        [call for call in response.function_calls]
                        if response.function_calls
                        else []
                    ),
                    metadata={"provider": session.provider_name},
                )

                # Update session
                session.last_activity = datetime.now().isoformat()
                session.context_hash = context_snapshot.context_hash

                # Learn from interaction
                self._learn_from_interaction(session.user_id, user_input, response)

                return response

        except Exception as e:
            # Return error response
            error_response = AIResponse(
                content=f"I encountered an error: {str(e)}. Please try again or check your configuration.",
                metadata={"error": True, "provider": session.provider_name},
            )
            return error_response

    async def _stream_conversation(
        self,
        provider: AIProvider,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        system_prompt: str,
        session: AISession,
        context_snapshot,
        user_input: str,
    ) -> AsyncGenerator[str, None]:
        """Stream conversation response"""
        full_response = ""
        async for chunk in provider.stream(messages, tools, system_prompt):
            full_response += chunk
            yield chunk

        # Store conversation after streaming completes
        self.memory.add_conversation_turn(
            session.session_id,
            user_input,
            full_response,
            context_snapshot.context_hash,
            metadata={"provider": session.provider_name, "streamed": True},
        )

    def _build_system_prompt(self, ai_context: Dict[str, Any], user_id: str) -> str:
        """Build system prompt with current context"""
        prompt_parts = [
            "You are an AI workflow orchestrator for Conductor, helping users manage their daily work efficiently.",
            "",
            "Your primary capabilities:",
            "- Create and manage workflows based on templates or custom content",
            "- Update workflow and action statuses",
            "- Schedule reminders and follow-ups",
            "- Create and publish documentation",
            "- Integrate with external services (JIRA, Confluence, GitHub, Slack)",
            "",
            "Guidelines:",
            "- Be proactive in suggesting next steps based on workflow state",
            "- Prioritize urgent and high-priority items",
            "- Maintain context across conversation turns",
            "- Use available tools to take concrete actions when requested",
            "- Provide clear, actionable recommendations",
            "",
            "Current Workflow Context:",
        ]

        # Add current context
        if ai_context.get("current_workflow"):
            workflow = ai_context["current_workflow"]
            prompt_parts.extend(
                [
                    f"Active Workflow: {workflow.get('title', 'Untitled')}",
                    f"Status: {workflow.get('status', 'unknown')}",
                    f"Priority: {workflow.get('priority', 'medium')}",
                ]
            )

        if ai_context.get("user_focus"):
            prompt_parts.append(f"Current Focus: {ai_context['user_focus']}")

        if ai_context.get("insights"):
            insights = ai_context["insights"]
            if insights.get("recommendations"):
                prompt_parts.append("Recommendations:")
                for rec in insights["recommendations"]:
                    prompt_parts.append(f"- {rec}")

        # Add user preferences from memory
        user_memories = self.memory.recall_context(user_id, "preference")
        if user_memories:
            prompt_parts.append("\nUser Preferences:")
            for memory in user_memories[:3]:  # Top 3 preferences
                prompt_parts.append(f"- {memory.key}: {memory.value}")

        return "\n".join(prompt_parts)

    async def _execute_function_calls(
        self, response: AIResponse, session: AISession
    ) -> AIResponse:
        """Execute AI-requested function calls"""
        if not response.function_calls:
            return response

        execution_results = []

        for call in response.function_calls:
            try:
                result = await self._execute_single_function(call, session)
                execution_results.append(result)
            except Exception as e:
                execution_results.append(
                    {"function": call["name"], "success": False, "error": str(e)}
                )

        # Update response with execution results
        if execution_results:
            response.content += "\n\n" + self._format_execution_results(
                execution_results
            )

        return response

    async def _execute_single_function(
        self, call: Dict[str, Any], session: AISession
    ) -> Dict[str, Any]:
        """Execute a single function call"""
        function_name = call["name"]
        arguments = call.get("arguments", {})

        # Check if this is an MCP tool call
        mcp_call = self._parse_mcp_call(function_name)
        if mcp_call:
            try:
                mcp_call.params = arguments
                result = await self.mcp_client.call_tool(
                    mcp_call.server,
                    mcp_call.tool,
                    mcp_call.params
                )
                return {
                    "function": function_name,
                    "success": True,
                    "result": result
                }
            except Exception as e:
                return {
                    "function": function_name,
                    "success": False,
                    "error": str(e)
                }

        if function_name == "create_workflow":
            result = self.workflow_engine.create_workflow(
                title=arguments["title"],
                template=arguments.get("template"),
                content=arguments.get("content"),
                priority=arguments.get("priority", 3),
                due_date=arguments.get("due_date"),
            )
            return {
                "function": "create_workflow",
                "success": True,
                "workflow_id": result["workflow_id"],
            }

        elif function_name == "update_workflow_status":
            self.workflow_engine.update_workflow_status(
                arguments["workflow_id"], arguments["status"], arguments.get("notes")
            )
            return {"function": "update_workflow_status", "success": True}

        elif function_name == "update_action_status":
            self.workflow_engine.update_action_status(
                arguments["workflow_id"],
                arguments["action_index"],
                completed=arguments.get("completed"),
                notes=arguments.get("notes"),
            )
            return {"function": "update_action_status", "success": True}

        elif function_name == "schedule_reminder":
            reminder_id = self.scheduler.schedule_reminder(
                arguments["message"],
                arguments["scheduled_for"],
                recurring=arguments.get("recurring", False),
                metadata={"workflow_id": arguments.get("workflow_id")},
            )
            return {
                "function": "schedule_reminder",
                "success": True,
                "reminder_id": reminder_id,
            }

        elif function_name == "create_document":
            result = self.doc_processor.create_document(
                title=arguments["title"],
                content=arguments["content"],
                format=arguments.get("format", "html"),
                metadata={"workflow_id": arguments.get("workflow_id")},
            )
            return {
                "function": "create_document",
                "success": True,
                "doc_id": result["doc_id"],
            }

        elif function_name == "publish_to_service":
            result = self.mcp_manager.execute_service_action(
                arguments["service"], arguments["action"], arguments["parameters"]
            )
            return {
                "function": "publish_to_service",
                "success": result.get("success", False),
            }

        else:
            raise ValueError(f"Unknown function: {function_name}")

    def _format_execution_results(self, results: List[Dict[str, Any]]) -> str:
        """Format function execution results for display"""
        if not results:
            return ""

        formatted = ["**Actions Taken:**"]
        for result in results:
            if result["success"]:
                formatted.append(f"✅ {result['function']}: Completed successfully")
            else:
                formatted.append(
                    f"❌ {result['function']}: {result.get('error', 'Failed')}"
                )

        return "\n".join(formatted)

    async def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available MCP tools as tool definitions"""
        mcp_tools = []

        try:
            for server_name in self.mcp_client.get_available_servers():
                tools = await self.mcp_client.list_tools(server_name)
                for tool in tools:
                    mcp_tools.append({
                        "type": "function",
                        "function": {
                            "name": f"mcp_{server_name}_{tool.get('name', '')}",
                            "description": f"[MCP {server_name}] {tool.get('description', '')}",
                            "parameters": tool.get('inputSchema', {
                                "type": "object",
                                "properties": {},
                                "required": []
                            })
                        }
                    })
        except Exception as e:
            logger.error(f"Failed to get MCP tools: {e}")

        return mcp_tools

    def _parse_mcp_call(self, function_name: str) -> Optional[MCPToolCall]:
        """Parse MCP function call from AI response"""
        if not function_name.startswith('mcp_'):
            return None

        try:
            # Extract server and tool from function name: mcp_jira_search_issues
            parts = function_name[4:].split('_', 1)  # Remove 'mcp_' prefix
            if len(parts) < 2:
                return None

            server = parts[0]
            tool = parts[1]

            return MCPToolCall(server=server, tool=tool, params={})
        except Exception:
            return None

    def _learn_from_interaction(
        self, user_id: str, user_input: str, response: AIResponse
    ):
        """Learn patterns from user interactions"""
        # Learn preferred actions
        if response.function_calls:
            preferred_actions = [call["name"] for call in response.function_calls]
            self.memory.learn_from_interaction(
                user_id,
                "preference",
                "preferred_actions",
                preferred_actions,
                confidence=0.8,
            )

        # Learn conversation patterns
        input_lower = user_input.lower()
        if "urgent" in input_lower or "asap" in input_lower:
            self.memory.learn_from_interaction(
                user_id,
                "pattern",
                "urgency_keywords",
                ["urgent", "asap", "immediately"],
                confidence=0.9,
            )

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about an active session"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}

        session = self.active_sessions[session_id]
        return {
            "session_id": session.session_id,
            "provider": session.provider_name,
            "user_id": session.user_id,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "conversation_count": len(self.memory.get_conversation_history(session_id)),
        }

    def list_available_providers(self) -> List[Dict[str, Any]]:
        """List available AI providers"""
        providers = []
        for name, provider in self.providers.items():
            providers.append(
                {
                    "name": name,
                    "model": provider.model,
                    "capabilities": [cap.value for cap in provider.capabilities],
                }
            )
        return providers
