# Conductor

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**An AI-native workflow orchestration platform that remembers, learns, and automates your daily work through intelligent conversation.**

Conductor transforms routine work management by providing a persistent AI assistant that maintains context across all your conversations, understands your work patterns, and automatically handles the tedious parts of project coordination.

## Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd conductor
python3 -m venv venv && source venv/bin/activate

# Install with shell completion
pip install -e .
conductor completion --install

# Configure your AI provider
export ANTHROPIC_API_KEY="your-claude-key"
# OR
export OPENAI_API_KEY="your-openai-key"

# Start your AI assistant
conductor ai chat
```

## Core Philosophy

Instead of forcing you to adapt to rigid workflow templates, Conductor adapts to how you actually work. The AI learns your preferences, remembers ongoing projects, and proactively suggests next steps.

### Traditional Workflow Tools
- Static templates that don't fit your specific situation
- Manual task creation and status updates
- Context switching between multiple applications
- Repetitive documentation and follow-up work

### Conductor's Approach
- **Conversational interface** - describe what you need in natural language
- **Persistent memory** - AI remembers your projects, preferences, and work patterns
- **Dynamic workflows** - processes adapt to your specific situation
- **Proactive automation** - AI handles follow-ups and integrations automatically

## AI-Driven Workflow Examples

**Bug Investigation Workflow**
```bash
conductor ai ask "Help me investigate a login bug affecting production users"

# AI automatically creates:
# - Bug investigation workflow with specific steps
# - Documentation template for findings
# - Scheduled follow-up reminders
# - Team notification tasks
```

**Documentation Generation**
```bash
conductor ai ask "Create API documentation for our user service"

# AI generates:
# - Comprehensive API documentation
# - Code examples and usage patterns
# - Publishes to Confluence (if configured)
# - Sets review reminders with team
```

**Daily Standup Preparation**
```bash
conductor ai ask "Prepare my standup notes for tomorrow"

# AI provides:
# - Summary of yesterday's completed work
# - Today's priorities based on deadlines
# - Blockers and dependencies to discuss
# - Follow-up actions needed from teammates
```

## How AI Context Works

Conductor's AI maintains persistent memory about your work environment:

- **Work patterns** - learns how you prefer to structure projects
- **Project context** - remembers ongoing initiatives and their status
- **Team dynamics** - understands your team structure and communication style
- **Tools and services** - knows your JIRA projects, Confluence spaces, etc.
- **Preferences** - adapts to your workflow style over time

### Context Engineering in Action

```
You: "I'm starting work on the authentication system refactor"

AI: I remember you mentioned this project last week. Based on our previous
    conversations, I'll:

    1. Create a technical design document workflow
    2. Set up code review checkpoints with the security team
    3. Schedule integration testing milestones
    4. Create documentation for the API changes

    I notice this relates to the Q2 security initiative. Should I also
    coordinate with Maria's compliance review timeline?
```

## Built-in Skills & Automation

Conductor includes AI skills for common development workflows:

**Project Management**
- `bug_investigation` - comprehensive bug tracking and resolution
- `deployment_workflow` - release planning and execution
- `code_review_process` - systematic code review workflows

**Documentation**
- `create_documentation` - AI-generated technical documentation
- `update_documentation` - keep docs current with code changes
- `api_documentation` - auto-generate API docs from code

**Daily Operations**
- `standup_prep` - daily meeting preparation and notes
- `follow_up_management` - track and manage action items
- `priority_analysis` - intelligent task prioritization

```bash
conductor ai skills --detail  # View all available skills
```

## Service Integrations

Conductor integrates with your existing tools through context-aware AI:

**Supported Services**
- JIRA - project tracking, issue management
- Confluence - documentation and knowledge base
- GitHub - code management and collaboration
- Slack - team communication and notifications

**Configuration**
```bash
# Set environment variables (all optional)
export JIRA_API_TOKEN="your-token"
export JIRA_SERVER_URL="https://company.atlassian.net"
export CONFLUENCE_API_TOKEN="your-token"
export GITHUB_TOKEN="your-token"

# Verify integrations
conductor services --status
```

**AI-Powered Usage**
```bash
# Instead of manually using JIRA:
conductor ai ask "Create a JIRA ticket for the login bug I found"

# Instead of manually updating Confluence:
conductor ai ask "Update our deployment docs with the new process"

# Instead of manually managing GitHub:
conductor ai ask "Create a PR for the authentication fix"
```

## Daily Usage Patterns

**Morning Startup**
```bash
conductor ai ask "What should I focus on today?"
```

**Continuous Assistance**
```bash
conductor ai chat  # Keep running in a terminal
```

**Project Management**
```bash
conductor ai ask "Help me start the user authentication project"
conductor ai ask "I finished the login component, what's next?"
conductor ai ask "Create release documentation for the auth project"
```

**End of Day**
```bash
conductor ai ask "Summarize what I accomplished today"
```

## Advanced Configuration

### AI Provider Setup
```bash
# Anthropic Claude (recommended)
export ANTHROPIC_API_KEY="your-api-key"

# OpenAI GPT (alternative)
export OPENAI_API_KEY="your-api-key"

# Verify setup
conductor ai status
```

### Optional Service Integrations
```bash
# Create .env file
cat > .env << EOF
# JIRA Integration
JIRA_API_TOKEN=your_jira_token
JIRA_SERVER_URL=https://company.atlassian.net
JIRA_USERNAME=your@email.com

# Confluence Integration
CONFLUENCE_API_TOKEN=your_confluence_token
CONFLUENCE_SERVER_URL=https://company.atlassian.net

# GitHub Integration
GITHUB_TOKEN=your_github_token
EOF
```

## Architecture

Conductor is built around three core systems:

**AI Core** - conversation management, persistent memory, skill execution
**Workflow Engine** - dynamic process creation and execution
**Integration Layer** - context-aware service connections

```
conductor/
├── AI Core
│   ├── src/ai/orchestrator.py          # Main AI orchestration
│   ├── src/ai/context/                 # Context management & memory
│   ├── src/ai/providers/               # Claude, OpenAI providers
│   └── src/skills/                     # AI-callable workflow skills
│
├── Core Systems
│   ├── src/core/workflow_engine.py     # Workflow execution
│   ├── src/core/doc_processor.py       # Document generation
│   ├── src/core/scheduler.py           # Smart scheduling
│   └── src/core/mcp_manager.py         # Service integrations
│
└── User Content (automatically gitignored)
    ├── .conductor/                     # AI context & memory
    ├── user_docs/                     # Generated documents
    └── user_workflows/                 # Personal workflows
```

## Custom Development

**Creating Custom Skills**
```python
from skills.base import Skill, SkillExecutionResult

class CustomDeploymentSkill(Skill):
    name = "custom_deployment"
    description = "Handle custom deployment workflow"

    async def execute(self, context, parameters, orchestrator=None):
        # Your workflow logic
        return SkillExecutionResult(
            success=True,
            result="Deployment workflow created",
            data={"workflow_id": "deploy-123"}
        )
```

**Programmatic API**
```python
from ai.orchestrator import AIOrchestrator

orchestrator = AIOrchestrator()
session_id = await orchestrator.start_conversation()

response = await orchestrator.chat(
    session_id,
    "Create a deployment checklist for the new release"
)
```

## Command Reference

```bash
# Primary AI Interface
conductor ai chat                 # Conversational AI assistant
conductor ai ask "question"       # Quick AI questions and commands
conductor ai status               # Check AI provider and capabilities
conductor ai skills               # List available automation skills

# Traditional Interface
conductor workflows               # Manual workflow management
conductor docs                    # Document management
conductor services --status       # Service integration status
conductor completion --install    # Shell completion setup
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow AI-native development patterns
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

**Development Setup**
```bash
git clone <your-fork>
cd conductor
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest  # Run tests
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Conductor** - AI-native workflow orchestration. Less process management, more productive work.