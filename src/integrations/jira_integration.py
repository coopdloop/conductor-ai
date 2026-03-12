from typing import Any, Dict, List, Optional

from atlassian import Jira

from .mcp_base import MCPIntegration


class JiraIntegration(MCPIntegration):
    """JIRA MCP integration for ticket management and research."""

    def __init__(self):
        super().__init__("jira")

    def _setup_client(self):
        """Setup JIRA client with authentication."""
        if not all(
            [
                self.settings.jira_server_url,
                self.settings.jira_username,
                self.settings.jira_api_token,
            ]
        ):
            self.client = None
            return

        try:
            self.client = Jira(
                url=self.settings.jira_server_url,
                username=self.settings.jira_username,
                password=self.settings.jira_api_token,
            )
        except Exception as e:
            print(f"Failed to setup JIRA client: {e}")
            self.client = None

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search JIRA tickets using JQL or text search."""
        if not self.client:
            return [
                self._format_error(Exception("JIRA client not configured"), "search")
            ]

        try:
            # Build JQL query
            project = kwargs.get("project")
            issue_type = kwargs.get("issue_type")
            status = kwargs.get("status")
            max_results = kwargs.get("max_results", 50)

            jql_parts = []
            if project:
                jql_parts.append(f'project = "{project}"')
            if issue_type:
                jql_parts.append(f'issueType = "{issue_type}"')
            if status:
                jql_parts.append(f'status = "{status}"')

            # Add text search
            if query:
                jql_parts.append(f'text ~ "{query}"')

            jql = " AND ".join(jql_parts) if jql_parts else f'text ~ "{query}"'

            issues = self.client.jql(jql, limit=max_results)

            results = []
            for issue in issues["issues"]:
                results.append(
                    {
                        "id": issue["key"],
                        "summary": issue["fields"]["summary"],
                        "description": issue["fields"].get("description", ""),
                        "status": issue["fields"]["status"]["name"],
                        "issue_type": issue["fields"]["issuetype"]["name"],
                        "created": issue["fields"]["created"],
                        "updated": issue["fields"]["updated"],
                        "url": f"{self.settings.jira_server_url}/browse/{issue['key']}",
                    }
                )

            return [self._format_success(results, "search")]

        except Exception as e:
            return [self._format_error(e, "search")]

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get a specific JIRA ticket by ID."""
        if not self.client:
            return self._format_error(
                Exception("JIRA client not configured"), "get_item"
            )

        try:
            issue = self.client.issue(item_id)

            # Get comments
            comments = []
            for comment in issue["fields"].get("comment", {}).get("comments", []):
                comments.append(
                    {
                        "author": comment["author"]["displayName"],
                        "body": comment["body"],
                        "created": comment["created"],
                    }
                )

            result = {
                "id": issue["key"],
                "summary": issue["fields"]["summary"],
                "description": issue["fields"].get("description", ""),
                "status": issue["fields"]["status"]["name"],
                "issue_type": issue["fields"]["issuetype"]["name"],
                "priority": (
                    issue["fields"]["priority"]["name"]
                    if issue["fields"]["priority"]
                    else None
                ),
                "assignee": (
                    issue["fields"]["assignee"]["displayName"]
                    if issue["fields"]["assignee"]
                    else None
                ),
                "reporter": issue["fields"]["reporter"]["displayName"],
                "created": issue["fields"]["created"],
                "updated": issue["fields"]["updated"],
                "comments": comments,
                "url": f"{self.settings.jira_server_url}/browse/{issue['key']}",
            }

            return self._format_success(result, "get_item")

        except Exception as e:
            return self._format_error(e, "get_item")

    async def create_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new JIRA ticket."""
        if not self.client:
            return self._format_error(
                Exception("JIRA client not configured"), "create_item"
            )

        try:
            issue_dict = {
                "project": {"key": data["project"]},
                "summary": data["summary"],
                "description": data.get("description", ""),
                "issuetype": {"name": data.get("issue_type", "Task")},
            }

            if "priority" in data:
                issue_dict["priority"] = {"name": data["priority"]}

            new_issue = self.client.create_issue(fields=issue_dict)

            result = {
                "id": new_issue["key"],
                "url": f"{self.settings.jira_server_url}/browse/{new_issue['key']}",
            }

            return self._format_success(result, "create_item")

        except Exception as e:
            return self._format_error(e, "create_item")

    async def update_item(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing JIRA ticket."""
        if not self.client:
            return self._format_error(
                Exception("JIRA client not configured"), "update_item"
            )

        try:
            # Add comment if provided
            if "comment" in data:
                self.client.add_comment(item_id, data["comment"])

            # Update fields if provided
            update_dict = {}
            if "summary" in data:
                update_dict["summary"] = data["summary"]
            if "description" in data:
                update_dict["description"] = data["description"]

            if update_dict:
                self.client.update_issue_field(item_id, update_dict)

            # Transition status if provided
            if "status" in data:
                transitions = self.client.get_issue_transitions(item_id)
                for transition in transitions["transitions"]:
                    if transition["name"].lower() == data["status"].lower():
                        self.client.transition_issue(item_id, transition["id"])
                        break

            result = {
                "id": item_id,
                "updated": True,
                "url": f"{self.settings.jira_server_url}/browse/{item_id}",
            }

            return self._format_success(result, "update_item")

        except Exception as e:
            return self._format_error(e, "update_item")

    def add_documentation_link(
        self, ticket_id: str, doc_title: str, doc_url: str
    ) -> Dict[str, Any]:
        """Add a documentation link to a JIRA ticket."""
        comment = f"""
Documentation Created: {doc_title}

Link: {doc_url}

This documentation was automatically generated and linked to address the technical requirements in this ticket.
        """.strip()

        return self.update_item(ticket_id, {"comment": comment})
