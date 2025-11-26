#!/bin/bash
# Quick test script for Document MCP Server

echo "🧪 Testing Document MCP Server"
echo "================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Run: source .venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment active: $VIRTUAL_ENV"
echo ""

# Test 1: Syntax check
echo "Test 1: Checking Python syntax..."
if python -m py_compile document_mcp_server.py 2>/dev/null; then
    echo "✓ Syntax check passed"
else
    echo "✗ Syntax check failed"
    exit 1
fi
echo ""

# Test 2: Import check
echo "Test 2: Checking imports..."
if python -c "import document_mcp_server" 2>/dev/null; then
    echo "✓ Module imports successfully"
else
    echo "✗ Import failed"
    exit 1
fi
echo ""

# Test 3: Check dependencies
echo "Test 3: Checking dependencies..."
MISSING=0
for pkg in mcp pydantic httpx; do
    if python -c "import $pkg" 2>/dev/null; then
        echo "✓ $pkg installed"
    else
        echo "✗ $pkg missing"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "Run: uv sync"
    exit 1
fi
echo ""

echo "================================"
echo "✅ All checks passed!"
echo ""
echo "To test interactively, run:"
echo "  npx @modelcontextprotocol/inspector python document_mcp_server.py"
echo ""
echo "Or to run the server:"
echo "  python document_mcp_server.py"
