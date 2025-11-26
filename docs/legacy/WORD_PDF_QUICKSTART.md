# Word & PDF Support - Quick Start

## TL;DR

```bash
# 1. Install dependencies
source .venv/bin/activate
./INSTALL_WORD_PDF.sh

# 2. Test it works
cd test_word_pdf
python3 -c "from document_parsers import extract_text_from_file; from pathlib import Path; print(extract_text_from_file(Path('test.docx')))"
```

## What You Get

### ✅ Completed
- **document_parsers.py** - Full parsing library for Word/PDF
- **Dependencies added** to pyproject.toml
- **Example tools** in example_word_pdf_tools.py
- **Installation script** - INSTALL_WORD_PDF.sh
- **Full documentation** - WORD_PDF_SUPPORT.md

### 📝 To Do (Integration)
1. Add the example tools to `document_mcp_server.py`
2. Test with real Word/PDF files
3. Update Claude Desktop config
4. Test in MCP Inspector

## Quick Integration

### Step 1: Add Import to document_mcp_server.py

At the top of the file, add:

```python
from document_parsers import (
    extract_text_from_file,
    create_pdf_from_text,
    create_docx_from_text,
    DocumentParseError,
    UnsupportedFormatError
)
```

### Step 2: Add Input Models

Copy these from `example_word_pdf_tools.py`:

```python
class CreateFromFileInput(BaseModel):
    """Input for creating document from file."""
    # ... (see example_word_pdf_tools.py)

class ExportEnhancedInput(BaseModel):
    """Enhanced export input with Word/PDF support."""
    # ... (see example_word_pdf_tools.py)
```

### Step 3: Add Tools

Copy the tool functions from `example_word_pdf_tools.py`:

```python
@mcp.tool(annotations={...})
async def document_create_from_file(params: CreateFromFileInput) -> str:
    # ... implementation

@mcp.tool(annotations={...})
async def document_export_enhanced(params: ExportEnhancedInput) -> str:
    # ... implementation
```

### Step 4: Test

```bash
# Restart your server
python document_mcp_server.py

# Or test in MCP Inspector
npx @modelcontextprotocol/inspector python document_mcp_server.py
```

## Usage Examples

### Import a Word Document

In Claude Desktop or MCP Inspector:

```json
{
  "file_path": "/Users/gmossy/Documents/report.docx",
  "title": "Q4 Financial Report",
  "tags": ["finance", "quarterly", "2024"],
  "status": "draft"
}
```

Tool: `document_create_from_file`

### Import a PDF

```json
{
  "file_path": "/Users/gmossy/Documents/presentation.pdf",
  "tags": ["presentation", "meeting"],
  "extract_metadata": true
}
```

Tool: `document_create_from_file`

### Export to Word

```json
{
  "document_id": "doc_abc123",
  "format": "docx",
  "output_path": "/Users/gmossy/Desktop/exported.docx"
}
```

Tool: `document_export_enhanced`

### Export to PDF

```json
{
  "document_id": "doc_abc123",
  "format": "pdf",
  "output_path": "/Users/gmossy/Desktop/exported.pdf"
}
```

Tool: `document_export_enhanced`

## What Gets Extracted

### From Word (.docx)
- ✅ All text content
- ✅ Paragraph structure
- ✅ Author, title, subject
- ✅ Creation/modification dates
- ✅ Table detection (count)
- ❌ Formatting (bold, italic)
- ❌ Images

### From PDF
- ✅ Text from all pages
- ✅ Page numbers
- ✅ Metadata (author, title, creator)
- ✅ Page count
- ❌ Complex layouts (may be imperfect)
- ❌ Scanned images (needs OCR)

## File Structure

```
claude_document_mcp_server/
├── document_mcp_server.py          # Main server (add tools here)
├── document_parsers.py             # ✅ NEW: Parsing library
├── example_word_pdf_tools.py       # ✅ NEW: Example implementations
├── WORD_PDF_SUPPORT.md             # ✅ NEW: Full documentation
├── WORD_PDF_QUICKSTART.md          # ✅ NEW: This file
├── INSTALL_WORD_PDF.sh             # ✅ NEW: Installation script
├── pyproject.toml                  # ✅ UPDATED: New dependencies
└── test_word_pdf/                  # ✅ NEW: Test files (after install)
    ├── test.docx
    └── test.pdf
```

## Troubleshooting

### "Module not found: docx"
```bash
source .venv/bin/activate
uv sync
```

### "libmagic not found"
```bash
brew install libmagic
```

### "PDF extraction returns empty text"
- PDF may be scanned images (needs OCR)
- PDF may be encrypted
- Try opening PDF manually to verify text is selectable

### "Word document error"
- Ensure file is .docx (not old .doc format)
- File may be corrupted
- Try opening in Word to verify

## Performance Notes

- **Small files** (<1MB): Instant
- **Medium files** (1-10MB): 1-5 seconds
- **Large files** (10-50MB): 5-30 seconds
- **Very large files** (>50MB): Consider adding file size limits

## Security Considerations

Before deploying to production:

1. Add file size limits (e.g., 50MB max)
2. Validate file types before processing
3. Consider virus scanning for uploaded files
4. Sanitize file paths to prevent directory traversal
5. Run parsers in isolated environment if possible

## Next Steps

1. **Install**: Run `./INSTALL_WORD_PDF.sh`
2. **Review**: Check `WORD_PDF_SUPPORT.md` for details
3. **Integrate**: Copy tools from `example_word_pdf_tools.py`
4. **Test**: Try with your own Word/PDF files
5. **Deploy**: Update Claude Desktop config

## Need Help?

- **Full docs**: See `WORD_PDF_SUPPORT.md`
- **Code examples**: See `example_word_pdf_tools.py`
- **Installation**: Run `./INSTALL_WORD_PDF.sh`
- **Testing**: Check `test_word_pdf/` directory after install

## Summary

You now have everything needed to add Word and PDF support to your MCP server:

✅ Parsing library (`document_parsers.py`)
✅ Example implementations (`example_word_pdf_tools.py`)
✅ Installation script (`INSTALL_WORD_PDF.sh`)
✅ Full documentation (`WORD_PDF_SUPPORT.md`)
✅ This quick start guide

Just run the install script and integrate the example tools into your server!
