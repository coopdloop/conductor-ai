"""MCP (Model Context Protocol) Client Implementation

Connects Conductor to local MCP servers for external tool integrations.
Supports both standalone MCP servers and VSCode MCP extension bridges.
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


class MCPServerConfig:
    """Configuration for an MCP server"""

    def __init__(self, name: str, command: str, args: List[str], env: Dict[str, str] = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.process: Optional[subprocess.Popen] = None
        self.port: Optional[int] = None


class MCPClient:
    """Client for communicating with MCP servers"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / '.conductor' / 'mcp' / 'config.json'
        self.servers: Dict[str, MCPServerConfig] = {}
        self.connections: Dict[str, aiohttp.ClientSession] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load MCP server configurations"""
        if not self.config_path.exists():
            logger.info(f"No MCP config found at {self.config_path}")
            return

        try:
            with open(self.config_path) as f:
                config_data = json.load(f)

            for server_name, server_config in config_data.get('mcpServers', {}).items():
                self.servers[server_name] = MCPServerConfig(
                    name=server_name,
                    command=server_config['command'],
                    args=server_config.get('args', []),
                    env=server_config.get('env', {})
                )
                logger.info(f"Loaded MCP server config: {server_name}")

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")

    async def start_server(self, server_name: str) -> bool:
        """Start an MCP server process"""
        if server_name not in self.servers:
            logger.error(f"Unknown MCP server: {server_name}")
            return False

        server = self.servers[server_name]

        if server.process and server.process.poll() is None:
            logger.info(f"MCP server {server_name} already running")
            return True

        try:
            # Find available port
            server.port = await self._find_available_port()

            # Prepare environment
            env = {**server.env, 'MCP_PORT': str(server.port)}

            # Start the server process
            cmd = [server.command] + server.args + ['--port', str(server.port)]
            server.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            await self._wait_for_server_start(server_name, server.port)

            logger.info(f"Started MCP server {server_name} on port {server.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start MCP server {server_name}: {e}")
            return False

    async def stop_server(self, server_name: str) -> bool:
        """Stop an MCP server process"""
        if server_name not in self.servers:
            return False

        server = self.servers[server_name]

        if server.process:
            try:
                server.process.terminate()
                await asyncio.sleep(1)
                if server.process.poll() is None:
                    server.process.kill()
                logger.info(f"Stopped MCP server {server_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to stop MCP server {server_name}: {e}")

        return False

    async def call_tool(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")

        server = self.servers[server_name]

        # Ensure server is running
        if not server.process or server.process.poll() is not None:
            success = await self.start_server(server_name)
            if not success:
                raise RuntimeError(f"Failed to start MCP server: {server_name}")

        # Get or create connection
        if server_name not in self.connections:
            self.connections[server_name] = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

        session = self.connections[server_name]

        try:
            # Make the MCP tool call
            payload = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params
                }
            }

            url = f"http://localhost:{server.port}/mcp"
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if 'error' in result:
                        raise RuntimeError(f"MCP tool error: {result['error']}")
                    return result.get('result', {})
                else:
                    raise RuntimeError(f"MCP server error: {response.status}")

        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            raise

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools on an MCP server"""
        try:
            result = await self.call_tool(server_name, "list_tools", {})
            return result.get('tools', [])
        except Exception as e:
            logger.error(f"Failed to list tools for {server_name}: {e}")
            return []

    async def test_connection(self, server_name: str) -> bool:
        """Test connection to an MCP server"""
        try:
            await self.list_tools(server_name)
            return True
        except Exception:
            return False

    def get_available_servers(self) -> List[str]:
        """Get list of configured server names"""
        return list(self.servers.keys())

    async def _find_available_port(self, start_port: int = 8000) -> int:
        """Find an available port for MCP server"""
        for port in range(start_port, start_port + 100):
            try:
                # Try to bind to the port
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise RuntimeError("No available ports found")

    async def _wait_for_server_start(self, server_name: str, port: int, timeout: int = 10) -> None:
        """Wait for MCP server to start accepting connections"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:{port}/health") as response:
                        if response.status == 200:
                            return
            except Exception:
                pass

            await asyncio.sleep(0.5)

        raise RuntimeError(f"MCP server {server_name} failed to start within {timeout}s")

    async def close(self) -> None:
        """Close all connections and stop servers"""
        # Close HTTP connections
        for session in self.connections.values():
            await session.close()
        self.connections.clear()

        # Stop all servers
        for server_name in list(self.servers.keys()):
            await self.stop_server(server_name)


class MCPToolCall:
    """Represents an MCP tool call for use in AI conversations"""

    def __init__(self, server: str, tool: str, params: Dict[str, Any]):
        self.server = server
        self.tool = tool
        self.params = params

    @classmethod
    def parse(cls, tool_call_str: str) -> Optional['MCPToolCall']:
        """Parse MCP tool call from string format: mcp://server/tool"""
        if not tool_call_str.startswith('mcp://'):
            return None

        try:
            # Remove mcp:// prefix
            call_path = tool_call_str[6:]

            # Split server/tool
            if '/' not in call_path:
                return None

            server, tool = call_path.split('/', 1)

            return cls(server=server, tool=tool, params={})

        except Exception:
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'type': 'mcp_tool_call',
            'server': self.server,
            'tool': self.tool,
            'params': self.params
        }

    def __str__(self) -> str:
        return f"mcp://{self.server}/{self.tool}"