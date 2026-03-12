# Complete MCP Setup Guide for VSCode Copilot Users

**Target Audience**: VSCode users with GitHub Copilot who want to use Conductor with external tool integrations (JIRA, GitHub, Confluence)

This guide walks you through setting up MCP (Model Context Protocol) integration with Conductor, enabling your AI conversations to directly interact with external services like JIRA, GitHub, and Confluence.

## Table of Contents

1. [What is MCP and Why Use It?](#what-is-mcp-and-why-use-it)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Service Configuration](#service-configuration)
5. [VSCode Copilot Integration](#vscode-copilot-integration)
6. [Creating Skills with MCP](#creating-skills-with-mcp)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## What is MCP and Why Use It?

**MCP (Model Context Protocol)** is a standardized way for AI agents to interact with external tools and services. With MCP integration, Conductor can:

- 🎯 **Execute JIRA queries** and update tickets directly from AI conversations
- 🚀 **Create GitHub issues** and pull requests automatically
- 📚 **Search and update Confluence** pages with generated content
- 🔗 **Chain multiple services** together in a single AI workflow

**Before MCP**: "Can you help me plan my sprint?"
**After MCP**: "Update all JIRA tickets in project XYZ to target quarter FY26Q3" → *AI automatically finds and updates 47 tickets*

---

## Prerequisites

### Required Software

1. **Node.js** (for MCP servers)
   ```bash
   # Check if installed
   node --version
   npm --version

   # If not installed, download from https://nodejs.org/
   # Or using Homebrew (macOS):
   brew install node
   ```

2. **VSCode** with GitHub Copilot (already installed)

3. **Conductor** (this repository)
   ```bash
   # Clone and install
   git clone <this-repo>
   cd conductor
   pip install -e .

   # Verify installation
   conductor --help
   ```

### Service Accounts Needed

You'll need API credentials for the services you want to integrate:

- **JIRA**: API Token from Atlassian
- **GitHub**: Personal Access Token
- **Confluence**: API Token (same as JIRA if using Atlassian)

---

## Quick Start

### Step 1: Initialize MCP Configuration

Open a terminal in this conductor repository and run:

```bash
# Install MCP servers and create initial configuration
conductor mcp setup --install-servers

# Check setup status
conductor mcp status
```

This creates the configuration file at `~/.conductor/mcp/config.json` with templates for JIRA and GitHub.

### Step 2: Configure Service Credentials

Edit the MCP configuration with your API credentials:

```bash
# Open configuration file in your editor
conductor mcp config --edit

# Or edit manually at:
# ~/.conductor/mcp/config.json
```

**Update the template values**:
```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-jira"],
      "env": {
        "JIRA_API_TOKEN": "your_actual_jira_token",
        "JIRA_HOST": "your-company.atlassian.net",
        "JIRA_EMAIL": "your-email@company.com",
        "JIRA_PROJECT": "YOUR_PROJECT_KEY"
      }
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your_github_personal_access_token",
        "GITHUB_OWNER": "your_github_username",
        "GITHUB_REPO": "your_repository_name"
      }
    }
  }
}
```

### Step 3: Test Connections

```bash
# Test specific service
conductor mcp test jira
conductor mcp test github

# Check overall status
conductor mcp status
```

### Step 4: Try Your First MCP-Enabled Conversation

```bash
# Start AI conversation with MCP tools available
conductor ai chat

# Try a command like:
# "Search for all JIRA tickets in project ABC that are still open"
# "Create a GitHub issue for the bug we discussed"
```

---

## Service Configuration

### JIRA Configuration

#### Getting Your JIRA API Token

1. Go to **Atlassian Account Settings**: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Name it "Conductor MCP Integration"
4. Copy the generated token

#### JIRA Configuration Example

```json
"jira": {
  "command": "npx",
  "args": ["@modelcontextprotocol/server-jira"],
  "env": {
    "JIRA_API_TOKEN": "ATxxxxxxxxxxxxxxxxxxxxxxxx",
    "JIRA_HOST": "mycompany.atlassian.net",
    "JIRA_EMAIL": "john.doe@mycompany.com",
    "JIRA_PROJECT": "PROJ"
  }
}
```

#### Available JIRA Operations

Once configured, your AI can use these JIRA operations:
- `mcp_jira_search_issues` - Search for tickets using JQL
- `mcp_jira_update_issue` - Update ticket fields
- `mcp_jira_create_issue` - Create new tickets
- `mcp_jira_get_issue` - Get detailed ticket information

### GitHub Configuration

#### Getting Your GitHub Token

1. Go to **GitHub Settings**: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Select scopes: `repo`, `write:org`, `read:user`
4. Click **"Generate token"** and copy it

#### GitHub Configuration Example

```json
"github": {
  "command": "npx",
  "args": ["@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "GITHUB_OWNER": "myusername",
    "GITHUB_REPO": "my-project"
  }
}
```

#### Available GitHub Operations

- `mcp_github_create_issue` - Create GitHub issues
- `mcp_github_list_issues` - List repository issues
- `mcp_github_create_pr` - Create pull requests
- `mcp_github_search_repos` - Search repositories

### Confluence Configuration

#### Adding Confluence Support

Add this to your MCP configuration:

```json
"confluence": {
  "command": "npx",
  "args": ["@modelcontextprotocol/server-confluence"],
  "env": {
    "CONFLUENCE_API_TOKEN": "ATxxxxxxxxxxxxxxxxxxxxxxxx",
    "CONFLUENCE_HOST": "https://mycompany.atlassian.net/wiki",
    "CONFLUENCE_EMAIL": "john.doe@mycompany.com",
    "CONFLUENCE_SPACE": "TEAM"
  }
}
```

#### Available Confluence Operations

- `mcp_confluence_search_pages` - Search wiki pages
- `mcp_confluence_create_page` - Create new pages
- `mcp_confluence_update_page` - Update existing pages
- `mcp_confluence_get_page` - Get page content

---

## VSCode Copilot Integration

### Automatic Bridge Detection

If you already have MCP configured in VSCode, Conductor can automatically detect and use your existing settings:

```bash
# This will scan your VSCode settings and import MCP configurations
conductor mcp setup --copy-from-vscode
```

### Manual VSCode MCP Setup

If you want to configure MCP in VSCode first, add this to your VSCode `settings.json`:

```json
{
  "claude.mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-jira"],
      "env": {
        "JIRA_API_TOKEN": "your_token_here",
        "JIRA_HOST": "your-company.atlassian.net",
        "JIRA_EMAIL": "your-email@company.com"
      }
    }
  }
}
```

Then run:
```bash
conductor mcp setup --copy-from-vscode
```

### Using Both VSCode Copilot and Conductor

The ideal setup lets you use both:

1. **VSCode Copilot**: For code-related tasks with MCP tools
2. **Conductor**: For workflow automation and complex multi-step processes

Both share the same MCP configuration, so skills created in either environment work in both.

---

## Creating Skills with MCP

### What are Skills?

Skills in Conductor are AI-powered workflows that can use MCP tools to automate complex tasks. Here's how to create them:

### Example: JIRA Quarter Update Skill

1. **Start an AI conversation**:
   ```bash
   conductor ai chat
   ```

2. **Request skill creation**:
   ```
   User: Create a skill that updates all JIRA tickets in a project to a specific target quarter

   AI: I'll create a JIRA Quarter Update skill for you. This skill will:
   - Search for tickets using JQL queries
   - Show you a preview of changes
   - Bulk update the target_quarter field

   The skill will use these MCP tools:
   - mcp_jira_search_issues: To find matching tickets
   - mcp_jira_update_issue: To update target_quarter fields

   Would you like me to create this skill now?
   ```

3. **The AI creates the skill** using the MCP JIRA integration automatically

### Example: GitHub Documentation Sync Skill

```
User: Create a skill that takes our project documentation and creates GitHub wiki pages

AI: I'll create a Documentation Sync skill that:
- Scans your local documentation files
- Uses mcp_github_create_issue to track documentation updates
- Updates your project's GitHub wiki automatically
- Maintains a sync log of what was updated
```

### Skill Storage

Skills are stored in `user_workflows/skills/` and include:
- **Skill Definition**: What the skill does and when to trigger it
- **MCP Integration Context**: Which tools to use and how
- **Example Usage**: Sample commands and expected outputs

### Managing Skills

```bash
# List available skills
conductor workflows list --skills

# See detailed skill information
conductor workflows list --skills --detail

# Test a specific skill
conductor ai chat
# Then: "Run the JIRA Quarter Update skill for project MYPROJ"
```

---

## Troubleshooting

### Common Issues

#### 1. "No such command 'mcp'"

**Problem**: Conductor binary not properly installed
```bash
# Solution: Reinstall conductor
pip install -e .

# Verify
conductor --help | grep mcp
```

#### 2. "npx: command not found"

**Problem**: Node.js not installed or not in PATH
```bash
# Check Node.js installation
which node
which npx

# If missing, install Node.js
# macOS: brew install node
# Windows: Download from https://nodejs.org/
```

#### 3. "Failed to start MCP server"

**Problem**: MCP server packages not published yet

**Solution**: The MCP server packages in the configuration are examples. Real MCP servers may have different package names. For now, this creates the infrastructure - actual server packages will be available later.

#### 4. "VSCode settings.json has formatting issues"

**Problem**: JSON parsing error in VSCode settings

**Solution**: Conductor handles this automatically and will still create a working configuration using templates.

#### 5. JIRA/GitHub Authentication Errors

**Problem**: Invalid credentials or insufficient permissions

**Checklist**:
- [ ] API token is valid and not expired
- [ ] Email matches the token's account
- [ ] Host URL is correct (no trailing slashes)
- [ ] Token has required permissions (JIRA: Administer projects, GitHub: repo access)

#### 6. "Connection test failed"

**Problem**: Network issues or service unavailable

```bash
# Test manually
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://api.github.com/user"

# Test JIRA
curl -u your-email@company.com:YOUR_JIRA_TOKEN \
     "https://your-company.atlassian.net/rest/api/2/myself"
```

### Debug Mode

Enable detailed logging:

```bash
# Set environment variable for debug mode
export CONDUCTOR_DEBUG=true

# Run commands with debug output
conductor mcp status
conductor mcp test jira
```

### Getting Help

1. **Check logs**: Look in `~/.conductor/logs/` for detailed error logs
2. **Verify configuration**: `conductor mcp config --show`
3. **Test step by step**:
   ```bash
   conductor mcp status
   conductor mcp test jira
   conductor mcp test github
   conductor ai chat
   ```

---

## Advanced Configuration

### Multiple JIRA Projects

Configure multiple JIRA projects:

```json
{
  "mcpServers": {
    "jira_project_a": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-jira"],
      "env": {
        "JIRA_API_TOKEN": "your_token",
        "JIRA_HOST": "company.atlassian.net",
        "JIRA_EMAIL": "your-email@company.com",
        "JIRA_PROJECT": "PROJ_A"
      }
    },
    "jira_project_b": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-jira"],
      "env": {
        "JIRA_API_TOKEN": "your_token",
        "JIRA_HOST": "company.atlassian.net",
        "JIRA_EMAIL": "your-email@company.com",
        "JIRA_PROJECT": "PROJ_B"
      }
    }
  }
}
```

### Environment-Specific Configurations

Create different configs for different environments:

```bash
# Development environment
cp ~/.conductor/mcp/config.json ~/.conductor/mcp/config.dev.json

# Production environment
cp ~/.conductor/mcp/config.json ~/.conductor/mcp/config.prod.json

# Switch configurations
export CONDUCTOR_MCP_CONFIG=~/.conductor/mcp/config.dev.json
```

### Custom MCP Servers

If you have custom MCP servers:

```json
"my_custom_service": {
  "command": "python",
  "args": ["/path/to/my/mcp_server.py"],
  "env": {
    "API_KEY": "your_custom_api_key",
    "SERVICE_URL": "https://my-custom-service.com"
  }
}
```

### Backup and Restore

```bash
# Backup your MCP configuration
cp ~/.conductor/mcp/config.json ~/mcp-config-backup.json

# Restore from backup
cp ~/mcp-config-backup.json ~/.conductor/mcp/config.json

# Verify restoration
conductor mcp status
```

---

## Security Best Practices

### API Token Security

1. **Use least privilege**: Only grant necessary permissions
2. **Rotate regularly**: Update API tokens every 90 days
3. **Environment variables**: Store sensitive tokens in environment variables instead of config files
4. **Separate tokens**: Use different tokens for different projects/environments

### Configuration File Security

```bash
# Secure the configuration file
chmod 600 ~/.conductor/mcp/config.json

# Ensure only your user can read it
ls -la ~/.conductor/mcp/config.json
# Should show: -rw------- 1 yourusername yourusername
```

### Network Security

- **Use HTTPS**: All API calls use HTTPS/TLS
- **VPN**: Consider using VPN for sensitive corporate environments
- **IP Restrictions**: Configure IP allowlists on service side if available

---

## Next Steps

### 1. Create Your First Skill

Try creating a skill that solves a real workflow problem:

```bash
conductor ai chat

# Example requests:
# "Create a skill that syncs my daily standup notes to JIRA ticket comments"
# "Create a skill that creates GitHub issues from JIRA bugs"
# "Create a skill that updates Confluence with sprint retrospective notes"
```

### 2. Automate Regular Tasks

Set up skills for recurring workflows:
- Weekly sprint planning
- Daily standup preparation
- End-of-sprint reporting
- Documentation updates

### 3. Integrate with Team Workflows

Share your successful skills with your team by documenting them in `user_workflows/skills/`.

### 4. Explore Advanced Features

- **Skill chaining**: Connect multiple skills together
- **Conditional logic**: Skills that make decisions based on data
- **Scheduled execution**: Run skills on a schedule
- **Webhook triggers**: Skills that respond to external events

---

## Conclusion

You now have MCP integration set up between VSCode Copilot and Conductor, enabling powerful workflow automation with your existing tools. The AI can now:

✅ Search and update JIRA tickets
✅ Create and manage GitHub issues
✅ Update Confluence documentation
✅ Chain multiple operations together
✅ Learn from your patterns and preferences

**Pro Tip**: Start small with simple skills (like "search JIRA tickets") and gradually build more complex workflows as you get comfortable with the system.

---

*Last updated: March 2026*
*This guide assumes MCP servers will be published to npm as the protocol matures.*