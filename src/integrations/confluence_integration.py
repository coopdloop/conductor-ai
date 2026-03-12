from typing import Any, Dict, List, Optional

from atlassian import Confluence

from .mcp_base import MCPIntegration


class ConfluenceIntegration(MCPIntegration):
    """Confluence MCP integration for documentation publishing and research."""

    def __init__(self):
        super().__init__("confluence")

    def _setup_client(self):
        """Setup Confluence client with authentication."""
        if not all(
            [
                self.settings.confluence_server_url,
                self.settings.jira_username,
                self.settings.confluence_api_token,
            ]
        ):
            self.client = None
            return

        try:
            self.client = Confluence(
                url=self.settings.confluence_server_url,
                username=self.settings.jira_username,
                password=self.settings.confluence_api_token,
            )
        except Exception as e:
            print(f"Failed to setup Confluence client: {e}")
            self.client = None

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search Confluence pages."""
        if not self.client:
            return [
                self._format_error(
                    Exception("Confluence client not configured"), "search"
                )
            ]

        try:
            space_keys = kwargs.get("space_keys", [])
            limit = kwargs.get("limit", 25)

            # Build CQL query
            cql_parts = [f'text ~ "{query}"']
            if space_keys:
                space_filter = " OR ".join([f'space = "{key}"' for key in space_keys])
                cql_parts.append(f"({space_filter})")

            cql = " AND ".join(cql_parts)

            results = self.client.cql(cql, limit=limit)

            pages = []
            for result in results["results"]:
                pages.append(
                    {
                        "id": result["content"]["id"],
                        "title": result["content"]["title"],
                        "type": result["content"]["type"],
                        "space_key": result["content"]["space"]["key"],
                        "space_name": result["content"]["space"]["name"],
                        "url": f"{self.settings.confluence_server_url}{result['content']['_links']['webui']}",
                        "excerpt": result.get("excerpt", ""),
                        "lastModified": result["content"]["version"]["when"],
                    }
                )

            return [self._format_success(pages, "search")]

        except Exception as e:
            return [self._format_error(e, "search")]

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get a specific Confluence page by ID."""
        if not self.client:
            return self._format_error(
                Exception("Confluence client not configured"), "get_item"
            )

        try:
            page = self.client.get_page_by_id(
                item_id, expand="body.storage,space,version,metadata.labels"
            )

            # Get page content
            content = page["body"]["storage"]["value"] if "body" in page else ""

            # Get labels
            labels = []
            if "metadata" in page and "labels" in page["metadata"]:
                labels = [
                    label["name"] for label in page["metadata"]["labels"]["results"]
                ]

            result = {
                "id": page["id"],
                "title": page["title"],
                "type": page["type"],
                "space_key": page["space"]["key"],
                "space_name": page["space"]["name"],
                "content": content,
                "labels": labels,
                "version": page["version"]["number"],
                "created": page["version"]["when"],
                "url": f"{self.settings.confluence_server_url}{page['_links']['webui']}",
            }

            return self._format_success(result, "get_item")

        except Exception as e:
            return self._format_error(e, "get_item")

    async def create_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Confluence page."""
        if not self.client:
            return self._format_error(
                Exception("Confluence client not configured"), "create_item"
            )

        try:
            page_data = {
                "type": "page",
                "title": data["title"],
                "space": {"key": data["space_key"]},
                "body": {
                    "storage": {"value": data["content"], "representation": "storage"}
                },
            }

            # Add parent page if specified
            if "parent_id" in data:
                parent_page = self.client.get_page_by_id(data["parent_id"])
                page_data["ancestors"] = [{"id": parent_page["id"]}]

            new_page = self.client.create_page(**page_data)

            # Add labels if provided
            if "labels" in data and data["labels"]:
                for label in data["labels"]:
                    self.client.add_page_label(new_page["id"], label)

            result = {
                "id": new_page["id"],
                "title": new_page["title"],
                "url": f"{self.settings.confluence_server_url}{new_page['_links']['webui']}",
            }

            return self._format_success(result, "create_item")

        except Exception as e:
            return self._format_error(e, "create_item")

    async def update_item(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Confluence page."""
        if not self.client:
            return self._format_error(
                Exception("Confluence client not configured"), "update_item"
            )

        try:
            # Get current page to get version number
            current_page = self.client.get_page_by_id(item_id)

            update_data = {
                "type": "page",
                "title": data.get("title", current_page["title"]),
                "version": {"number": current_page["version"]["number"] + 1},
            }

            if "content" in data:
                update_data["body"] = {
                    "storage": {"value": data["content"], "representation": "storage"}
                }

            updated_page = self.client.update_page(item_id, **update_data)

            # Update labels if provided
            if "labels" in data:
                # Remove existing labels and add new ones
                current_labels = self.client.get_page_labels(item_id)
                for label in current_labels["results"]:
                    self.client.remove_page_label(item_id, label["name"])

                for label in data["labels"]:
                    self.client.add_page_label(item_id, label)

            result = {
                "id": updated_page["id"],
                "title": updated_page["title"],
                "version": updated_page["version"]["number"],
                "url": f"{self.settings.confluence_server_url}{updated_page['_links']['webui']}",
            }

            return self._format_success(result, "update_item")

        except Exception as e:
            return self._format_error(e, "update_item")

    def convert_to_confluence_markup(self, content: str) -> str:
        """Convert content to Confluence markup format."""
        # Basic conversion from Markdown to Confluence markup
        # This is a simplified implementation - you might want to use a proper converter

        # Headers
        content = content.replace("# ", "h1. ")
        content = content.replace("## ", "h2. ")
        content = content.replace("### ", "h3. ")
        content = content.replace("#### ", "h4. ")

        # Bold and italic
        content = content.replace("**", "*")
        content = content.replace("__", "_")

        # Code blocks
        content = content.replace("```", "{code}")

        # Lists (basic conversion)
        lines = content.split("\n")
        converted_lines = []
        for line in lines:
            if line.strip().startswith("- "):
                converted_lines.append(line.replace("- ", "* "))
            elif line.strip().startswith("1. "):
                converted_lines.append(line.replace("1. ", "# "))
            else:
                converted_lines.append(line)

        return "\n".join(converted_lines)

    def publish_documentation(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """High-level method to publish documentation to Confluence."""

        # Convert content to Confluence markup
        confluence_content = self.convert_to_confluence_markup(content)

        # Check if page already exists
        try:
            if self.client:
                existing_page = self.client.get_page_by_title(space_key, title)
                if existing_page:
                    # Update existing page
                    return self.update_item(
                        existing_page["id"],
                        {"content": confluence_content, "labels": labels or []},
                    )
        except:
            # Page doesn't exist, create new one
            pass

        # Create new page
        return self.create_item(
            {
                "space_key": space_key,
                "title": title,
                "content": confluence_content,
                "parent_id": parent_id,
                "labels": labels or [],
            }
        )
