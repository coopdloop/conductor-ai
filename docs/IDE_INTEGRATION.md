# IDE Integration Guide

This guide explains how to integrate Conductor with popular IDEs and AI assistants for enhanced development experience.

## 🤖 GitHub Copilot Integration

### Setup

1. **Install GitHub Copilot Extension**
   - VS Code: Install "GitHub Copilot" extension
   - JetBrains IDEs: Install "GitHub Copilot" plugin
   - Neovim: Install copilot.vim plugin

2. **Configure Copilot for Conductor**

   Create `.copilot/copilot-settings.json`:
   ```json
   {
     "python": {
       "enableAutoImports": true,
       "analysis": {
         "autoSearchPaths": ["src"],
         "extraPaths": ["src"]
       }
     },
     "conductor": {
       "templatePatterns": ["src/templates/**/*.py"],
       "agentPatterns": ["src/agents/**/*.py"],
       "integrationPatterns": ["src/integrations/**/*.py"]
     }
   }
   ```

### Copilot Prompts for Conductor

Use these prompt patterns when working with Conductor:

#### Creating New Agents
```python
# Create a new agent for [specific purpose] that inherits from BaseAgent
# The agent should handle [specific functionality]
# Include proper error handling and async methods
```

#### Creating Templates
```python
# Create a Jinja2 template for [document type]
# Include sections for: [list requirements]
# Use proper Splunk/technical documentation structure
```

#### Integration Development
```python
# Create MCP integration for [service name]
# Implement search, get_item, create_item, update_item methods
# Include proper authentication and error handling
```

## 🔧 VS Code Configuration

### Settings

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.associations": {
    "*.jinja2": "jinja",
    "*.j2": "jinja"
  },
  "conductor.templateDirectory": "src/templates",
  "conductor.outputDirectory": "output"
}
```

### Extensions

Install these VS Code extensions:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "ms-python.black-formatter",
    "ms-python.isort",
    "github.copilot",
    "github.copilot-chat",
    "samuelcolvin.jinjahtml",
    "wholroyd.jinja",
    "redhat.vscode-yaml",
    "ms-vscode.test-adapter-converter",
    "littlefoxteam.vscode-python-test-adapter"
  ]
}
```

### Tasks

Create `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest",
      "args": ["tests/", "-v"],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Format Code",
      "type": "shell",
      "command": "black",
      "args": ["src/", "tests/"],
      "group": "build"
    },
    {
      "label": "Type Check",
      "type": "shell",
      "command": "mypy",
      "args": ["src/"],
      "group": "build"
    },
    {
      "label": "Generate Documentation",
      "type": "shell",
      "command": "./conductor.py",
      "args": ["generate", "--interactive"],
      "group": "build"
    }
  ]
}
```

### Launch Configuration

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Conductor CLI",
      "type": "python",
      "request": "launch",
      "program": "conductor.py",
      "args": ["generate", "--interactive"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v", "--tb=short"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    },
    {
      "name": "Debug Specific Agent",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/examples/debug_agent.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

## 🧠 IntelliJ/PyCharm Configuration

### Project Structure
1. Mark `src` as Sources Root
2. Mark `tests` as Test Sources Root
3. Set Python interpreter to `./venv/bin/python`

### Code Style Settings
1. Go to Settings → Editor → Code Style → Python
2. Import settings from `.editorconfig`
3. Configure imports: Settings → Editor → Code Style → Python → Imports
   - Use `from __future__ import annotations`
   - Sort imports alphabetically
   - Separate groups with blank line

### Run Configurations

Create run configurations for:
- **Conductor CLI**: `conductor.py generate --interactive`
- **Tests**: `pytest tests/ -v`
- **Type Check**: `mypy src/`
- **Format**: `black src/ tests/`

### Plugins
- GitHub Copilot
- Python
- YAML/Ansible Support
- Jinja2

## 🚀 AI Assistant Integration

### GitHub Copilot Chat

Use these chat prompts for Conductor development:

#### Code Generation
```
Generate a Conductor agent for [purpose] with the following requirements:
- Inherits from BaseAgent
- Implements [specific methods]
- Handles [specific functionality]
- Includes proper error handling
- Follows Conductor patterns
```

#### Template Creation
```
Create a Conductor template for [document type] that includes:
- [Section 1]
- [Section 2]
- Proper Jinja2 syntax
- Splunk best practices
- Professional formatting
```

#### Debugging
```
Help me debug this Conductor agent that's failing with:
[Error message]
[Code snippet]
Expected behavior: [description]
```

### Cursor AI Integration

Configure Cursor with Conductor context:

1. **Add to `.cursorrules`:**
```
Conductor Documentation System Rules:
- Use type hints for all functions
- Follow async patterns for integrations
- Inherit from base classes (BaseAgent, MCPIntegration)
- Use Jinja2 for templates
- Follow the existing code structure
- Add proper docstrings
- Include error handling
```

2. **Context Files:**
```
@src/agents/base_agent.py
@src/integrations/mcp_base.py
@src/templates/
@README.md
```

### Claude Dev Integration

Create `.claude/conductor_context.md`:
```markdown
# Conductor Context

## Architecture
- Multi-agent system using CrewAI
- MCP integrations for JIRA, Confluence, GitHub
- Document generation with multiple formats
- Template-based documentation

## Patterns
- Agents inherit from BaseAgent
- Integrations inherit from MCPIntegration
- Templates use Jinja2
- CLI uses Click framework
- Async/await for integrations

## Key Classes
- DocumentationAgent: Main orchestrator
- ResearchAgent: Information gathering
- ReviewAgent: Quality assurance
- PublishAgent: Distribution
```

## 🔍 Code Navigation

### VS Code Symbols
Use these workspace symbols for quick navigation:
- `@DocumentationAgent` - Main documentation agent
- `@JiraIntegration` - JIRA integration
- `@SplunkTemplates` - Splunk templates
- `@WorkflowManager` - Workflow orchestration

### File Search Patterns
- Agent files: `*_agent.py`
- Integration files: `*_integration.py`
- Template files: `*_templates.py`
- Test files: `test_*.py`
- Example files: `examples/*.py`

## 🧪 Testing Integration

### Test-Driven Development
1. Write test first
2. Use Copilot to generate implementation
3. Run tests continuously
4. Refactor with AI assistance

### Example Test Generation Prompt
```
Generate pytest tests for the DocumentationAgent class that:
- Test document creation
- Mock external dependencies
- Test error handling
- Include async test patterns
- Use fixtures appropriately
```

## 🔧 Custom Snippets

### VS Code Snippets

Create `.vscode/conductor.code-snippets`:
```json
{
  "Conductor Agent": {
    "prefix": "agent",
    "body": [
      "from typing import Dict, Any",
      "from crewai import Task",
      "from .base_agent import BaseAgent",
      "",
      "class ${1:AgentName}(BaseAgent):",
      "    \"\"\"${2:Agent description}.\"\"\"",
      "",
      "    def __init__(self):",
      "        super().__init__(",
      "            name=\"${3:Agent Name}\",",
      "            role=\"${4:Agent Role}\",",
      "            goal=\"${5:Agent Goal}\",",
      "            backstory=\"\"\"${6:Agent Backstory}\"\"\"",
      "        )",
      "",
      "    def create_task(self, description: str, expected_output: str, **kwargs) -> Task:",
      "        \"\"\"Create a task for this agent.\"\"\"",
      "        return Task(",
      "            description=description,",
      "            expected_output=expected_output,",
      "            agent=self.agent,",
      "            context=kwargs.get('context', []),",
      "            tools=kwargs.get('tools', [])",
      "        )"
    ],
    "description": "Create new Conductor agent"
  }
}
```

## 🤝 Collaboration

### AI Pair Programming
1. Use Copilot for code generation
2. Use ChatGPT/Claude for architecture discussions
3. Use Cursor for complex refactoring
4. Validate with human review

### Code Reviews with AI
1. Use GitHub Copilot to explain code changes
2. Ask AI to identify potential issues
3. Generate test cases for new features
4. Suggest improvements

## 📚 Learning Resources

### AI Assistant Prompts
- "Explain this Conductor pattern"
- "How does this agent work?"
- "Generate tests for this integration"
- "Optimize this template"
- "Debug this workflow"

### Documentation Generation
- Use AI to generate docstrings
- Create README sections
- Generate usage examples
- Write API documentation

This integration guide helps you leverage AI assistants effectively while working with Conductor, making development faster and more intuitive.