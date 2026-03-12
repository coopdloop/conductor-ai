import importlib
import importlib.util
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type


class ServiceStatus(Enum):
    AVAILABLE = "available"
    CONFIGURED = "configured"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ServiceCapability:
    """Represents a capability that an MCP service provides."""

    name: str
    description: str
    parameters: List[str]
    required_config: List[str]


@dataclass
class ServiceInfo:
    """Information about an MCP service."""

    name: str
    description: str
    status: ServiceStatus
    capabilities: List[ServiceCapability]
    config_keys: List[str]
    version: str = "1.0.0"


class MCPService(ABC):
    """Base class for all MCP services."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._status = ServiceStatus.AVAILABLE

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return the service name."""
        pass

    @property
    @abstractmethod
    def service_description(self) -> str:
        """Return the service description."""
        pass

    @property
    @abstractmethod
    def required_config(self) -> List[str]:
        """Return list of required configuration keys."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[ServiceCapability]:
        """Return list of service capabilities."""
        pass

    @property
    def status(self) -> ServiceStatus:
        """Get current service status."""
        return self._status

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the service with provided config."""
        self.config.update(config)

        # Check if all required config is present
        missing_keys = [
            key
            for key in self.required_config
            if key not in self.config or not self.config[key]
        ]
        if missing_keys:
            self._status = ServiceStatus.ERROR
            return False

        self._status = ServiceStatus.CONFIGURED
        return True

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the service."""
        pass

    @abstractmethod
    def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a service action."""
        pass

    def get_info(self) -> ServiceInfo:
        """Get service information."""
        return ServiceInfo(
            name=self.service_name,
            description=self.service_description,
            status=self.status,
            capabilities=self.capabilities,
            config_keys=self.required_config,
        )


class MCPManager:
    """Manages all MCP services and their capabilities."""

    def __init__(self, services_dir: Path = None):
        self.services_dir = (
            services_dir or Path(__file__).parent.parent / "integrations"
        )
        self.services: Dict[str, MCPService] = {}
        self.service_classes: Dict[str, Type[MCPService]] = {}

        self.discover_services()

    def discover_services(self):
        """Discover and load available MCP services."""
        if not self.services_dir.exists():
            return

        # Look for service files
        for service_file in self.services_dir.glob("*_integration.py"):
            if service_file.name == "mcp_base.py":
                continue

            try:
                # Import the module
                module_name = service_file.stem
                spec = importlib.util.spec_from_file_location(module_name, service_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for MCP service classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, MCPService)
                        and attr != MCPService
                    ):

                        service_name = (
                            attr_name.lower()
                            .replace("integration", "")
                            .replace("service", "")
                        )
                        self.service_classes[service_name] = attr

            except Exception as e:
                # Silently skip services that can't be loaded (usually due to relative imports)
                # This is expected for integration files that aren't proper MCP services yet
                pass

    def get_available_services(self) -> List[ServiceInfo]:
        """Get list of all available services."""
        services_info = []

        for service_name, service_class in self.service_classes.items():
            try:
                # Create temporary instance to get info
                temp_service = service_class()
                services_info.append(temp_service.get_info())
            except Exception as e:
                services_info.append(
                    ServiceInfo(
                        name=service_name,
                        description=f"Error loading service: {e}",
                        status=ServiceStatus.ERROR,
                        capabilities=[],
                        config_keys=[],
                    )
                )

        return services_info

    def configure_service(
        self, service_name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure a specific service."""
        if service_name not in self.service_classes:
            return {"success": False, "error": f"Service {service_name} not found"}

        try:
            # Create or update service instance
            if service_name in self.services:
                service = self.services[service_name]
                success = service.configure(config)
            else:
                service_class = self.service_classes[service_name]
                service = service_class(config)
                success = service.configure(config)
                if success:
                    self.services[service_name] = service

            if success:
                return {"success": True, "status": service.status.value}
            else:
                return {
                    "success": False,
                    "error": "Configuration failed",
                    "status": service.status.value,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_service(self, service_name: str) -> Dict[str, Any]:
        """Test connection to a service."""
        if service_name not in self.services:
            return {"success": False, "error": f"Service {service_name} not configured"}

        try:
            service = self.services[service_name]
            result = service.test_connection()

            if result.get("success"):
                service._status = ServiceStatus.CONNECTED
            else:
                service._status = ServiceStatus.ERROR

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_service_action(
        self, service_name: str, action: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action on a specific service."""
        if service_name not in self.services:
            return {"success": False, "error": f"Service {service_name} not configured"}

        try:
            service = self.services[service_name]
            if service.status not in [
                ServiceStatus.CONFIGURED,
                ServiceStatus.CONNECTED,
            ]:
                return {
                    "success": False,
                    "error": f"Service {service_name} not ready (status: {service.status.value})",
                }

            result = service.execute_action(action, parameters)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_service_capabilities(self, service_name: str) -> List[ServiceCapability]:
        """Get capabilities for a specific service."""
        if service_name in self.services:
            return self.services[service_name].capabilities
        elif service_name in self.service_classes:
            # Create temporary instance to get capabilities
            temp_service = self.service_classes[service_name]()
            return temp_service.capabilities
        else:
            return []

    def auto_configure_from_env(self) -> Dict[str, Dict[str, Any]]:
        """Auto-configure services from environment variables."""
        results = {}

        import os

        # Common environment variable patterns
        env_mappings = {
            "jira": {
                "server_url": "JIRA_SERVER_URL",
                "username": "JIRA_USERNAME",
                "api_token": "JIRA_API_TOKEN",
            },
            "confluence": {
                "server_url": "CONFLUENCE_SERVER_URL",
                "api_token": "CONFLUENCE_API_TOKEN",
            },
            "github": {"token": "GITHUB_TOKEN"},
            "slack": {"token": "SLACK_BOT_TOKEN", "webhook_url": "SLACK_WEBHOOK_URL"},
            "webex": {"token": "WEBEX_BOT_TOKEN"},
        }

        for service_name, env_keys in env_mappings.items():
            if service_name in self.service_classes:
                config = {}
                for config_key, env_key in env_keys.items():
                    if env_key in os.environ:
                        config[config_key] = os.environ[env_key]

                if config:
                    result = self.configure_service(service_name, config)
                    results[service_name] = result

        return results

    def get_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services."""
        status = {}

        for service_name, service in self.services.items():
            status[service_name] = {
                "name": service.service_name,
                "status": service.status.value,
                "configured": service.status != ServiceStatus.AVAILABLE,
                "connected": service.status == ServiceStatus.CONNECTED,
                "capabilities_count": len(service.capabilities),
            }

        # Include available but not configured services
        for service_name in self.service_classes:
            if service_name not in status:
                status[service_name] = {
                    "name": service_name,
                    "status": ServiceStatus.AVAILABLE.value,
                    "configured": False,
                    "connected": False,
                    "capabilities_count": 0,
                }

        return status

    def get_service_by_capability(self, capability_name: str) -> List[str]:
        """Get services that provide a specific capability."""
        matching_services = []

        for service_name, service in self.services.items():
            for capability in service.capabilities:
                if capability.name.lower() == capability_name.lower():
                    matching_services.append(service_name)
                    break

        return matching_services

    def execute_workflow_action(
        self, action_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow action using appropriate MCP service."""

        # Map action types to service capabilities
        action_mappings = {
            "jira_update": ("jira", "update_issue"),
            "jira_comment": ("jira", "add_comment"),
            "confluence_publish": ("confluence", "publish_page"),
            "github_commit": ("github", "create_commit"),
            "slack_message": ("slack", "send_message"),
            "webex_message": ("webex", "send_message"),
        }

        if action_type not in action_mappings:
            return {"success": False, "error": f"Unknown action type: {action_type}"}

        service_name, action = action_mappings[action_type]

        if service_name not in self.services:
            return {"success": False, "error": f"Service {service_name} not configured"}

        return self.execute_service_action(service_name, action, parameters)

    def bulk_configure_services(
        self, configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Configure multiple services at once."""
        results = {}

        for service_name, config in configs.items():
            results[service_name] = self.configure_service(service_name, config)

        return results

    def export_configuration(self) -> Dict[str, Any]:
        """Export current service configurations (excluding sensitive data)."""
        export_data = {
            "configured_services": [],
            "export_timestamp": datetime.now().isoformat(),
        }

        for service_name, service in self.services.items():
            service_data = {
                "name": service_name,
                "status": service.status.value,
                "config_keys": list(service.config.keys()),
                "capabilities": [cap.name for cap in service.capabilities],
            }
            export_data["configured_services"].append(service_data)

        return export_data


# Enhanced service base classes for specific types


class ChatService(MCPService):
    """Base class for chat/messaging services."""

    @abstractmethod
    def send_message(self, channel: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send a message to a channel/user."""
        pass


class IssueTrackingService(MCPService):
    """Base class for issue tracking services."""

    @abstractmethod
    def get_assigned_issues(self, user: str = None) -> Dict[str, Any]:
        """Get assigned issues for a user."""
        pass

    @abstractmethod
    def update_issue(self, issue_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update an issue."""
        pass

    @abstractmethod
    def add_comment(self, issue_id: str, comment: str) -> Dict[str, Any]:
        """Add a comment to an issue."""
        pass


class DocumentationService(MCPService):
    """Base class for documentation services."""

    @abstractmethod
    def publish_page(
        self, title: str, content: str, space: str = None
    ) -> Dict[str, Any]:
        """Publish a documentation page."""
        pass

    @abstractmethod
    def search_pages(self, query: str, space: str = None) -> Dict[str, Any]:
        """Search for documentation pages."""
        pass


class RepositoryService(MCPService):
    """Base class for code repository services."""

    @abstractmethod
    def create_commit(
        self, repo: str, file_path: str, content: str, message: str
    ) -> Dict[str, Any]:
        """Create a commit in a repository."""
        pass

    @abstractmethod
    def create_pull_request(
        self,
        repo: str,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str,
    ) -> Dict[str, Any]:
        """Create a pull request."""
        pass
