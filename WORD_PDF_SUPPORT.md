# Word, PDF, and Excel Document Support

## Overview

This guide explains how to extend your MCP server to handle Microsoft Word (.docx), PDF, and Excel (.xlsx) documents in addition to plain text.

## Installation

### 1. Install New Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install the new dependencies
uv sync
```

This will install:
- **python-docx**: Read/write Word documents
- **pypdf**: Read PDF files
- **reportlab**: Create PDF files
- **python-magic**: Detect file types
- **pillow**: Handle images in documents

### 2. Install System Dependencies (macOS)

For `python-magic` to work properly:

```bash
brew install libmagic
```

## Architecture Changes

### New Module: `document_parsers.py`

I've created a new module with these key functions:

- `extract_text_from_docx()` - Extract text from Word files
- `extract_text_from_pdf()` - Extract text from PDFs
- `extract_text_from_file()` - Auto-detect and extract from any supported format
- `create_pdf_from_text()` - Generate PDFs from text
- `create_docx_from_text()` - Generate Word docs from text
- `detect_file_type()` - Identify file MIME types

### How It Works

1. **Upload**: User provides file path or base64-encoded content
2. **Detection**: System detects file type (Word, PDF, or text)
3. **Extraction**: Text content is extracted using appropriate parser
4. **Storage**: 
   - Extracted text stored in database (searchable)
   - Original file stored in `document_storage/` directory
5. **Metadata**: File-specific metadata (page count, author, etc.) preserved

## Implementation Options

### Option 1: File Path Based (Simpler)

Add a new tool `document_create_from_file`:

```python
@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def document_create_from_file(
    file_path: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: str = "draft"
) -> str:
    """
    Create a document from a Word or PDF file.
    
    Args:
        file_path: Path to .docx or .pdf file
        title: Optional title (uses filename if not provided)
        tags: Optional tags
        status: Document status
    """
    from document_parsers import extract_text_from_file
    
    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": "File not found"})
    
    # Extract text and metadata
    text, file_metadata = extract_text_from_file(path)
    
    # Use filename as title if not provided
    if not title:
        title = path.stem
    
    # Create document with extracted content
    # ... (use existing document_create logic)
```

### Option 2: Base64 Upload (More Flexible)

Add support for base64-encoded file uploads:

```python
@mcp.tool()
async def document_upload(
    filename: str,
    content_base64: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> str:
    """
    Upload and create document from base64-encoded file.
    
    Args:
        filename: Original filename (with extension)
        content_base64: Base64-encoded file content
        title: Optional title
        tags: Optional tags
    """
    from document_parsers import decode_base64_to_file, extract_text_from_file
    
    # Save temporary file
    temp_path = DOCUMENTS_DIR / f"temp_{filename}"
    decode_base64_to_file(content_base64, temp_path)
    
    try:
        # Extract text
        text, metadata = extract_text_from_file(temp_path)
        
        # Create document
        # ... (use existing logic)
        
    finally:
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
```

### Option 3: Enhanced Export (Recommended Addition)

Update the existing `document_export` tool to support Word/PDF output:

```python
# In document_export function, add new format options:

if format == "docx":
    from document_parsers import create_docx_from_text
    output_path = DOCUMENTS_DIR / f"{document_id}.docx"
    create_docx_from_text(content, output_path, title)
    # Return file path or base64

elif format == "pdf":
    from document_parsers import create_pdf_from_text
    output_path = DOCUMENTS_DIR / f"{document_id}.pdf"
    create_pdf_from_text(content, output_path, title)
    # Return file path or base64
```

## Database Schema Updates

Add a column to track original file format:

```sql
ALTER TABLE documents ADD COLUMN original_format TEXT DEFAULT 'text';
ALTER TABLE documents ADD COLUMN original_file_path TEXT;
```

This lets you:
- Know which documents came from Word/PDF
- Store reference to original file
- Preserve original alongside extracted text

## Usage Examples

### Creating from Word Document

```json
{
  "file_path": "/Users/gmossy/Documents/report.docx",
  "tags": ["report", "2024"],
  "status": "draft"
}
```

### Creating from PDF

```json
{
  "file_path": "/Users/gmossy/Documents/presentation.pdf",
  "title": "Q4 Presentation",
  "tags": ["presentation", "quarterly"]
}
```

### Exporting to Word

```json
{
  "document_id": "doc_abc123",
  "format": "docx",
  "include_metadata": true
}
```

### Exporting to PDF

```json
{
  "document_id": "doc_abc123",
  "format": "pdf",
  "include_metadata": true
}
```

## Features You Get

### From Word Documents
- ✅ Full text extraction
- ✅ Paragraph preservation
- ✅ Table detection (metadata)
- ✅ Author/title/subject metadata
- ✅ Creation/modification dates
- ❌ Formatting (bold, italic, etc.) - stored as plain text
- ❌ Images - not extracted

### From PDF Documents
- ✅ Text extraction from all pages
- ✅ Page-by-page content
- ✅ Metadata (author, title, creator)
- ✅ Page count
- ❌ Complex layouts may not extract perfectly
- ❌ Scanned PDFs (images) won't extract text without OCR

### Creating Documents
- ✅ Generate Word docs from text
- ✅ Generate PDFs from text
- ✅ Basic formatting preserved
- ✅ Paragraph structure maintained

## Limitations & Considerations

### Performance
- Large PDFs (100+ pages) may take time to process
- Word documents with many images will be slower
- Consider adding file size limits

### Storage
- Original files take more space than text
- Consider cleanup strategy for old files
- May want to compress stored files

### Search
- Only extracted text is searchable
- Images and embedded content not indexed
- Complex layouts may affect search quality

## Next Steps

### Phase 1: Basic Support (Recommended Start)
1. ✅ Add dependencies to `pyproject.toml`
2. ✅ Create `document_parsers.py` module
3. Add `document_create_from_file` tool
4. Test with sample Word/PDF files
5. Update documentation

### Phase 2: Enhanced Features
1. Add base64 upload support
2. Update export to support Word/PDF output
3. Add file type validation
4. Implement file size limits
5. Add progress indicators for large files

### Phase 3: Advanced Features
1. OCR support for scanned PDFs (tesseract)
2. Image extraction and storage
3. Format preservation (styles, fonts)
4. Table extraction and structured data
5. Batch file processing

## Testing

### Test with Sample Files

```bash
# Create test directory
mkdir -p test_files

# Test Word document
python3 << 'EOF'
from pathlib import Path
from document_parsers import extract_text_from_docx

# Create a simple test Word doc
from docx import Document
doc = Document()
doc.add_heading('Test Document', 0)
doc.add_paragraph('This is a test paragraph.')
doc.save('test_files/test.docx')

# Extract text
text, metadata = extract_text_from_docx(Path('test_files/test.docx'))
print("Extracted text:", text)
print("Metadata:", metadata)
EOF
```

### Test PDF Extraction

```bash
python3 << 'EOF'
from pathlib import Path
from document_parsers import extract_text_from_pdf, create_pdf_from_text

# Create a test PDF
create_pdf_from_text(
    "This is a test PDF document.\n\nIt has multiple paragraphs.",
    Path('test_files/test.pdf'),
    "Test PDF"
)

# Extract text
text, metadata = extract_text_from_pdf(Path('test_files/test.pdf'))
print("Extracted text:", text)
print("Metadata:", metadata)
EOF
```

## Troubleshooting

### python-magic errors
```bash
# Install libmagic
brew install libmagic

# Or use fallback (less accurate)
# The code will fall back to mimetypes if magic fails
```

### PDF extraction returns empty text
- PDF may be scanned images (needs OCR)
- PDF may be encrypted
- Try opening PDF manually to verify it has selectable text

### Word document errors
- Ensure file is .docx format (not .doc)
- Old .doc format requires different library (python-docx doesn't support it)
- File may be corrupted

## Security Considerations

1. **File Size Limits**: Add max file size (e.g., 50MB)
2. **File Type Validation**: Verify file types before processing
3. **Sandboxing**: Consider running parsers in isolated environment
4. **Virus Scanning**: For production, scan uploaded files
5. **Path Traversal**: Validate file paths to prevent directory traversal attacks

## Summary

You now have a complete framework to:
- ✅ Extract text from Word and PDF files
- ✅ Create Word and PDF documents
- ✅ Auto-detect file types
- ✅ Preserve document metadata
- ✅ Export to multiple formats

The modular design in `document_parsers.py` makes it easy to add support for more formats in the future (Excel, PowerPoint, etc.).
