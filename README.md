# 🤖 Conductor - AI-Native Workflow Orchestrator

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **An AI-first workflow orchestration platform that serves as your persistent digital assistant, maintaining context across conversations and automating your daily work through intelligent skill-based workflows.**

Conductor transforms how you manage daily work by providing an AI assistant that:
- 🧠 **Remembers everything** - Persistent context across all conversations
- 🛠️ **Automates workflows** - Intelligent skill-based task execution
- 📚 **Manages documentation** - AI-generated docs with version control
- ⏰ **Schedules smartly** - Context-aware reminders and follow-ups
- 🔗 **Integrates services** - Seamless JIRA, Confluence, GitHub, and more

## 🚀 Quick Start (2 minutes)

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd conductor
python3 -m venv venv && source venv/bin/activate

# 2. Install as binary with shell completion
pip install -e .
conductor completion --install

# 3. Set your AI provider (choose one)
export ANTHROPIC_API_KEY="your-claude-key"
# OR
export OPENAI_API_KEY="your-openai-key"

# 4. Start your AI assistant
conductor ai chat
```

**That's it!** You now have a persistent AI assistant with shell completion.

## 💬 AI Copilot Integration

### Core AI Interaction Patterns

```bash
# 💬 Conversational workflow management
conductor ai chat

# 🎯 Quick questions and commands
conductor ai ask "What should I prioritize today?"
conductor ai ask "Create a bug investigation workflow"
conductor ai ask "Schedule a team meeting for Friday"

# 📊 Check your AI assistant's capabilities
conductor ai status
conductor ai skills
```

### AI-Driven Workflow Examples

<details>
<summary><b>🔍 Bug Investigation Workflow</b></summary>

```bash
conductor ai ask "Help me investigate a login bug affecting production users"

# AI creates:
# ✅ Bug investigation workflow with steps
# ✅ Documentation template for findings
# ✅ Scheduled follow-up reminders
# ✅ Team notification tasks
```
</details>

<details>
<summary><b>📚 Documentation Generation</b></summary>

```bash
conductor ai ask "Create API documentation for our user service"

# AI generates:
# ✅ Comprehensive API documentation
# ✅ Code examples and usage patterns
# ✅ Publishes to Confluence (if configured)
# ✅ Sets review reminders with team
```
</details>

<details>
<summary><b>🔄 Daily Standup Prep</b></summary>

```bash
conductor ai ask "Prepare my standup notes for tomorrow"

# AI provides:
# ✅ Summary of yesterday's completed work
# ✅ Today's priorities based on deadlines
# ✅ Blockers and dependencies to discuss
# ✅ Follow-up actions needed from teammates
```
</details>

## 🧠 How AI Context Works

Conductor's AI maintains **persistent memory** about:
- **Your work patterns** - Learns how you prefer to work
- **Project context** - Remembers ongoing projects and their status
- **Team dynamics** - Understands your team structure and communication patterns
- **Tools and services** - Knows your JIRA projects, Confluence spaces, etc.
- **Preferences** - Adapts to your workflow style over time

### Context Engineering Example

```bash
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

## 🛠️ Core Skills & Automation

Conductor comes with built-in AI skills for common workflows:

### 📋 Project Management Skills
- `bug_investigation` - Comprehensive bug tracking and resolution
- `deployment_workflow` - Release planning and execution
- `code_review_process` - Systematic code review workflows

### 📚 Documentation Skills
- `create_documentation` - AI-generated technical documentation
- `update_documentation` - Keep docs current with code changes
- `api_documentation` - Auto-generate API docs from code

### 🗓️ Daily Operations Skills
- `standup_prep` - Daily meeting preparation and notes
- `follow_up_management` - Track and manage action items
- `priority_analysis` - Intelligent task prioritization

### View Available Skills
```bash
conductor ai skills --detail
```

## 🔗 Service Integrations

Conductor integrates with your existing tools through **context-aware AI**:

### Supported Services
- **JIRA** - Project tracking, issue management
- **Confluence** - Documentation and knowledge base
- **GitHub** - Code management and collaboration
- **Slack** - Team communication and notifications

### Auto-Configuration
```bash
# Set environment variables (all optional)
export JIRA_API_TOKEN="your-token"
export JIRA_SERVER_URL="https://company.atlassian.net"
export CONFLUENCE_API_TOKEN="your-token"
export GITHUB_TOKEN="your-token"

# Let AI configure integrations
conductor services --configure
conductor services --status
```

### AI-Powered Service Usage
```bash
# Instead of manually using JIRA:
conductor ai ask "Create a JIRA ticket for the login bug I found"

# Instead of manually updating Confluence:
conductor ai ask "Update our deployment docs with the new process"

# Instead of manually managing GitHub:
conductor ai ask "Create a PR for the authentication fix"
```

## 📁 Installation Methods

### Method 1: Package Installation (Recommended)
```bash
# Install as a proper Python package with shell completion
git clone <your-repo>
cd conductor
python3 -m venv venv && source venv/bin/activate
pip install -e .
conductor completion --install
```

### Method 2: Direct Script Usage
```bash
# Run directly from the repository
git clone <your-repo>
cd conductor
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python conductor.py ai chat
```

### Verify Installation
```bash
conductor --version
conductor ai status
```

## 🎯 Usage Patterns

### 🌅 Daily Workflow
```bash
# Start your day with AI
conductor ai ask "What should I focus on today?"

# Work with continuous AI assistance
conductor ai chat
# (Keep this running in a terminal for ongoing assistance)

# End of day summary
conductor ai ask "Summarize what I accomplished today"
```

### 🔄 Project Workflows
```bash
# Project initiation
conductor ai ask "Help me start the user authentication project"

# Ongoing development
conductor ai ask "I finished the login component, what's next?"

# Project completion
conductor ai ask "Create release documentation for the auth project"
```

### 📋 Task Management
```bash
# Create structured workflows
conductor ai ask "Plan out the database migration project"

# Track progress
conductor ai ask "Show me the status of all my active projects"

# Handle blockers
conductor ai ask "I'm blocked on the API integration, help me create an action plan"
```

## 🔧 Configuration

### AI Provider Setup (Required)
```bash
# Anthropic Claude (Recommended)
export ANTHROPIC_API_KEY="your-api-key"

# OpenAI GPT (Alternative)
export OPENAI_API_KEY="your-api-key"

# Verify AI setup
conductor ai status
```

### Service Integrations (Optional)
```bash
# Create .env file for integrations (optional)
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

# Slack Integration (optional)
SLACK_BOT_TOKEN=your_slack_token
EOF

# Test integrations
conductor services --status
```

## 📚 Project Structure

```
conductor/
├── 🤖 AI Core
│   ├── src/ai/orchestrator.py          # Main AI orchestration
│   ├── src/ai/context/                 # Context management & memory
│   ├── src/ai/providers/               # Claude, OpenAI providers
│   └── src/skills/                     # AI-callable workflow skills
│
├── 🔧 Core Systems
│   ├── src/core/workflow_engine.py     # Workflow execution
│   ├── src/core/doc_processor.py       # Document generation
│   ├── src/core/scheduler.py           # Smart scheduling
│   └── src/core/mcp_manager.py         # Service integrations
│
├── 🎛️ Interface
│   ├── conductor.py                    # Main CLI interface
│   ├── src/conductor_main.py           # Binary entry point
│   └── src/conductor.py                # Module interface
│
├── 📦 Package
│   ├── setup.py                        # Package configuration
│   ├── requirements.txt                 # Dependencies
│   └── venv/                           # Virtual environment
│
└── 👤 User Content (gitignored)
    ├── .conductor/                      # AI context & conversation memory
    ├── user_docs/                      # Your generated documents
    ├── user_workflows/                  # Your personal workflows
    └── workflow_templates/              # Custom workflow templates
```

## 🎨 Advanced Usage

### Custom Skill Development
```python
# Create custom AI skills for your specific workflows
from skills.base import Skill, SkillExecutionResult

class CustomDeploymentSkill(Skill):
    name = "custom_deployment"
    description = "Handle custom deployment workflow"

    async def execute(self, context, parameters, orchestrator=None):
        # Your custom workflow logic
        return SkillExecutionResult(
            success=True,
            result="Deployment workflow created",
            data={"workflow_id": "deploy-123"}
        )
```

### Programmatic API
```python
from ai.orchestrator import AIOrchestrator

# Initialize AI orchestrator
orchestrator = AIOrchestrator()

# Start AI conversation
session_id = await orchestrator.start_conversation()

# AI-driven workflow creation
response = await orchestrator.chat(
    session_id,
    "Create a deployment checklist for the new release"
)
```

## 🚀 Why AI-Native?

### Traditional Workflow Tools
- ❌ Static templates and rigid processes
- ❌ Manual task creation and tracking
- ❌ Context switching between tools
- ❌ Repetitive documentation work

### Conductor's AI-First Approach
- ✅ **Dynamic workflows** adapted to your specific situation
- ✅ **Conversational interface** - just describe what you need
- ✅ **Persistent memory** - AI remembers your preferences and context
- ✅ **Proactive assistance** - AI suggests next steps and handles follow-ups
- ✅ **Intelligent automation** - Context-aware integration with your tools

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the AI-native development patterns
4. Add tests for new functionality
5. Update documentation
6. Commit changes (`git commit -m 'Add amazing AI feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup
```bash
git clone <your-fork>
cd conductor
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"  # Install with dev dependencies
pytest  # Run tests
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Anthropic Claude](https://www.anthropic.com/) for conversational AI capabilities
- [OpenAI](https://openai.com/) for GPT model support
- [Rich](https://github.com/Textualize/rich) for beautiful CLI interfaces
- [Click](https://click.palletsprojects.com/) for CLI framework

## 🎯 Quick Command Reference

```bash
# AI Commands (Primary Interface)
conductor ai chat                 # Start conversational AI assistant
conductor ai ask "question"       # Quick AI questions and commands
conductor ai status               # Check AI provider and capabilities
conductor ai skills               # List available automation skills

# Traditional Commands (Fallback)
conductor start --dashboard       # Enhanced dashboard view
conductor workflows               # Manage workflows manually
conductor docs                    # Document management
conductor services --status       # Check service integrations
conductor completion --install    # Enable shell tab completion
```

---

**🤖 Conductor** - Your AI-native workflow orchestration platform. Less clicking, more creating. Let the AI handle the process while you focus on the work.