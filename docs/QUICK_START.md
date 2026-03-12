# Quick Start Guide

Get up and running with Conductor in minutes! This guide will walk you through the essential steps to start generating professional documentation.

## ⚡ 5-Minute Setup

### 1. Install Requirements
```bash
# Prerequisites
- Python 3.9+
- OpenAI API key
- Git

# Clone repository
git clone https://github.com/your-org/conductor.git
cd conductor
```

### 2. Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your OpenAI API key to .env
echo "OPENAI_API_KEY=your_key_here" >> .env
```

### 3. First Documentation
```bash
# Make CLI executable
chmod +x conductor.py

# Generate your first document
./conductor.py generate --interactive
```

That's it! 🎉 You're now ready to create professional documentation.

## 🎯 Basic Usage Examples

### Simple Documentation Generation
```bash
# Basic generation with notes
./conductor.py generate \
  --notes "Setup Splunk forwarder on Linux servers. Configure inputs.conf for log collection." \
  --title "Splunk Forwarder Setup Guide" \
  --format pdf
```

### With Splunk Template
```bash
# Use Splunk-specific template
./conductor.py generate \
  --notes "Create alert for high CPU usage. Alert when CPU > 80% for 5 minutes." \
  --title "High CPU Alert Configuration" \
  --type technical_procedure \
  --template splunk
```

### Interactive Mode (Recommended for beginners)
```bash
# Let Conductor guide you through the process
./conductor.py generate --interactive
```

## 🔧 Configuration

### Minimal Configuration (.env)
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional - add as needed
JIRA_API_TOKEN=your_jira_token
JIRA_SERVER_URL=https://company.atlassian.net
CONFLUENCE_API_TOKEN=your_confluence_token
GITHUB_TOKEN=your_github_token
```

### Check Your Setup
```bash
# Verify configuration
./conductor.py config
```

## 📋 Common Use Cases

### 1. Splunk Procedure Documentation
```bash
./conductor.py generate \
  --notes "Deploy new Splunk app: 1) Download app 2) Install on search heads 3) Configure permissions 4) Test functionality" \
  --title "Splunk App Deployment" \
  --type technical_procedure \
  --format docx
```

### 2. Alert Configuration Guide
```bash
./conductor.py generate \
  --notes "Failed login alert: search failed authentications, alert on >5 failures from same IP in 10 min, email security team" \
  --title "Failed Login Alert Setup" \
  --template splunk \
  --format pdf
```

### 3. Troubleshooting Documentation
```bash
./conductor.py generate \
  --notes "Indexer disk space issues: check disk usage, clean old logs, expand storage, monitor trends" \
  --title "Indexer Storage Troubleshooting" \
  --type troubleshooting_guide
```

### 4. Multiple Formats
```bash
# Generate in multiple formats at once
./conductor.py generate \
  --notes "Search optimization techniques" \
  --title "Splunk Search Best Practices" \
  --format docx,pdf,markdown
```

## 🔍 Exploring Features

### View Available Templates
```bash
# Splunk templates
./conductor.py template --type splunk

# General templates
./conductor.py template --type base

# Generate sample template
./conductor.py template --type splunk --template alert_configuration --output sample.md
```

### Search Integration Services
```bash
# Search JIRA (requires configuration)
./conductor.py search --query "indexer issues" --service jira

# Search Confluence
./conductor.py search --query "deployment guide" --service confluence
```

## 🚀 Advanced Quick Start

### Docker Setup
```bash
# Quick start with Docker
docker-compose up conductor

# Run with environment file
docker-compose --env-file .env run conductor generate --interactive
```

### With Research Integration
```bash
./conductor.py generate \
  --notes "Configure index clustering" \
  --title "Splunk Index Cluster Setup" \
  --research \
  --publish
```

### Batch Processing
```python
# Python script for multiple documents
from src.core.document_generator import DocumentGenerator

docs = [
    {"notes": "Alert setup guide", "title": "Alert Configuration"},
    {"notes": "Dashboard creation", "title": "Dashboard Guide"}
]

generator = DocumentGenerator()
for doc in docs:
    result = generator.generate_document(
        content=doc["notes"],
        title=doc["title"],
        output_format="pdf"
    )
```

## 📚 Next Steps

### Learn More
- 📖 Read the [full documentation](README.md)
- 🧪 Explore [examples](examples/)
- 🤝 Check [contributing guide](CONTRIBUTING.md)
- 🔧 Review [IDE integration](docs/IDE_INTEGRATION.md)

### Common Next Actions

1. **Configure MCP Services**: Add JIRA, Confluence, GitHub tokens
2. **Customize Templates**: Create your own organization-specific templates
3. **Set up Automation**: Create workflow templates for common tasks
4. **Integrate with CI/CD**: Add documentation generation to your pipelines

### Get Help
- 🐛 [Report issues](https://github.com/your-org/conductor/issues)
- 💬 [Join discussions](https://github.com/your-org/conductor/discussions)
- 📧 Email: support@conductor-docs.dev

## 🎓 Tutorial: Your First Workflow

Let's create a complete Splunk documentation workflow:

### Step 1: Basic Document
```bash
./conductor.py generate --interactive
```
When prompted:
- **Notes**: "Configure Splunk Universal Forwarder on Windows servers for log collection"
- **Title**: "Windows Forwarder Setup Guide"
- **Research**: No (for now)
- **Publish**: No (for now)

### Step 2: Add Research
First configure JIRA in `.env`:
```bash
JIRA_API_TOKEN=your_token
JIRA_SERVER_URL=https://company.atlassian.net
JIRA_USERNAME=your_email
```

Then generate with research:
```bash
./conductor.py generate \
  --notes "Troubleshoot forwarder connectivity issues" \
  --title "Forwarder Troubleshooting" \
  --research \
  --format pdf
```

### Step 3: Full Automation
```bash
./conductor.py generate \
  --notes "Deploy monitoring dashboard for infrastructure metrics" \
  --title "Infrastructure Monitoring Dashboard" \
  --research \
  --publish \
  --format docx,pdf,markdown
```

## ✅ Success Indicators

You'll know Conductor is working correctly when:
- ✅ `./conductor.py config` shows configured services
- ✅ Documents generate in the `output/` directory
- ✅ Generated documents are well-formatted and professional
- ✅ Interactive mode guides you through the process smoothly

## 🔧 Troubleshooting Quick Fixes

### Common Issues

**"Command not found: ./conductor.py"**
```bash
chmod +x conductor.py
python conductor.py generate --help
```

**"OpenAI API Error"**
```bash
# Check API key in .env file
echo $OPENAI_API_KEY
# Verify key is valid at platform.openai.com
```

**"No documents generated"**
```bash
# Check output directory
ls -la output/
# Verify write permissions
mkdir -p output && chmod 755 output
```

**"Import errors"**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

## 🎉 You're Ready!

Congratulations! You now have a powerful AI-driven documentation system. Start with simple documents and gradually explore advanced features like:

- 🔍 Research integration
- 📤 Automated publishing
- 🎨 Custom templates
- 🤖 Workflow automation

Happy documenting! 🚀