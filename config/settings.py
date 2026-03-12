import os
from pathlib import Path
from typing import Any, Dict

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Keys
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    jira_api_token: str = Field(default="", env="JIRA_API_TOKEN")
    jira_server_url: str = Field(default="", env="JIRA_SERVER_URL")
    jira_username: str = Field(default="", env="JIRA_USERNAME")
    confluence_api_token: str = Field(default="", env="CONFLUENCE_API_TOKEN")
    confluence_server_url: str = Field(default="", env="CONFLUENCE_SERVER_URL")
    github_token: str = Field(default="", env="GITHUB_TOKEN")

    # Project Configuration
    project_root: Path = Path(__file__).parent.parent
    templates_dir: Path = project_root / "src" / "templates"
    output_dir: Path = project_root / "output"

    # Documentation Settings
    default_output_format: str = "docx"
    supported_formats: list = ["docx", "pdf", "markdown", "html"]

    # Splunk Configuration
    splunk_server_url: str = Field(default="", env="SPLUNK_SERVER_URL")
    splunk_username: str = Field(default="", env="SPLUNK_USERNAME")
    splunk_password: str = Field(default="", env="SPLUNK_PASSWORD")

    # Agent Configuration
    max_retries: int = 3
    agent_timeout: int = 300
    verbose_logging: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
