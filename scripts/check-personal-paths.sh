#!/bin/bash
# Check for hardcoded personal data paths in Python code

set -e

echo "👤 Checking for hardcoded personal data paths..."

# Patterns that suggest hardcoded user-specific paths
PERSONAL_PATH_PATTERNS=(
    # Hardcoded user directories that should be configurable (but NOT in already fixed code)
    "Path\(['\"]docs['\"]"
    "Path\(['\"]logs['\"]"
    "Path\(['\"]output['\"]"

    # Absolute hardcoded personal paths (CRITICAL)
    "/Users/[a-zA-Z0-9_-]+/"
    "/home/[a-zA-Z0-9_-]+/"
    "C:\\\\Users\\\\[a-zA-Z0-9_-]+\\\\"

    # Common personal directory names hardcoded
    "['\"]Documents[/\\\\]"
    "['\"]Desktop[/\\\\]"
    "['\"]Downloads[/\\\\]"

    # Database paths with absolute personal paths
    "['\"][~/][^'\"]*\\.db['\"]"
    "['\"][~/][^'\"]*\\.sqlite['\"]"
)

VIOLATIONS=0
WARNINGS=0

# Function to scan a file
scan_file() {
    local file="$1"
    local found_issues=0

    for pattern in "${PERSONAL_PATH_PATTERNS[@]}"; do
        matches=$(grep -inE "$pattern" "$file" 2>/dev/null || true)
        if [ -n "$matches" ]; then
            if [ $found_issues -eq 0 ]; then
                echo ""
                echo "⚠️  PERSONAL PATHS in $file:"
                found_issues=1
            fi

            # Check if this is a critical violation or just a warning
            if [[ "$pattern" == *"Users/"* ]] || [[ "$pattern" == *"home/"* ]] || [[ "$pattern" == *"~/"* ]]; then
                echo "   🚨 CRITICAL Line $(echo "$matches" | cut -d: -f1): $(echo "$matches" | cut -d: -f2-)"
                VIOLATIONS=$((VIOLATIONS + 1))
            else
                echo "   ⚠️  WARNING Line $(echo "$matches" | cut -d: -f1): $(echo "$matches" | cut -d: -f2-)"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    done
}

# Scan Python files
echo "📁 Scanning Python files for personal paths..."

FILES=$(find . -name "*.py" \
    ! -path "./venv/*" \
    ! -path "./.venv/*" \
    ! -path "./user_docs/*" \
    ! -path "./user_workflows/*" \
    ! -path "./.conductor/*" \
    ! -path "./.git/*" \
    ! -path "./tests/*" \
    ! -path "./test_*")

TOTAL_FILES=0
for file in $FILES; do
    TOTAL_FILES=$((TOTAL_FILES + 1))
    scan_file "$file"
done

echo ""
echo "📊 Scan Results:"
echo "   Files scanned: $TOTAL_FILES"
echo "   Critical violations: $VIOLATIONS"
echo "   Warnings: $WARNINGS"

if [ $VIOLATIONS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ No personal data paths detected!"
    exit 0
elif [ $VIOLATIONS -eq 0 ]; then
    echo "⚠️  Found $WARNINGS potential issues (warnings only)"
    echo ""
    echo "💡 Consider reviewing these patterns to ensure they're appropriate"
    exit 0
else
    echo ""
    echo "❌ Found $VIOLATIONS critical personal path violations!"
    echo ""
    echo "💡 To fix personal path issues:"
    echo "   1. Use relative paths: Path('user_docs') instead of Path('/Users/john/docs')"
    echo "   2. Make paths configurable: Path(config.get('docs_dir', 'user_docs'))"
    echo "   3. Use environment variables: Path(os.getenv('CONDUCTOR_DOCS', 'user_docs'))"
    echo "   4. Avoid hardcoded home directory paths"
    echo ""
    echo "Good patterns:"
    echo "   ✅ Path('user_docs')  # Relative to project"
    echo "   ✅ Path('.conductor') # Hidden, relative"
    echo "   ✅ os.getenv('HOME') / '.conductor'  # Programmatic home detection"
    echo ""
    echo "Bad patterns:"
    echo "   ❌ Path('/Users/john/conductor')  # Hardcoded user"
    echo "   ❌ Path('~/conductor')  # Shell expansion needed"
    echo "   ❌ Path('C:\\Users\\John\\Documents')  # Windows specific + personal"
    echo ""
    exit 1
fi