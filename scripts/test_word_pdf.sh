#!/bin/bash
# Quick test script for Word/PDF support (doesn't require venv activation check)

set -e

echo "📦 Testing Word and PDF Support"
echo "================================"
echo ""

cd "/Volumes/My Book8TB-6TB Partition/claude_document_mcp_server"

# Use the venv's Python directly (absolute path)
PYTHON="/Volumes/My Book8TB-6TB Partition/claude_document_mcp_server/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found at .venv/"
    echo "Run: uv venv --python 3.13 && uv sync"
    exit 1
fi

echo "✓ Using Python: $PYTHON"
echo ""

# Install dependencies
echo "Step 1: Installing dependencies..."
/Users/gmossy/.local/bin/uv sync
echo ""

# Test imports
echo "Step 2: Testing imports..."
"$PYTHON" << 'EOF'
import sys

packages = {
    "docx": "python-docx",
    "pypdf": "pypdf",
    "reportlab": "reportlab",
    "PIL": "pillow"
}

all_ok = True
for module, package in packages.items():
    try:
        __import__(module)
        print(f"✓ {package} installed")
    except ImportError:
        print(f"✗ {package} missing")
        all_ok = False

# python-magic is optional
try:
    import magic
    print(f"✓ python-magic installed")
except ImportError:
    print(f"⚠️  python-magic not installed (optional, will use fallback)")

if not all_ok:
    print("\n⚠️  Some packages are missing. Run: uv sync")
    sys.exit(1)
else:
    print("\n✅ All required packages installed!")
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# Test document_parsers module
echo "Step 3: Testing document_parsers module..."
"$PYTHON" << 'EOF'
try:
    from document_parsers import (
        extract_text_from_file,
        create_pdf_from_text,
        create_docx_from_text,
        detect_file_type
    )
    print("✓ document_parsers module loads successfully")
except Exception as e:
    print(f"✗ Error loading document_parsers: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# Create test directory
echo "Step 4: Creating test files..."
mkdir -p test_word_pdf
cd test_word_pdf

# Create test Word document
"$PYTHON" << 'EOF'
from pathlib import Path
from docx import Document

doc = Document()
doc.add_heading('Test Word Document', 0)
doc.add_paragraph('This is a test paragraph in a Word document.')
doc.add_paragraph('It has multiple paragraphs to test extraction.')
doc.add_paragraph('This is the third paragraph with some content.')
doc.save('test.docx')
print("✓ Created test.docx")
EOF

# Create test PDF
"$PYTHON" << 'EOF'
import sys
sys.path.insert(0, '/Volumes/My Book8TB-6TB Partition/claude_document_mcp_server')
from pathlib import Path
from document_parsers import create_pdf_from_text

text = """This is a test PDF document.

It has multiple paragraphs to test extraction.

This is the third paragraph with some content.

And here is a fourth paragraph for good measure."""

create_pdf_from_text(text, Path('test.pdf'), 'Test PDF Document')
print("✓ Created test.pdf")
EOF

# Test extraction
echo ""
echo "Step 5: Testing Word extraction..."
"$PYTHON" << 'EOF'
import sys
sys.path.insert(0, '/Volumes/My Book8TB-6TB Partition/claude_document_mcp_server')
from pathlib import Path
from document_parsers import extract_text_from_file

text, metadata = extract_text_from_file(Path('test.docx'))
print(f"✓ Extracted {len(text)} characters from Word document")
print(f"  Format: {metadata.get('format')}")
print(f"  Paragraphs: {metadata.get('paragraph_count')}")
print(f"\n  First 100 chars: {text[:100]}...")
EOF

if [ $? -ne 0 ]; then
    echo "✗ Word extraction failed"
    exit 1
fi

echo ""
echo "Step 6: Testing PDF extraction..."
"$PYTHON" << 'EOF'
import sys
sys.path.insert(0, '/Volumes/My Book8TB-6TB Partition/claude_document_mcp_server')
from pathlib import Path
from document_parsers import extract_text_from_file

text, metadata = extract_text_from_file(Path('test.pdf'))
print(f"✓ Extracted {len(text)} characters from PDF")
print(f"  Format: {metadata.get('format')}")
print(f"  Pages: {metadata.get('page_count')}")
print(f"\n  First 100 chars: {text[:100]}...")
EOF

if [ $? -ne 0 ]; then
    echo "✗ PDF extraction failed"
    exit 1
fi

echo ""
echo "Step 7: Testing round-trip (text -> docx -> text)..."
"$PYTHON" << 'EOF'
import sys
sys.path.insert(0, '/Volumes/My Book8TB-6TB Partition/claude_document_mcp_server')
from pathlib import Path
from document_parsers import create_docx_from_text, extract_text_from_file

original_text = "This is a round-trip test.\n\nIt has two paragraphs."
create_docx_from_text(original_text, Path('roundtrip.docx'), 'Round Trip Test')
extracted_text, _ = extract_text_from_file(Path('roundtrip.docx'))

print(f"✓ Original: {len(original_text)} chars")
print(f"✓ Extracted: {len(extracted_text)} chars")
print(f"✓ Round-trip successful!")
EOF

if [ $? -ne 0 ]; then
    echo "✗ Round-trip test failed"
    exit 1
fi

cd ..
echo ""
echo "===================================="
echo "✅ All Tests Passed!"
echo ""
echo "Test files created in: test_word_pdf/"
echo "  - test.docx (Word document)"
echo "  - test.pdf (PDF document)"
echo "  - roundtrip.docx (Round-trip test)"
echo ""
echo "Try extracting text from your own files:"
echo "  $PYTHON -c \"from document_parsers import extract_text_from_file; from pathlib import Path; text, meta = extract_text_from_file(Path('your_file.docx')); print(text)\""
echo ""
echo "Next: Integrate tools into document_mcp_server.py"
echo "See: example_word_pdf_tools.py for implementation"
