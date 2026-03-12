import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from config.settings import get_settings


class MCPIntegration(ABC):
    """Base class for MCP (Model Context Protocol) integrations."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.settings = get_settings()
        self.client = None
        self._setup_client()

    @abstractmethod
    def _setup_client(self):
        """Setup the client for the specific service."""
        pass

    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search for content in the service."""
        pass

    @abstractmethod
    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get a specific item by ID."""
        pass

    @abstractmethod
    async def create_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item in the service."""
        pass

    @abstractmethod
    async def update_item(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item."""
        pass

    def _format_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Format error responses consistently."""
        return {
            "success": False,
            "error": str(error),
            "operation": operation,
            "service": self.service_name,
        }

    def _format_success(self, data: Any, operation: str) -> Dict[str, Any]:
        """Format success responses consistently."""
        return {
            "success": True,
            "data": data,
            "operation": operation,
            "service": self.service_name,
        }
