# MCP Integration Setup for Conductor

## Problem Statement

VSCode MCP extensions are isolated from Conductor's Claude API calls. This document explains how to bridge MCP services so Conductor can use them.

## Solution: Local MCP Bridge

### Setup 1: Standalone MCP Server Configuration

Create a local MCP configuration that Conductor can access:

```bash
# 1. Install MCP servers locally (outside VSCode)
npm install -g @modelcontextprotocol/server-jira
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-slack

# 2. Create MCP config for Conductor
mkdir -p ~/.conductor/mcp
```

**File: `~/.conductor/mcp/config.json`**
```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-jira"],
      "env": {
        "JIRA_API_TOKEN": "your_jira_token",
        "JIRA_HOST": "your-company.atlassian.net",
        "JIRA_EMAIL": "your-email@company.com"
      }
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your_github_token"
      }
    }
  }
}
```

### Setup 2: MCP Proxy Service

Create a proxy that forwards MCP calls between Conductor and VSCode:

**File: `scripts/mcp-proxy.js`**
```javascript
#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');

// Proxy MCP calls to VSCode extension MCP servers
class MCPProxy {
  constructor() {
    this.vscodeConnections = new Map();
  }

  // Forward tool calls to appropriate VSCode MCP server
  async forwardToVSCode(toolName, params) {
    // Implementation to bridge VSCode MCP extension
    // Uses VSCode extension API or socket communication
  }
}

const proxy = new MCPProxy();
const server = new Server(
  {
    name: "conductor-mcp-proxy",
    version: "1.0.0"
  },
  {
    capabilities: {
      tools: {
        // Expose all VSCode MCP tools here
      }
    }
  }
);

// Register tools that forward to VSCode
server.setRequestHandler('tools/call', proxy.forwardToVSCode.bind(proxy));

const transport = new StdioServerTransport();
server.connect(transport);
```

### Setup 3: Environment Variable Bridge

**File: `.env.mcp`**
```bash
# Copy your VSCode MCP credentials here for Conductor to use
JIRA_API_TOKEN=your_token_from_vscode_config
JIRA_HOST=your_host_from_vscode_config
GITHUB_TOKEN=your_token_from_vscode_config
SLACK_BOT_TOKEN=your_token_from_vscode_config

# Conductor will use these to create its own MCP connections
MCP_BRIDGE_ENABLED=true
MCP_CONFIG_PATH=~/.conductor/mcp/config.json
```

## Usage in Skills

### Before (Broken):
```markdown
# JIRA Quarter Update Skill
- Uses JIRA MCP integration
- ERROR: No JIRA MCP access from Conductor's Claude API calls
```

### After (Working):
```markdown
# JIRA Quarter Update Skill

## Context for AI Agent
When executing this skill, use the local MCP JIRA integration:

1. **Check MCP Connection**: Verify JIRA MCP server is available
2. **Execute JIRA Queries**: Use mcp://jira/search-issues tool
3. **Update Tickets**: Use mcp://jira/update-issue tool
4. **Handle Errors**: MCP connection issues, auth failures, etc.

The AI should use MCP tool calls like:
```
Tool: mcp://jira/search-issues
Params: {
  "jql": "project = MYPROJ AND status != Done",
  "fields": ["key", "summary", "customfield_target_quarter"]
}
```
```

### Implementation in Conductor

**File: `src/core/mcp_local_bridge.py`**
```python
class LocalMCPBridge:
    """Bridge between Conductor and local/VSCode MCP servers"""

    def __init__(self):
        self.config = self.load_mcp_config()
        self.connections = {}

    async def call_mcp_tool(self, tool_name: str, params: dict):
        """Call MCP tool and return result"""
        server_name = self.get_server_for_tool(tool_name)

        if server_name not in self.connections:
            await self.connect_to_server(server_name)

        return await self.connections[server_name].call_tool(tool_name, params)

    def load_mcp_config(self):
        """Load MCP configuration from ~/.conductor/mcp/config.json"""
        config_path = Path.home() / '.conductor' / 'mcp' / 'config.json'
        if config_path.exists():
            return json.loads(config_path.read_text())
        return {}
```

## User Setup Instructions

### Step 1: Copy VSCode MCP Configuration
```bash
# If you have JIRA MCP in VSCode, copy the credentials:
conductor mcp --copy-from-vscode

# This automatically creates ~/.conductor/mcp/config.json
```

### Step 2: Test MCP Connection
```bash
conductor mcp --test-connection jira
# Should show: ✅ JIRA MCP connected successfully
```

### Step 3: Create Skills Using MCP
```bash
conductor ai ask "Create a JIRA skill using the MCP integration I just configured"
```

## Alternative: Claude Desktop Integration

### Option: Use Claude Desktop as MCP Proxy
1. Run Claude Desktop alongside Conductor
2. Conductor sends requests to Claude Desktop via API
3. Claude Desktop uses its MCP connections to execute tools
4. Results flow back to Conductor

**Pros**: No duplication of MCP setup
**Cons**: Requires Claude Desktop to be running, more complex architecture

## Migration Path

### Phase 1: Environment Variable Fallback
- Skills check for MCP, fall back to direct API calls
- Use `JIRA_API_TOKEN` directly if MCP unavailable

### Phase 2: Local MCP Setup
- Users configure local MCP servers
- Conductor connects directly to MCP

### Phase 3: Universal MCP Bridge
- Conductor automatically discovers available MCP servers
- Seamless integration with VSCode, Claude Desktop, or standalone

---

**Status**: Architecture design
**Priority**: Critical for skill ecosystem
**Impact**: Enables all external tool integrations in skills