# Contributing to Conductor

Thank you for your interest in contributing to Conductor! This document provides guidelines for contributing to this open source workflow orchestrator.

## 📋 Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` (optional for integrations)

## 🧪 Testing

Test your changes by running the basic commands:

```bash
# Test basic functionality
./conductor.py --help
./conductor.py start --dashboard
./conductor.py services
./conductor.py workflows
```

## 🎯 Contributing Areas

### Core Features
- **Workflow Engine**: Markdown-based workflow parsing and execution
- **Document Processing**: Versioning, format conversion, and publishing
- **Scheduler**: Natural language time parsing and reminders
- **MCP Services**: Integration with external services (JIRA, GitHub, etc.)

### Integrations
- New MCP service integrations (follow the pattern in `src/integrations/`)
- Enhanced existing integrations
- Improved error handling and configuration

### Templates
- New workflow templates in `workflows/`
- Documentation templates
- Industry-specific workflows

### CLI and UX
- Enhanced dashboard features
- Better error messages and help text
- Performance improvements

## 🏗️ Project Structure

```
conductor/
├── src/
│   ├── core/           # Core system components
│   ├── integrations/   # MCP service integrations
│   └── utils/          # Utility functions
├── workflows/          # Workflow templates
├── conductor.py        # Main CLI
└── requirements.txt    # Dependencies
```

## 📝 Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Keep functions focused and well-documented
- Use descriptive variable names
- Add docstrings to public methods

## 🔧 Adding New MCP Services

1. Create a new file in `src/integrations/` following the pattern:
   ```
   your_service_integration.py
   ```

2. Implement the `MCPService` base class:
   ```python
   from src.core.mcp_manager import MCPService, ServiceCapability

   class YourServiceIntegration(MCPService):
       @property
       def service_name(self) -> str:
           return "your_service"

       @property
       def capabilities(self) -> List[ServiceCapability]:
           return [
               ServiceCapability(
                   name="your_capability",
                   description="Description of what it does",
                   parameters=["param1", "param2"],
                   required_config=["api_token"]
               )
           ]
   ```

3. The service will be auto-discovered by the MCP manager

## 🎨 Adding Workflow Templates

Create new templates in the `workflows/` directory:

```markdown
---
title: "Your Workflow Title"
description: "What this workflow accomplishes"
priority: 2
status: pending
tags: ["category", "feature"]
---

# Your Workflow

Description of the workflow purpose.

## Actions

- [ ] First action to take
- [ ] Second action with MCP service call
- [ ] Final verification step

## Reminders

- Remind me in 2 days to check progress
- Follow up weekly until completion
```

## 📚 Documentation

- Keep README.md up to date
- Document new features and configuration options
- Include examples for complex features
- Update help text in CLI commands

## 🚀 Submitting Changes

1. Create a descriptive branch name:
   ```bash
   git checkout -b feature/workflow-templates
   git checkout -b fix/scheduler-timezone
   ```

2. Make your changes with clear commit messages:
   ```bash
   git commit -m "Add Slack integration with message sending capability"
   ```

3. Test thoroughly before submitting
4. Create a pull request with:
   - Clear description of changes
   - Why the change is needed
   - Any breaking changes
   - Testing instructions

## 🎯 Design Principles

- **Offline First**: Core functionality should work without internet/API keys
- **Plugin Architecture**: Easy to add new services and integrations
- **User-Friendly**: Simple CLI with helpful error messages
- **Markdown-Centric**: Use markdown for configuration and workflows
- **Minimal Dependencies**: Keep the dependency list lean

## 🆘 Getting Help

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Be specific about your environment and steps to reproduce
- Include error messages and logs when relevant

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for helping make Conductor better! 🎉
