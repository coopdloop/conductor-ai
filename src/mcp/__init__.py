"""MCP (Model Context Protocol) Integration

This package provides MCP client implementation for Conductor,
enabling skills to use external tools through MCP servers.
"""

from .client import MCPClient, MCPServerConfig, MCPToolCall
from .bridge import MCPBridge

__all__ = ['MCPClient', 'MCPServerConfig', 'MCPToolCall', 'MCPBridge']