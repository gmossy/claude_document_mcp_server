#!/bin/bash
# Installation script for Word/PDF support

set -e  # Exit on error

echo "📦 Installing Word and PDF Support"
echo "===================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Run: source .venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment active: $VIRTUAL_ENV"
echo ""

# Install system dependencies (macOS)
echo "Step 1: Installing system dependencies..."
if command -v brew &> /dev/null; then
    echo "Installing libmagic via Homebrew..."
    brew install libmagic || echo "⚠️  libmagic may already be installed"
else
    echo "⚠️  Homebrew not found. Install manually: brew install libmagic"
fi
echo ""

# Install Python dependencies
echo "Step 2: Installing Python packages..."
uv sync
echo ""

# Test imports
echo "Step 3: Testing imports..."
python3 << 'EOF'
import sys

packages = {
    "docx": "python-docx",
    "pypdf": "pypdf",
    "reportlab": "reportlab",
    "magic": "python-magic",
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

if not all_ok:
    print("\n⚠️  Some packages are missing. Run: uv sync")
    sys.exit(1)
else:
    print("\n✅ All packages installed successfully!")
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# Test document_parsers module
echo "Step 4: Testing document_parsers module..."
python3 << 'EOF'
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
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# Create test directory
echo "Step 5: Creating test files..."
mkdir -p test_word_pdf
cd test_word_pdf

# Create test Word document
python3 << 'EOF'
from pathlib import Path
from docx import Document

doc = Document()
doc.add_heading('Test Word Document', 0)
doc.add_paragraph('This is a test paragraph in a Word document.')
doc.add_paragraph('It has multiple paragraphs to test extraction.')
doc.save('test.docx')
print("✓ Created test.docx")
EOF

# Create test PDF
python3 << 'EOF'
from pathlib import Path
from document_parsers import create_pdf_from_text

text = """This is a test PDF document.

It has multiple paragraphs to test extraction.

This is the third paragraph."""

create_pdf_from_text(text, Path('test.pdf'), 'Test PDF Document')
print("✓ Created test.pdf")
EOF

# Test extraction
echo ""
echo "Step 6: Testing extraction..."
python3 << 'EOF'
from pathlib import Path
from document_parsers import extract_text_from_file

# Test Word extraction
print("\nTesting Word extraction:")
text, metadata = extract_text_from_file(Path('test.docx'))
print(f"  Extracted {len(text)} characters")
print(f"  Format: {metadata.get('format')}")
print(f"  Paragraphs: {metadata.get('paragraph_count')}")

# Test PDF extraction
print("\nTesting PDF extraction:")
text, metadata = extract_text_from_file(Path('test.pdf'))
print(f"  Extracted {len(text)} characters")
print(f"  Format: {metadata.get('format')}")
print(f"  Pages: {metadata.get('page_count')}")

print("\n✓ Extraction tests passed!")
EOF

if [ $? -ne 0 ]; then
    echo "✗ Extraction tests failed"
    exit 1
fi

cd ..
echo ""
echo "===================================="
echo "✅ Installation Complete!"
echo ""
echo "Test files created in: test_word_pdf/"
echo ""
echo "Next steps:"
echo "1. Review WORD_PDF_SUPPORT.md for implementation guide"
echo "2. Check example_word_pdf_tools.py for code examples"
echo "3. Integrate the tools into document_mcp_server.py"
echo ""
echo "To test with your own files:"
echo "  python3 -c \"from document_parsers import extract_text_from_file; print(extract_text_from_file(Path('your_file.docx')))\""
