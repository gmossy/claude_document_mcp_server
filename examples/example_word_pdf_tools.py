"""
Example implementation of Word/PDF support tools for the MCP server.

This file shows how to add new tools to document_mcp_server.py to support
Word and PDF document uploads and exports.

To integrate these into your server:
1. Copy the tool functions to document_mcp_server.py
2. Import document_parsers at the top
3. Add the tools to your MCP server
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# These would be imported in your main server file
# from document_parsers import (
#     extract_text_from_file,
#     create_pdf_from_text,
#     create_docx_from_text,
#     DocumentParseError,
#     UnsupportedFormatError
# )


class CreateFromFileInput(BaseModel):
    """Input for creating document from file."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    file_path: str = Field(
        ...,
        description="Path to Word (.docx) or PDF (.pdf) file",
        min_length=1,
        max_length=500
    )
    title: Optional[str] = Field(
        None,
        description="Document title (uses filename if not provided)",
        max_length=200
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Tags for categorization",
        max_length=50
    )
    status: str = Field(
        default="draft",
        description="Document status: draft, published, or archived",
        pattern="^(draft|published|archived)$"
    )
    extract_metadata: bool = Field(
        default=True,
        description="Extract and store file metadata (author, dates, etc.)"
    )


class ExportEnhancedInput(BaseModel):
    """Enhanced export input with Word/PDF support."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    document_id: str = Field(
        ...,
        description="Document identifier",
        min_length=1,
        max_length=100
    )
    format: str = Field(
        ...,
        description="Export format: markdown, html, json, txt, docx, or pdf",
        pattern="^(markdown|html|json|txt|docx|pdf)$"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include document metadata in export"
    )
    output_path: Optional[str] = Field(
        None,
        description="Optional output file path (for docx/pdf formats)",
        max_length=500
    )


# ============================================================================
# Tool: Create Document from File
# ============================================================================

async def document_create_from_file(params: CreateFromFileInput) -> str:
    """
    Create a document by importing from Word or PDF file.

    Extracts text content from .docx or .pdf files and creates a searchable
    document in the system. Original file metadata is preserved.

    Supported formats:
    - Microsoft Word (.docx)
    - PDF (.pdf)
    - Plain text (.txt, .md)

    Args:
        params (CreateFromFileInput): Input parameters containing:
            - file_path (str): Path to the file
            - title (str, optional): Document title
            - tags (List[str], optional): Document tags
            - status (str): Document status
            - extract_metadata (bool): Extract file metadata

    Returns:
        str: JSON response with document ID and extraction details

    Example:
        {
            "file_path": "/Users/gmossy/Documents/test-report.docx",
            "title": "Q4 AI Test Engineering Report",
            "tags": ["test-report", "engineering"],
            "status": "draft"
        }
    """
    from document_parsers import extract_text_from_file, DocumentParseError, UnsupportedFormatError

    try:
        file_path = Path(params.file_path).expanduser()

        # Validate file exists
        if not file_path.exists():
            return json.dumps({
                "error": "File not found",
                "message": f"The file '{params.file_path}' does not exist",
                "suggestion": "Check the file path and try again"
            }, indent=2)

        # Extract text and metadata from file
        try:
            extracted_text, file_metadata = extract_text_from_file(file_path)
        except UnsupportedFormatError as e:
            return json.dumps({
                "error": "Unsupported format",
                "message": str(e),
                "suggestion": "Supported formats: .docx, .pdf, .txt, .md"
            }, indent=2)
        except DocumentParseError as e:
            return json.dumps({
                "error": "Parse error",
                "message": str(e),
                "suggestion": "The file may be corrupted or in an unexpected format"
            }, indent=2)

        # Use filename as title if not provided
        title = params.title or file_path.stem

        # Merge file metadata with user metadata if requested
        metadata = {}
        if params.extract_metadata:
            metadata.update(file_metadata)

        # Add original file info
        metadata["original_file"] = str(file_path)
        metadata["original_filename"] = file_path.name

        # Now create the document using existing document_create logic
        # This would call your existing document creation code
        # For this example, we'll show the structure:

        document_id = f"doc_{generate_id()}"  # Your ID generation

        # Store in database with extracted content
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # cursor.execute("""
        #     INSERT INTO documents (id, title, content, tags, status, metadata, ...)
        #     VALUES (?, ?, ?, ?, ?, ?, ...)
        # """, (document_id, title, extracted_text, ...))

        return json.dumps({
            "success": True,
            "document_id": document_id,
            "title": title,
            "extracted_text_length": len(extracted_text),
            "file_format": file_metadata.get("format"),
            "metadata": metadata,
            "message": f"Successfully imported document from {file_path.name}"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": "Unexpected error",
            "message": str(e),
            "suggestion": "Check server logs for details"
        }, indent=2)


# ============================================================================
# Tool: Enhanced Export with Word/PDF Support
# ============================================================================

async def document_export_enhanced(params: ExportEnhancedInput) -> str:
    """
    Export document to various formats including Word and PDF.

    Exports document content to the specified format. For Word and PDF exports,
    generates formatted documents with proper structure.

    Supported formats:
    - markdown: Markdown text
    - html: HTML document
    - json: Structured JSON
    - txt: Plain text
    - docx: Microsoft Word document
    - pdf: PDF document

    Args:
        params (ExportEnhancedInput): Input parameters containing:
            - document_id (str): Document to export
            - format (str): Output format
            - include_metadata (bool): Include metadata
            - output_path (str, optional): Where to save file

    Returns:
        str: Export result with file path or content

    Example:
        {
            "document_id": "doc_abc123",
            "format": "pdf",
            "include_metadata": true,
            "output_path": "/Users/gmossy/Desktop/test-report.pdf"
        }
    """
    from document_parsers import create_pdf_from_text, create_docx_from_text, DocumentParseError

    try:
        # Fetch document from database
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # cursor.execute("SELECT * FROM documents WHERE id = ?", (params.document_id,))
        # row = cursor.fetchone()

        # For this example, assume we have the document data:
        # title = row["title"]
        # content = row["content"]
        # metadata = json.loads(row["metadata"])

        # Placeholder values for example
        title = "Example Document"
        content = "Document content here..."
        metadata = {"author": "User", "created": "2024-01-01"}

        # Handle Word export
        if params.format == "docx":
            output_path = Path(params.output_path) if params.output_path else Path(f"{params.document_id}.docx")

            try:
                create_docx_from_text(content, output_path, title)

                return json.dumps({
                    "success": True,
                    "format": "docx",
                    "output_path": str(output_path),
                    "file_size": output_path.stat().st_size,
                    "message": f"Document exported to Word format: {output_path.name}"
                }, indent=2)

            except DocumentParseError as e:
                return json.dumps({
                    "error": "Export failed",
                    "message": str(e)
                }, indent=2)

        # Handle PDF export
        elif params.format == "pdf":
            output_path = Path(params.output_path) if params.output_path else Path(f"{params.document_id}.pdf")

            try:
                create_pdf_from_text(content, output_path, title)

                return json.dumps({
                    "success": True,
                    "format": "pdf",
                    "output_path": str(output_path),
                    "file_size": output_path.stat().st_size,
                    "message": f"Document exported to PDF format: {output_path.name}"
                }, indent=2)

            except DocumentParseError as e:
                return json.dumps({
                    "error": "Export failed",
                    "message": str(e)
                }, indent=2)

        # For other formats, use existing export logic
        else:
            # Call existing document_export function
            pass

    except Exception as e:
        return json.dumps({
            "error": "Export error",
            "message": str(e)
        }, indent=2)


# ============================================================================
# How to Add These to Your Server
# ============================================================================

"""
To integrate these tools into document_mcp_server.py:

1. Add import at the top of document_mcp_server.py:

   from document_parsers import (
       extract_text_from_file,
       create_pdf_from_text,
       create_docx_from_text,
       DocumentParseError,
       UnsupportedFormatError
   )

2. Add the Pydantic input models (CreateFromFileInput, ExportEnhancedInput)

3. Register the tools with your MCP server:

   @mcp.tool(
       annotations={
           "readOnlyHint": False,
           "destructiveHint": False,
           "idempotentHint": False,
           "openWorldHint": False,
       }
   )
   async def document_create_from_file(params: CreateFromFileInput) -> str:
       # ... implementation from above ...

   @mcp.tool(
       annotations={
           "readOnlyHint": False,
           "destructiveHint": False,
           "idempotentHint": False,
           "openWorldHint": False,
       }
   )
   async def document_export_enhanced(params: ExportEnhancedInput) -> str:
       # ... implementation from above ...

4. Update your existing document_export tool to support docx/pdf formats,
   or replace it with document_export_enhanced

5. Test with:
   - Word documents
   - PDF files
   - Export to Word/PDF

That's it! Your server will now support Word and PDF documents.
"""


# ============================================================================
# Helper Function Example
# ============================================================================

def generate_id() -> str:
    """Generate a unique document ID."""
    import secrets
    return secrets.token_hex(6)
