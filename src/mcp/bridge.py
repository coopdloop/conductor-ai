"""MCP Bridge Implementation

Bridges between VSCode MCP extensions and Conductor's Claude API calls.
Provides compatibility layer for users with existing VSCode MCP setups.
"""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import MCPClient

logger = logging.getLogger(__name__)


class VSCodeMCPConfig:
    """Parser for VSCode MCP configuration"""

    @staticmethod
    def get_vscode_settings_path() -> Path:
        """Get VSCode settings.json path for current platform"""
        home = Path.home()

        if os.name == 'nt':  # Windows
            return home / 'AppData' / 'Roaming' / 'Code' / 'User' / 'settings.json'
        elif os.name == 'posix':  # macOS/Linux
            if 'darwin' in os.uname().sysname.lower():  # macOS
                return home / 'Library' / 'Application Support' / 'Code' / 'User' / 'settings.json'
            else:  # Linux
                return home / '.config' / 'Code' / 'User' / 'settings.json'

        raise RuntimeError("Unsupported operating system")

    @classmethod
    def extract_mcp_config(cls) -> Dict[str, Any]:
        """Extract MCP configuration from VSCode settings"""
        settings_path = cls.get_vscode_settings_path()

        if not settings_path.exists():
            logger.warning(f"VSCode settings not found at {settings_path}")
            return {}

        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try to parse JSON, handling common VSCode settings.json issues
            try:
                settings = json.loads(content)
            except json.JSONDecodeError as json_err:
                # VSCode settings.json often has comments or trailing commas
                logger.warning(f"VSCode settings.json has formatting issues: {json_err}")

                # Try to clean up common issues
                import re
                # Remove comments
                content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
                # Remove trailing commas before } or ]
                content = re.sub(r',(\s*[}\]])', r'\1', content)

                try:
                    settings = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Could not parse VSCode settings.json even after cleanup")
                    return {}

            # Look for MCP-related settings
            mcp_config = {}

            # Extract Claude Desktop MCP config
            if 'claude.mcpServers' in settings:
                mcp_config['claude'] = settings['claude.mcpServers']

            # Extract other MCP extensions
            for key, value in settings.items():
                if 'mcp' in key.lower() and isinstance(value, dict):
                    service_name = key.split('.')[-1] if '.' in key else key
                    mcp_config[service_name] = value

            return mcp_config

        except Exception as e:
            logger.warning(f"Failed to parse VSCode settings: {e}")
            return {}


class MCPBridge:
    """Bridge between VSCode MCP and Conductor"""

    def __init__(self, conductor_config_dir: Path = None):
        self.config_dir = conductor_config_dir or Path.home() / '.conductor' / 'mcp'
        self.config_path = self.config_dir / 'config.json'
        self.bridge_config_path = self.config_dir / 'bridge.json'
        self.mcp_client: Optional[MCPClient] = None

    async def setup_bridge(self) -> bool:
        """Set up bridge between VSCode MCP and Conductor"""
        try:
            # Create config directory
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Extract VSCode MCP configuration
            vscode_config = VSCodeMCPConfig.extract_mcp_config()
            if not vscode_config:
                logger.info("No VSCode MCP configuration found, creating standalone setup")
                await self._create_standalone_config()
                return True

            # Convert VSCode config to Conductor format
            conductor_config = self._convert_vscode_to_conductor(vscode_config)

            # Save conductor MCP config
            with open(self.config_path, 'w') as f:
                json.dump(conductor_config, f, indent=2)

            # Save bridge metadata
            bridge_metadata = {
                'created_at': '2026-03-12T00:00:00Z',
                'source': 'vscode_bridge',
                'vscode_config_path': str(VSCodeMCPConfig.get_vscode_settings_path()),
                'servers_bridged': list(conductor_config.get('mcpServers', {}).keys())
            }

            with open(self.bridge_config_path, 'w') as f:
                json.dump(bridge_metadata, f, indent=2)

            logger.info(f"Created MCP bridge with {len(conductor_config.get('mcpServers', {}))} servers")
            return True

        except Exception as e:
            logger.error(f"Failed to setup MCP bridge: {e}")
            return False

    def _convert_vscode_to_conductor(self, vscode_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert VSCode MCP config to Conductor format"""
        conductor_config = {'mcpServers': {}}

        for config_key, servers in vscode_config.items():
            if not isinstance(servers, dict):
                continue

            for server_name, server_config in servers.items():
                # Convert VSCode format to Conductor format
                if isinstance(server_config, dict):
                    conductor_server = {
                        'command': server_config.get('command', 'npx'),
                        'args': server_config.get('args', []),
                        'env': server_config.get('env', {})
                    }

                    # Handle special cases for common MCP servers
                    if 'jira' in server_name.lower():
                        conductor_server = self._configure_jira_server(server_config)
                    elif 'github' in server_name.lower():
                        conductor_server = self._configure_github_server(server_config)
                    elif 'slack' in server_name.lower():
                        conductor_server = self._configure_slack_server(server_config)

                    conductor_config['mcpServers'][server_name] = conductor_server

        return conductor_config

    def _configure_jira_server(self, vscode_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure JIRA MCP server from VSCode config"""
        return {
            'command': 'npx',
            'args': ['@modelcontextprotocol/server-jira'],
            'env': {
                'JIRA_API_TOKEN': vscode_config.get('env', {}).get('JIRA_API_TOKEN', ''),
                'JIRA_HOST': vscode_config.get('env', {}).get('JIRA_HOST', ''),
                'JIRA_EMAIL': vscode_config.get('env', {}).get('JIRA_EMAIL', ''),
                'JIRA_PROJECT': vscode_config.get('env', {}).get('JIRA_PROJECT', '')
            }
        }

    def _configure_github_server(self, vscode_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure GitHub MCP server from VSCode config"""
        return {
            'command': 'npx',
            'args': ['@modelcontextprotocol/server-github'],
            'env': {
                'GITHUB_TOKEN': vscode_config.get('env', {}).get('GITHUB_TOKEN', ''),
                'GITHUB_OWNER': vscode_config.get('env', {}).get('GITHUB_OWNER', ''),
                'GITHUB_REPO': vscode_config.get('env', {}).get('GITHUB_REPO', '')
            }
        }

    def _configure_slack_server(self, vscode_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure Slack MCP server from VSCode config"""
        return {
            'command': 'npx',
            'args': ['@modelcontextprotocol/server-slack'],
            'env': {
                'SLACK_BOT_TOKEN': vscode_config.get('env', {}).get('SLACK_BOT_TOKEN', ''),
                'SLACK_SIGNING_SECRET': vscode_config.get('env', {}).get('SLACK_SIGNING_SECRET', '')
            }
        }

    async def _create_standalone_config(self) -> None:
        """Create standalone MCP configuration for users without VSCode"""
        standalone_config = {
            'mcpServers': {
                'jira': {
                    'command': 'npx',
                    'args': ['@modelcontextprotocol/server-jira'],
                    'env': {
                        'JIRA_API_TOKEN': 'your_jira_token',
                        'JIRA_HOST': 'your-company.atlassian.net',
                        'JIRA_EMAIL': 'your-email@company.com',
                        'JIRA_PROJECT': 'YOUR_PROJECT_KEY'
                    }
                },
                'github': {
                    'command': 'npx',
                    'args': ['@modelcontextprotocol/server-github'],
                    'env': {
                        'GITHUB_TOKEN': 'your_github_token',
                        'GITHUB_OWNER': 'your_github_username',
                        'GITHUB_REPO': 'your_repository_name'
                    }
                }
            }
        }

        with open(self.config_path, 'w') as f:
            json.dump(standalone_config, f, indent=2)

        logger.info(f"Created standalone MCP config at {self.config_path}")

    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all configured MCP servers"""
        if not self.mcp_client:
            self.mcp_client = MCPClient(self.config_path)

        results = {}
        for server_name in self.mcp_client.get_available_servers():
            try:
                results[server_name] = await self.mcp_client.test_connection(server_name)
            except Exception as e:
                logger.error(f"Connection test failed for {server_name}: {e}")
                results[server_name] = False

        return results

    async def install_mcp_servers(self) -> bool:
        """Install required MCP servers using npm"""
        # Note: These are example package names - actual MCP servers may have different names
        servers_to_install = [
            # '@modelcontextprotocol/server-jira',    # Not yet published
            # '@modelcontextprotocol/server-github',  # Not yet published
            # '@modelcontextprotocol/server-slack'    # Not yet published
        ]

        if not servers_to_install:
            logger.info("No MCP servers to install - using placeholder configuration")
            return True

        try:
            for server in servers_to_install:
                logger.info(f"Installing {server}...")
                result = subprocess.run(  # nosec B603 B607
                    ['npm', 'install', '-g', server],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode != 0:
                    logger.warning(f"Failed to install {server}: {result.stderr}")
                    continue

                logger.info(f"Successfully installed {server}")

            return True

        except Exception as e:
            logger.error(f"Failed to install MCP servers: {e}")
            return False

    def get_config_status(self) -> Dict[str, Any]:
        """Get current MCP configuration status"""
        status = {
            'config_exists': self.config_path.exists(),
            'bridge_exists': self.bridge_config_path.exists(),
            'config_path': str(self.config_path),
            'servers_configured': 0
        }

        if status['config_exists']:
            try:
                with open(self.config_path) as f:
                    config = json.load(f)
                status['servers_configured'] = len(config.get('mcpServers', {}))
            except Exception:
                pass

        return status