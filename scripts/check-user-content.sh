#!/bin/bash
# Check that user-generated content is properly gitignored

set -e

echo "🔍 Checking user content isolation..."

# Define user content directories that should NEVER be tracked
USER_DIRS=(
    "user_docs"
    "user_workflows"
    ".conductor"
    "ai_sessions"
    "conversation_memory"
    "generated_docs"
    "ai_generated"
    "output_documents"
)

# Check if any user content directories are tracked by git
VIOLATIONS=0

for dir in "${USER_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        # Check if this directory has any tracked files
        tracked_files=$(git ls-files "$dir/" 2>/dev/null || true)
        if [ -n "$tracked_files" ]; then
            echo "❌ ERROR: User content directory '$dir' contains tracked files:"
            echo "$tracked_files"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "✅ '$dir' is properly ignored"
        fi
    fi
done

# Check for any staged user content
echo "🔍 Checking staged files for user content..."
staged_files=$(git diff --cached --name-only 2>/dev/null || true)

for file in $staged_files; do
    for dir in "${USER_DIRS[@]}"; do
        if [[ "$file" == "$dir"* ]]; then
            echo "❌ ERROR: Attempting to commit user content: $file"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done
done

# Check for secret-like file patterns
echo "🔍 Checking for secret-like files..."
SECRET_PATTERNS=(
    "*.key"
    "*.pem"
    "*.p12"
    "*.pfx"
    "*_rsa"
    "*_dsa"
    "*_ed25519"
    "*_ecdsa"
    "id_*"
    ".env.local"
    ".env.production"
    "secrets.*"
    "*.credentials"
    "*.token"
)

for pattern in "${SECRET_PATTERNS[@]}"; do
    files=$(git ls-files "$pattern" 2>/dev/null || true)
    if [ -n "$files" ]; then
        echo "⚠️  WARNING: Found potential secret files:"
        echo "$files"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ All user content is properly isolated!"
    exit 0
else
    echo ""
    echo "❌ Found $VIOLATIONS violations. User content must not be committed!"
    echo ""
    echo "💡 To fix:"
    echo "   1. Remove user content from git: git rm -r --cached <directory>"
    echo "   2. Add to .gitignore if not already present"
    echo "   3. Ensure only project code is committed"
    exit 1
fi
