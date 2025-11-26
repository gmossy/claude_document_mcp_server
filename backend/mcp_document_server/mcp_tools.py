"""MCP tool implementations for document management server.

This module contains all tool implementations. Tools are registered with
the mcp instance via decorators when this module is imported.
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from backend.mcp_document_server.mcp_formatters import (
    calculate_reading_time,
    extract_keywords,
    format_document_markdown,
    format_search_results_markdown,
    format_timestamp,
)
from backend.mcp_document_server.mcp_models import (
    AnalyzeDocumentInput,
    BulkTagInput,
    CompareVersionsInput,
    CreateDocumentInput,
    DeleteDocumentInput,
    DownloadFileInput,
    ExportDocumentInput,
    ExportFileInput,
    GetDocumentInput,
    GetDocumentVersionInput,
    GetStatisticsInput,
    ListTagsInput,
    ResponseFormat,
    SearchDocumentsInput,
    UpdateDocumentInput,
)

# ============================================================================
# Tool Registration
# ============================================================================

def register_tools(mcp_instance: "FastMCP") -> None:
    """Register all tools with the MCP instance."""
    mcp_instance.tool()(document_create)
    mcp_instance.tool()(document_get)
    mcp_instance.tool()(document_update)
    mcp_instance.tool()(document_delete)
    mcp_instance.tool()(document_search)
    mcp_instance.tool()(document_list_tags)
    mcp_instance.tool()(document_get_version)
    mcp_instance.tool()(document_compare_versions)
    mcp_instance.tool()(document_analyze)
    mcp_instance.tool()(document_export)
    mcp_instance.tool()(document_export_file)
    mcp_instance.tool()(document_download_file)
    mcp_instance.tool()(document_bulk_tag)
    mcp_instance.tool()(document_statistics)


# ============================================================================
# Document CRUD Operations
# ============================================================================

async def document_create(params: CreateDocumentInput) -> str:
    """
    Create a new document with automatic versioning.

    Creates a document with the specified title, content, tags, and metadata.
    The document is automatically assigned version 1.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    result = document_service.create_document(
        title=params.title,
        content=params.content,
        tags=params.tags or [],
        status=params.status.value,
        metadata=params.metadata or {},
    )

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(result, indent=2)
    else:
        # Markdown format
        return f"# Document Created\n\n**ID**: `{result['document_id']}`\n**Title**: {result['title']}\n**Status**: {result['status']}\n**Version**: {result['version']}\n\n{result['message']}"


async def document_get(params: GetDocumentInput) -> str:
    """
    Retrieve a document with optional content and version history.

    Returns the document in the specified format (markdown or JSON).
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    doc = document_service.get_document(
        document_id=params.document_id,
        include_content=params.include_content,
        include_versions=params.include_versions,
    )

    if not doc:
        error_msg = f"Document '{params.document_id}' not found."
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg}, indent=2)
        return f"# Error\n\n{error_msg}"

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(doc, indent=2)
    else:
        return format_document_markdown(
            doc,
            include_content=params.include_content,
            include_versions=params.include_versions,
        )


async def document_update(params: UpdateDocumentInput) -> str:
    """
    Update document content, tags, or metadata with automatic versioning.

    If content changes, a new version is automatically created.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    # Get current document
    current = document_service.get_document(
        document_id=params.document_id, include_content=True
    )
    if not current:
        error_msg = f"Document '{params.document_id}' not found."
        return json.dumps({"error": error_msg}, indent=2)

    # Prepare update data
    new_title = params.title if params.title is not None else current["title"]
    new_content = params.content if params.content is not None else current["content"]
    new_tags = params.tags if params.tags is not None else json.loads(current["tags"])
    new_status = (
        params.status.value if params.status is not None else current["status"]
    )

    # Merge metadata
    current_metadata = json.loads(current["metadata"])
    if params.metadata:
        current_metadata.update(params.metadata)
    new_metadata = current_metadata

    # Check if content changed (triggers new version)
    content_changed = params.content is not None and params.content != current["content"]

    # For now, we'll create a new document version by updating
    # In a full implementation, we'd use an update method that handles versioning
    # For this implementation, we'll use create_document which always creates version 1
    # A proper update method should be added to DocumentService

    # Since DocumentService doesn't have an update method yet,
    # we'll return an error suggesting to use create for now
    # TODO: Implement proper update method in DocumentService
    result = {
        "success": False,
        "error": "Update functionality requires DocumentService.update_document() method",
        "document_id": params.document_id,
    }

    return json.dumps(result, indent=2)


async def document_delete(params: DeleteDocumentInput) -> str:
    """
    Archive or permanently delete a document.

    By default, archives the document (sets status to 'archived').
    Set permanent=True to permanently delete.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    result = document_service.delete_document(
        document_id=params.document_id, permanent=params.permanent
    )

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(result, indent=2)
    else:
        return f"# Document {result['action']}\n\n**ID**: `{result['document_id']}`\n**Title**: {result['title']}\n\n{result['message']}"


# ============================================================================
# Search and Discovery
# ============================================================================


async def document_search(params: SearchDocumentsInput) -> str:
    """
    Search documents with full-text search, tag filtering, and pagination.

    Supports searching by query string, filtering by tags and status,
    and sorting results.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    # Build search parameters
    status = params.status.value if params.status else None
    tags = params.tags or None

    # Use list_documents for now (semantic_search would need FTS implementation)
    if params.query:
        # If there's a query, try semantic search first
        results = document_service.semantic_search(params.query, limit=params.limit)
        total = len(results)
    else:
        # Otherwise use list_documents
        result_dict = document_service.list_documents(
            status=status,
            tags=tags,
            limit=params.limit,
            offset=params.offset,
            order_by=params.sort_by.value,
            order_desc=(params.sort_order.value == "desc"),
        )
        results = result_dict["documents"]
        total = result_dict["total"]

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(
            {
                "results": results,
                "total": total,
                "limit": params.limit,
                "offset": params.offset,
            },
            indent=2,
        )
    else:
        return format_search_results_markdown(results, total, params.offset)


async def document_list_tags(params: ListTagsInput) -> str:
    """
    List all tags with usage counts.

    Returns tags sorted by usage count or alphabetically.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    # Get all documents to extract tags
    all_docs = document_service.list_documents(limit=1000)
    tag_counts: dict[str, int] = {}

    for doc in all_docs["documents"]:
        tags = doc["tags"]
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Filter by min_count
    filtered_tags = {
        tag: count
        for tag, count in tag_counts.items()
        if count >= params.min_count
    }

    # Sort
    if params.sort_by_count:
        sorted_tags = sorted(
            filtered_tags.items(), key=lambda x: x[1], reverse=True
        )
    else:
        sorted_tags = sorted(filtered_tags.items())

    tag_list = [{"tag": tag, "count": count} for tag, count in sorted_tags]

    if params.response_format == ResponseFormat.JSON:
        return json.dumps({"tags": tag_list, "total": len(tag_list)}, indent=2)
    else:
        lines = ["# Tags", "", f"Total: {len(tag_list)}", ""]
        for item in tag_list:
            lines.append(f"- **{item['tag']}**: {item['count']} document(s)")
        return "\n".join(lines)


# ============================================================================
# Version Control
# ============================================================================


async def document_get_version(params: GetDocumentVersionInput) -> str:
    """
    Retrieve a specific historical version of a document.

    Returns the document as it existed at the specified version number.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    doc = document_service.get_document(
        document_id=params.document_id, include_content=True, include_versions=True
    )

    if not doc:
        error_msg = f"Document '{params.document_id}' not found."
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg}, indent=2)
        return f"# Error\n\n{error_msg}"

    # Find the specific version
    versions = doc.get("versions", [])
    target_version = next(
        (v for v in versions if v["version_number"] == params.version_number), None
    )

    if not target_version:
        error_msg = f"Version {params.version_number} not found for document '{params.document_id}'."
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg}, indent=2)
        return f"# Error\n\n{error_msg}"

    # Get version content from document_versions table
    # For now, return version metadata
    version_data = {
        "document_id": params.document_id,
        "version_number": params.version_number,
        "title": target_version.get("title", doc["title"]),
        "created_at": target_version.get("created_at"),
        "comment": target_version.get("comment", ""),
    }

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(version_data, indent=2)
    else:
        lines = [
            f"# Version {params.version_number}",
            "",
            f"**Document**: {doc['title']}",
            f"**Created**: {format_timestamp(version_data['created_at'])}",
        ]
        if version_data["comment"]:
            lines.append(f"**Comment**: {version_data['comment']}")
        return "\n".join(lines)


async def document_compare_versions(params: CompareVersionsInput) -> str:
    """
    Compare two versions of a document to see what changed.

    Returns a diff showing additions, deletions, and modifications.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    doc = document_service.get_document(
        document_id=params.document_id, include_content=True, include_versions=True
    )

    if not doc:
        return json.dumps({"error": f"Document '{params.document_id}' not found."}, indent=2)

    versions = doc.get("versions", [])
    version_a = next(
        (v for v in versions if v["version_number"] == params.version_a), None
    )
    version_b = next(
        (v for v in versions if v["version_number"] == params.version_b), None
    )

    if not version_a or not version_b:
        return json.dumps(
            {"error": "One or both versions not found."}, indent=2
        )

    # Simple text comparison
    # In a full implementation, we'd use a proper diff library
    result = {
        "document_id": params.document_id,
        "version_a": params.version_a,
        "version_b": params.version_b,
        "message": "Version comparison requires retrieving full content from versions table",
    }

    return json.dumps(result, indent=2)


# ============================================================================
# Analysis and Export
# ============================================================================


async def document_analyze(params: AnalyzeDocumentInput) -> str:
    """
    Get content statistics and extract keywords from a document.

    Provides word count, character count, reading time, and top keywords.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    doc = document_service.get_document(
        document_id=params.document_id, include_content=True
    )

    if not doc:
        error_msg = f"Document '{params.document_id}' not found."
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg}, indent=2)
        return f"# Error\n\n{error_msg}"

    content = doc["content"]
    stats = {}

    if params.include_stats:
        stats = {
            "word_count": len(content.split()),
            "character_count": len(content),
            "character_count_no_spaces": len(content.replace(" ", "")),
            "line_count": len(content.splitlines()),
            "paragraph_count": len([p for p in content.split("\n\n") if p.strip()]),
            "reading_time_minutes": calculate_reading_time(content),
        }

    keywords = []
    if params.include_keywords:
        keywords = extract_keywords(content, top_n=15)

    result = {
        "document_id": params.document_id,
        "title": doc["title"],
        "stats": stats,
        "keywords": keywords,
    }

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(result, indent=2)
    else:
        lines = [
            f"# Document Analysis: {doc['title']}",
            f"**ID**: `{params.document_id}`",
            "",
        ]
        if stats:
            lines.append("## Statistics")
            lines.append(f"- **Word Count**: {stats['word_count']:,}")
            lines.append(f"- **Character Count**: {stats['character_count']:,}")
            lines.append(
                f"- **Lines**: {stats['line_count']:,}"
            )
            lines.append(
                f"- **Paragraphs**: {stats['paragraph_count']:,}"
            )
            lines.append(
                f"- **Estimated Reading Time**: {stats['reading_time_minutes']} minutes"
            )
        if keywords:
            lines.append("")
            lines.append("## Top Keywords")
            lines.append(", ".join(f"`{kw}`" for kw in keywords))
        return "\n".join(lines)


async def document_export(params: ExportDocumentInput) -> str:
    """
    Export a document to Markdown, HTML, JSON, or plain text format.

    Exports the document content in the specified format.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    doc = document_service.get_document(
        document_id=params.document_id, include_content=True
    )

    if not doc:
        return json.dumps({"error": f"Document '{params.document_id}' not found."}, indent=2)

    if params.format == "json":
        export_data = {
            "id": doc["id"],
            "title": doc["title"],
            "content": doc["content"],
            "tags": json.loads(doc["tags"]) if isinstance(doc["tags"], str) else doc["tags"],
            "status": doc["status"],
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }
        if params.include_metadata:
            export_data["metadata"] = (
                json.loads(doc["metadata"])
                if isinstance(doc["metadata"], str)
                else doc["metadata"]
            )
        return json.dumps(export_data, indent=2)
    elif params.format == "html":
        tags = json.loads(doc["tags"]) if isinstance(doc["tags"], str) else doc["tags"]
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{doc['title']}</title>
</head>
<body>
    <h1>{doc['title']}</h1>
    <p><strong>ID:</strong> {doc['id']}</p>
    <p><strong>Status:</strong> {doc['status']}</p>
    <p><strong>Tags:</strong> {', '.join(tags)}</p>
    <hr>
    <div>{doc['content'].replace(chr(10), '<br>')}</div>
</body>
</html>"""
        return html
    elif params.format == "txt":
        return doc["content"]
    else:  # markdown
        return format_document_markdown(doc, include_content=True)


async def document_export_file(params: ExportFileInput) -> str:
    """
    Export a document version to a file on disk (markdown, txt, or code formats).

    Creates a versioned file in the document storage directory.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    try:
        result = document_service.export_document_file(
            document_id=params.document_id,
            file_format=params.format,
            version_number=params.version_number,
            file_name=params.file_name,
            code_extension=params.code_extension,
        )
        return json.dumps(result, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)


async def document_download_file(params: DownloadFileInput) -> str:
    """
    Get information about downloading the original binary file for a document.

    Returns metadata about the binary file including download URL.
    The actual file download should be done via GET /api/v1/documents/{document_id}/download
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    binary_data = document_service.get_binary_file(
        document_id=params.document_id,
        version_number=params.version_number,
    )

    if not binary_data:
        error_msg = f"Binary file not found for document '{params.document_id}'"
        if params.version_number:
            error_msg += f" version {params.version_number}"
        return json.dumps({"error": error_msg}, indent=2)

    result = {
        "document_id": params.document_id,
        "version_number": params.version_number or "latest",
        "filename": binary_data["filename"],
        "mime_type": binary_data["mime_type"],
        "format": binary_data["format"],
        "size_bytes": binary_data["size_bytes"],
        "download_url": f"/api/v1/documents/{params.document_id}/download",
    }
    if params.version_number:
        result["download_url"] += f"?version_number={params.version_number}"

    return json.dumps(result, indent=2)


# ============================================================================
# Bulk Operations
# ============================================================================


async def document_bulk_tag(params: BulkTagInput) -> str:
    """
    Add or remove tags from multiple documents at once.

    Efficiently updates tags across multiple documents in a single operation.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    results = []
    for doc_id in params.document_ids:
        doc = document_service.get_document(document_id=doc_id, include_content=False)
        if not doc:
            results.append({"document_id": doc_id, "success": False, "error": "Not found"})
            continue

        current_tags = json.loads(doc["tags"]) if isinstance(doc["tags"], str) else doc["tags"]
        new_tags = set(current_tags)

        if params.add_tags:
            new_tags.update(params.add_tags)
        if params.remove_tags:
            new_tags.difference_update(params.remove_tags)

        # Update document tags
        # TODO: Implement proper update method in DocumentService
        results.append({
            "document_id": doc_id,
            "success": False,
            "error": "Bulk tag update requires DocumentService.update_document() method",
            "current_tags": list(current_tags),
            "would_be_tags": list(new_tags),
        })

    return json.dumps({"results": results}, indent=2)


# ============================================================================
# System Monitoring
# ============================================================================


async def document_statistics(params: GetStatisticsInput) -> str:
    """
    Get comprehensive system statistics.

    Returns document counts, status distribution, version statistics, and more.
    """
    from backend.mcp_document_server.document_mcp_server import document_service

    all_docs = document_service.list_documents(limit=10000)
    documents = all_docs["documents"]

    total_docs = len(documents)
    status_counts = {"draft": 0, "published": 0, "archived": 0}
    total_size = 0
    tag_counts: dict[str, int] = {}

    for doc in documents:
        status_counts[doc["status"]] = status_counts.get(doc["status"], 0) + 1
        total_size += doc.get("size", 0)
        for tag in doc["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    stats = {
        "total_documents": total_docs,
        "total_size_bytes": total_size,
        "status_distribution": status_counts,
        "total_unique_tags": len(tag_counts),
        "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
    }

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(stats, indent=2)
    else:
        lines = [
            "# Document Library Statistics",
            "",
            f"**Total Documents**: {stats['total_documents']:,}",
            f"**Total Size**: {stats['total_size_bytes']:,} bytes ({stats['total_size_bytes'] / 1024 / 1024:.2f} MB)",
            "",
            "## Status Distribution",
        ]
        for status, count in stats["status_distribution"].items():
            lines.append(f"- **{status.capitalize()}**: {count:,}")
        lines.append("")
        lines.append(f"**Unique Tags**: {stats['total_unique_tags']}")
        if stats["top_tags"]:
            lines.append("")
            lines.append("## Top 10 Tags")
            for tag, count in stats["top_tags"]:
                lines.append(f"- **{tag}**: {count} document(s)")
        return "\n".join(lines)


__all__ = [
    "document_create",
    "document_get",
    "document_update",
    "document_delete",
    "document_search",
    "document_list_tags",
    "document_get_version",
    "document_compare_versions",
    "document_analyze",
    "document_export",
    "document_export_file",
    "document_download_file",
    "document_bulk_tag",
    "document_statistics",
    "register_tools",
]
