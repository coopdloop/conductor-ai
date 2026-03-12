#!/bin/bash
# Test that .gitignore effectively protects user content

set -e

echo "🧪 Testing .gitignore effectiveness..."

# Create temporary test files in user content directories
TEST_FILES=(
    "user_docs/test_secret_doc.md"
    "user_workflows/test_workflow.md"
    ".conductor/test_memory.json"
    ".conductor/memory/test_conversation.db"
    ".conductor/context/test_context.json"
)

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up test files..."
    for file in "${TEST_FILES[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
        fi
    done

    # Remove empty directories
    for dir in "user_docs" "user_workflows" ".conductor/memory" ".conductor/context" ".conductor"; do
        if [ -d "$dir" ] && [ -z "$(ls -A "$dir" 2>/dev/null)" ]; then
            rmdir "$dir" 2>/dev/null || true
        fi
    done
}

# Set trap for cleanup on script exit
trap cleanup EXIT

# Create test directories if they don't exist
for file in "${TEST_FILES[@]}"; do
    dir=$(dirname "$file")
    mkdir -p "$dir"
done

echo "📝 Creating test files with sensitive content..."

# Create test files with fake sensitive content
cat > "user_docs/test_secret_doc.md" << EOF
# Secret Document
This contains sensitive user information that should NEVER be committed:
- API Key: sk-test123456789
- Password: mySecretPassword123
- Personal workflow details
EOF

cat > "user_workflows/test_workflow.md" << EOF
# Personal Workflow
Contains personal work context that should be private:
- Meeting with John about confidential project X
- Personal TODO items
- Internal company information
EOF

cat > ".conductor/test_memory.json" << EOF
{
  "conversation_id": "test",
  "user_data": {
    "api_keys": ["sk-fake123"],
    "personal_context": "sensitive work information"
  }
}
EOF

cat > ".conductor/memory/test_conversation.db" << EOF
FAKE_DATABASE_WITH_PERSONAL_DATA
EOF

cat > ".conductor/context/test_context.json" << EOF
{
  "user_context": "personal work patterns",
  "projects": ["secret-project-alpha", "internal-tool-beta"]
}
EOF

echo "🔍 Testing if git detects these files..."

# Check if any test files show up in git status
DETECTED_FILES=$(git status --porcelain 2>/dev/null | grep -E "(user_docs|user_workflows|\.conductor)" || true)

if [ -n "$DETECTED_FILES" ]; then
    echo "❌ CRITICAL: Git detected user content files!"
    echo "Files that would be committed:"
    echo "$DETECTED_FILES"
    echo ""
    echo "💥 .gitignore is NOT working properly!"
    echo "🔧 Fix needed: Update .gitignore to properly exclude user content"
    exit 1
fi

# Test staging - try to add user files explicitly
echo "🧪 Testing explicit git add protection..."
STAGE_ERRORS=0

for file in "${TEST_FILES[@]}"; do
    if git add "$file" 2>/dev/null; then
        echo "❌ ERROR: Was able to stage user file: $file"
        git reset HEAD "$file" 2>/dev/null || true
        STAGE_ERRORS=$((STAGE_ERRORS + 1))
    fi
done

if [ $STAGE_ERRORS -gt 0 ]; then
    echo "❌ CRITICAL: Some user files can be staged!"
    echo "🔧 Fix needed: Update .gitignore patterns"
    exit 1
fi

# Test that project files are still trackable
echo "🧪 Testing that project files are still trackable..."
echo "# Test project file" > test_project_file.py
if ! git add test_project_file.py 2>/dev/null; then
    echo "❌ ERROR: Cannot stage legitimate project files"
    rm -f test_project_file.py
    exit 1
fi

# Clean up test project file
git reset HEAD test_project_file.py 2>/dev/null || true
rm -f test_project_file.py

echo "✅ .gitignore is working correctly!"
echo "   ✓ User content directories are ignored"
echo "   ✓ Sensitive files cannot be staged"
echo "   ✓ Project files can still be tracked"
echo "   ✓ Privacy protection is effective"

exit 0