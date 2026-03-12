import base64
from typing import Any, Dict, List, Optional

from github import Github

from .mcp_base import MCPIntegration


class GitHubIntegration(MCPIntegration):
    """GitHub MCP integration for repository management and documentation publishing."""

    def __init__(self):
        super().__init__("github")

    def _setup_client(self):
        """Setup GitHub client with authentication."""
        if not self.settings.github_token:
            self.client = None
            return

        try:
            self.client = Github(self.settings.github_token)
        except Exception as e:
            print(f"Failed to setup GitHub client: {e}")
            self.client = None

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search GitHub repositories, issues, or code."""
        if not self.client:
            return [
                self._format_error(Exception("GitHub client not configured"), "search")
            ]

        try:
            search_type = kwargs.get(
                "type", "repositories"
            )  # repositories, issues, code
            repo_name = kwargs.get("repository")
            limit = kwargs.get("limit", 30)

            results = []

            if search_type == "repositories":
                repos = self.client.search_repositories(query)
                for repo in repos[:limit]:
                    results.append(
                        {
                            "id": repo.id,
                            "name": repo.full_name,
                            "description": repo.description,
                            "url": repo.html_url,
                            "language": repo.language,
                            "stars": repo.stargazers_count,
                            "updated": repo.updated_at.isoformat(),
                        }
                    )

            elif search_type == "issues" and repo_name:
                repo = self.client.get_repo(repo_name)
                issues = repo.get_issues(state="all")
                for issue in issues[:limit]:
                    if (
                        query.lower() in issue.title.lower()
                        or query.lower() in (issue.body or "").lower()
                    ):
                        results.append(
                            {
                                "id": issue.number,
                                "title": issue.title,
                                "body": issue.body,
                                "state": issue.state,
                                "url": issue.html_url,
                                "created": issue.created_at.isoformat(),
                                "updated": issue.updated_at.isoformat(),
                            }
                        )

            elif search_type == "code" and repo_name:
                repo = self.client.get_repo(repo_name)
                contents = self.client.search_code(f"{query} repo:{repo_name}")
                for content in contents[:limit]:
                    results.append(
                        {
                            "path": content.path,
                            "name": content.name,
                            "url": content.html_url,
                            "repository": content.repository.full_name,
                        }
                    )

            return [self._format_success(results, "search")]

        except Exception as e:
            return [self._format_error(e, "search")]

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get a specific item (repository, file, or issue)."""
        if not self.client:
            return self._format_error(
                Exception("GitHub client not configured"), "get_item"
            )

        try:
            # Parse item_id which should be in format: repo_name/type/identifier
            # e.g., "owner/repo/file/path/to/file.md" or "owner/repo/issue/123"
            parts = item_id.split("/")
            if len(parts) < 3:
                raise ValueError("Invalid item ID format")

            repo_name = "/".join(parts[:2])
            item_type = parts[2]
            identifier = "/".join(parts[3:]) if len(parts) > 3 else None

            repo = self.client.get_repo(repo_name)

            if item_type == "file" and identifier:
                file_content = repo.get_contents(identifier)
                content = base64.b64decode(file_content.content).decode("utf-8")

                result = {
                    "type": "file",
                    "path": file_content.path,
                    "name": file_content.name,
                    "content": content,
                    "size": file_content.size,
                    "url": file_content.html_url,
                    "download_url": file_content.download_url,
                }

            elif item_type == "issue" and identifier:
                issue = repo.get_issue(int(identifier))

                # Get comments
                comments = []
                for comment in issue.get_comments():
                    comments.append(
                        {
                            "author": comment.user.login,
                            "body": comment.body,
                            "created": comment.created_at.isoformat(),
                        }
                    )

                result = {
                    "type": "issue",
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "author": issue.user.login,
                    "comments": comments,
                    "url": issue.html_url,
                    "created": issue.created_at.isoformat(),
                    "updated": issue.updated_at.isoformat(),
                }

            elif item_type == "repo":
                result = {
                    "type": "repository",
                    "name": repo.full_name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "created": repo.created_at.isoformat(),
                    "updated": repo.updated_at.isoformat(),
                }

            else:
                raise ValueError(f"Unsupported item type: {item_type}")

            return self._format_success(result, "get_item")

        except Exception as e:
            return self._format_error(e, "get_item")

    async def create_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item (file, issue, or repository)."""
        if not self.client:
            return self._format_error(
                Exception("GitHub client not configured"), "create_item"
            )

        try:
            item_type = data["type"]

            if item_type == "file":
                repo = self.client.get_repo(data["repository"])
                file = repo.create_file(
                    path=data["path"],
                    message=data.get("commit_message", "Add new file"),
                    content=data["content"],
                    branch=data.get("branch", "main"),
                )

                result = {
                    "type": "file",
                    "path": file["content"].path,
                    "url": file["content"].html_url,
                    "commit_sha": file["commit"].sha,
                }

            elif item_type == "issue":
                repo = self.client.get_repo(data["repository"])
                issue = repo.create_issue(
                    title=data["title"],
                    body=data.get("body", ""),
                    labels=data.get("labels", []),
                )

                result = {
                    "type": "issue",
                    "number": issue.number,
                    "url": issue.html_url,
                }

            else:
                raise ValueError(f"Creating {item_type} not supported")

            return self._format_success(result, "create_item")

        except Exception as e:
            return self._format_error(e, "create_item")

    async def update_item(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item."""
        if not self.client:
            return self._format_error(
                Exception("GitHub client not configured"), "update_item"
            )

        try:
            parts = item_id.split("/")
            repo_name = "/".join(parts[:2])
            item_type = parts[2]
            identifier = "/".join(parts[3:]) if len(parts) > 3 else None

            repo = self.client.get_repo(repo_name)

            if item_type == "file" and identifier:
                file = repo.get_contents(identifier)
                updated_file = repo.update_file(
                    path=file.path,
                    message=data.get("commit_message", "Update file"),
                    content=data["content"],
                    sha=file.sha,
                    branch=data.get("branch", "main"),
                )

                result = {
                    "type": "file",
                    "path": updated_file["content"].path,
                    "url": updated_file["content"].html_url,
                    "commit_sha": updated_file["commit"].sha,
                }

            elif item_type == "issue" and identifier:
                issue = repo.get_issue(int(identifier))

                if "title" in data:
                    issue.edit(title=data["title"])
                if "body" in data:
                    issue.edit(body=data["body"])
                if "state" in data:
                    issue.edit(state=data["state"])
                if "labels" in data:
                    issue.edit(labels=data["labels"])

                # Add comment if provided
                if "comment" in data:
                    issue.create_comment(data["comment"])

                result = {
                    "type": "issue",
                    "number": issue.number,
                    "url": issue.html_url,
                    "updated": True,
                }

            else:
                raise ValueError(f"Updating {item_type} not supported")

            return self._format_success(result, "update_item")

        except Exception as e:
            return self._format_error(e, "update_item")

    def publish_documentation(
        self,
        repository: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """High-level method to publish documentation to GitHub."""

        try:
            repo = self.client.get_repo(repository)

            # Check if file exists
            try:
                existing_file = repo.get_contents(file_path)
                # Update existing file
                return self.update_item(
                    f"{repository}/file/{file_path}",
                    {
                        "content": content,
                        "commit_message": commit_message,
                        "branch": branch,
                    },
                )
            except:
                # File doesn't exist, create new one
                return self.create_item(
                    {
                        "type": "file",
                        "repository": repository,
                        "path": file_path,
                        "content": content,
                        "commit_message": commit_message,
                        "branch": branch,
                    }
                )

        except Exception as e:
            return self._format_error(e, "publish_documentation")

    def search_repository_content(
        self, repository: str, topic: str
    ) -> List[Dict[str, Any]]:
        """Search for content within a specific repository."""
        try:
            results = []
            repo = self.client.get_repo(repository)

            # Search in README files
            try:
                readme = repo.get_readme()
                readme_content = base64.b64decode(readme.content).decode("utf-8")
                if topic.lower() in readme_content.lower():
                    results.append(
                        {
                            "type": "readme",
                            "path": readme.path,
                            "content_preview": readme_content[:500],
                            "url": readme.html_url,
                        }
                    )
            except:
                pass

            # Search in documentation directories
            doc_paths = ["docs/", "documentation/", "doc/"]
            for doc_path in doc_paths:
                try:
                    contents = repo.get_contents(doc_path)
                    if isinstance(contents, list):
                        for content in contents:
                            if content.type == "file" and content.name.endswith(
                                (".md", ".txt", ".rst")
                            ):
                                file_content = base64.b64decode(content.content).decode(
                                    "utf-8"
                                )
                                if topic.lower() in file_content.lower():
                                    results.append(
                                        {
                                            "type": "documentation",
                                            "path": content.path,
                                            "content_preview": file_content[:500],
                                            "url": content.html_url,
                                        }
                                    )
                except:
                    continue

            return results

        except Exception as e:
            return [{"error": str(e)}]
