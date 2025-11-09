#!/bin/bash

echo "🔍 Running pre-commit architecture validation..."

# Check for dashboard imports in core
VIOLATIONS=$(grep -r "from.*dashboard\|import.*dashboard" src/orchestrator/ 2>/dev/null)

if [ -n "$VIOLATIONS" ]; then
    echo "❌ ARCHITECTURE VIOLATION DETECTED!"
    echo ""
    echo "Core orchestrator must not import from dashboard:"
    echo "$VIOLATIONS"
    echo ""
    echo "Please remove these imports. Core must remain integration-agnostic."
    echo ""
    echo "Blocking commit. Fix violations and try again."
    exit 1
fi

# Check for hardcoded database paths
DB_PATHS=$(grep -r "orchestrator\.db" src/orchestrator/ 2>/dev/null | grep -v "test\|example")

if [ -n "$DB_PATHS" ]; then
    echo "⚠️  WARNING: Hardcoded database paths detected:"
    echo "$DB_PATHS"
    echo ""
    echo "Consider using environment variables for database paths."
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for secrets
SECRETS=$(grep -ri "api[_-]key\|secret\|password.*=" src/ dashboard/ --include="*.py" --include="*.ts" | grep -v "\.env\|config\.py\|settings")

if [ -n "$SECRETS" ]; then
    echo "🔐 WARNING: Potential secrets detected:"
    echo "$SECRETS"
    echo ""
    read -p "These look like secrets. Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Architecture validation passed!"
exit 0
