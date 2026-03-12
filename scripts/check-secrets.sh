#!/bin/bash
# Check for hardcoded API keys, secrets, and credentials in code

set -e

echo "🔐 Scanning for hardcoded secrets..."

# Define patterns to look for
SECRET_PATTERNS=(
    # API Keys
    "OPENAI_API_KEY\s*=\s*['\"][^'\"]+['\"]"
    "ANTHROPIC_API_KEY\s*=\s*['\"][^'\"]+['\"]"
    "CLAUDE_API_KEY\s*=\s*['\"][^'\"]+['\"]"
    "JIRA_API_TOKEN\s*=\s*['\"][^'\"]+['\"]"
    "CONFLUENCE_API_TOKEN\s*=\s*['\"][^'\"]+['\"]"
    "GITHUB_TOKEN\s*=\s*['\"][^'\"]+['\"]"
    "SLACK_BOT_TOKEN\s*=\s*['\"][^'\"]+['\"]"

    # Generic patterns
    "api[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9]{20,}['\"]"
    "secret[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9]{20,}['\"]"
    "access[_-]?token\s*[=:]\s*['\"][a-zA-Z0-9]{20,}['\"]"
    "bearer\s+[a-zA-Z0-9]{20,}"

    # Specific service patterns
    "sk-[a-zA-Z0-9]{32,}"  # OpenAI API keys
    "xoxb-[a-zA-Z0-9-]+"   # Slack bot tokens
    "ghp_[a-zA-Z0-9]{36}"  # GitHub personal access tokens
    "ghs_[a-zA-Z0-9]{36}"  # GitHub app tokens

    # Private keys
    "BEGIN\s+(RSA\s+)?PRIVATE\s+KEY"
    "BEGIN\s+OPENSSH\s+PRIVATE\s+KEY"
    "BEGIN\s+DSA\s+PRIVATE\s+KEY"
    "BEGIN\s+EC\s+PRIVATE\s+KEY"
    "BEGIN\s+PGP\s+PRIVATE\s+KEY"

    # Database URLs with credentials
    "(mysql|postgresql|mongodb)://[^/\s]+:[^@\s]+@"
    "postgres://[^/\s]+:[^@\s]+@"

    # AWS credentials
    "AKIA[0-9A-Z]{16}"
    "aws[_-]?access[_-]?key"
    "aws[_-]?secret"

    # Common test credentials (should still be flagged)
    "password\s*[=:]\s*['\"]123456['\"]"
    "password\s*[=:]\s*['\"]admin['\"]"
    "password\s*[=:]\s*['\"]test['\"]"
)

VIOLATIONS=0
TOTAL_FILES=0

# Function to scan a file
scan_file() {
    local file="$1"
    local found_secrets=0

    for pattern in "${SECRET_PATTERNS[@]}"; do
        matches=$(grep -inE "$pattern" "$file" 2>/dev/null || true)
        if [ -n "$matches" ]; then
            # Filter out documentation examples and placeholders
            filtered_matches=$(echo "$matches" | grep -vE "(your-|fake-|example|placeholder|test-|demo-)" || true)

            if [ -n "$filtered_matches" ]; then
                if [ $found_secrets -eq 0 ]; then
                    echo ""
                    echo "🚨 SECRETS FOUND in $file:"
                    found_secrets=1
                fi
                echo "   Line $(echo "$filtered_matches" | cut -d: -f1): $(echo "$filtered_matches" | cut -d: -f2-)"
            fi
        fi
    done

    if [ $found_secrets -eq 1 ]; then
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
}

# Scan all relevant files
echo "📁 Scanning files..."

# Get list of files to scan (excluding user content and virtual environments)
FILES=$(find . -type f \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.md" -o -name "*.txt" -o -name "*.sh" \) \
    ! -path "./venv/*" \
    ! -path "./.venv/*" \
    ! -path "./user_docs/*" \
    ! -path "./user_workflows/*" \
    ! -path "./.conductor/*" \
    ! -path "./.git/*" \
    ! -path "./scripts/check-secrets.sh" \
    ! -name ".secrets.baseline" \
    ! -name "bandit-report.json")

for file in $FILES; do
    TOTAL_FILES=$((TOTAL_FILES + 1))
    scan_file "$file"
done

echo ""
echo "📊 Scan Results:"
echo "   Files scanned: $TOTAL_FILES"
echo "   Files with secrets: $VIOLATIONS"

if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ No hardcoded secrets detected!"
    exit 0
else
    echo ""
    echo "❌ Found hardcoded secrets in $VIOLATIONS file(s)!"
    echo ""
    echo "💡 To fix:"
    echo "   1. Replace hardcoded secrets with environment variables"
    echo "   2. Use os.getenv('SECRET_NAME') or similar"
    echo "   3. Add actual secrets to .env file (which is gitignored)"
    echo "   4. Use secure secret management in production"
    echo ""
    echo "Example:"
    echo "   # Bad:"
    echo "   api_key = 'sk-abc123...'"
    echo ""
    echo "   # Good:"
    echo "   api_key = os.getenv('OPENAI_API_KEY')"
    echo ""
    exit 1
fi