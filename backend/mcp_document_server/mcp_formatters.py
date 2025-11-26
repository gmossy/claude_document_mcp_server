"""Formatting helper functions for MCP document server."""

import json
from datetime import datetime


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return iso_timestamp


def calculate_reading_time(content: str) -> int:
    """Calculate estimated reading time in minutes (200 words/min)."""
    word_count = len(content.split())
    return max(1, round(word_count / 200))


def extract_keywords(content: str, top_n: int = 10) -> list[str]:
    """Extract top keywords from content."""
    # Simple keyword extraction based on word frequency
    words = content.lower().split()
    # Filter out common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them',
        'their', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why',
        'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 'just', 'also'
    }

    # Count word frequencies
    word_freq: dict[str, int] = {}
    for word in words:
        # Clean word
        clean_word = ''.join(c for c in word if c.isalnum())
        if clean_word and len(clean_word) > 3 and clean_word not in stop_words:
            word_freq[clean_word] = word_freq.get(clean_word, 0) + 1

    # Sort by frequency and return top N
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def format_document_markdown(
    doc: dict,
    include_content: bool = True,
    include_versions: bool = False
) -> str:
    """Format a document as Markdown."""
    lines = [
        f"# {doc['title']}",
        "",
        f"**ID**: `{doc['id']}`",
        f"**Status**: {doc['status']}",
        f"**Created**: {format_timestamp(doc['created_at'])}",
        f"**Last Updated**: {format_timestamp(doc['updated_at'])}",
        f"**Size**: {doc['size']:,} bytes",
    ]

    tags = json.loads(doc['tags']) if isinstance(doc['tags'], str) else doc['tags']
    if tags:
        lines.append(f"**Tags**: {', '.join(tags)}")

    metadata = json.loads(doc['metadata']) if isinstance(doc['metadata'], str) else doc['metadata']
    if metadata:
        lines.append("")
        lines.append("## Metadata")
        for key, value in metadata.items():
            lines.append(f"- **{key}**: {value}")

    if include_content:
        lines.append("")
        lines.append("## Content")
        lines.append("")
        lines.append(doc['content'])

    if include_versions and 'versions' in doc:
        lines.append("")
        lines.append("## Version History")
        for ver in doc['versions']:
            lines.append(f"- **v{ver['version_number']}** ({format_timestamp(ver['created_at'])})")
            if ver['comment']:
                lines.append(f"  - {ver['comment']}")

    return "\n".join(lines)


def format_search_results_markdown(results: list[dict], total: int, offset: int) -> str:
    """Format search results as Markdown."""
    lines = [
        "# Search Results",
        "",
        f"Found **{total}** documents (showing {offset + 1}-{offset + len(results)})",
        ""
    ]

    for i, doc in enumerate(results, 1):
        tags = json.loads(doc['tags']) if isinstance(doc['tags'], str) else doc['tags']
        tag_str = f" • Tags: {', '.join(tags)}" if tags else ""
        lines.append(f"### {i}. {doc['title']}")
        status_line = (
            f"ID: `{doc['id']}` • Status: {doc['status']} • "
            f"Updated: {format_timestamp(doc['updated_at'])}{tag_str}"
        )
        lines.append(status_line)

        # Show content preview (first 200 chars)
        preview = doc['content'][:200].replace('\n', ' ')
        if len(doc['content']) > 200:
            preview += "..."
        lines.append(f"> {preview}")
        lines.append("")

    return "\n".join(lines)

