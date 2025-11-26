# Frontend Display Fields Documentation

This document describes all the fields that the frontend displays for documents in the document library.

## Document Display Fields

The frontend displays the following information for each document:

### 1. **Document Title**
- **Source**: `doc.title` or `doc.name`
- **Display**: Main heading in the document card
- **Fallback**: "Untitled" if not available

### 2. **Upload Date**
- **Source**: `doc.created_at` (ISO 8601 format)
- **Display**: Formatted as "Uploaded [Month Day, Year]" (e.g., "Uploaded Nov 26, 2025")
- **Format**: `new Date(uploadDate).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })`

### 3. **File Size**
- **Source**: `doc.size` (bytes)
- **Display**: Formatted as human-readable size (e.g., "1.5 MB", "256 KB")
- **Format**: Automatically converts bytes to appropriate unit (Bytes, KB, MB, GB)

### 4. **File Type/Format**
- **Source**: `doc.binary.format` or `doc.metadata.format`
- **Display**: Uppercase format (e.g., "PDF", "DOCX", "XLSX")
- **Fallback**: "UNKNOWN" if not available

### 5. **Category (DOTMLPF-P)**
- **Source**: `doc.metadata.category`
- **Display**: Badge with blue background
- **Examples**: 
  - "Training"
  - "Doctrine"
  - "Organization"
  - "Materiel"
  - "Leadership"
  - "Personnel"
  - "Facilities"
  - "Policy"
- **Fallback**: "Uncategorized"

### 6. **Source/Organization**
- **Source**: `doc.metadata.source` or `doc.metadata.organization`
- **Display**: Badge with green background
- **Examples**:
  - "US Army"
  - "US Navy"
  - "US Air Force"
  - "US Marine Corps"
  - "NASA"
  - "MIT Research"
  - "Stanford University"
- **Fallback**: "Unknown"

### 7. **Status**
- **Source**: `doc.status`
- **Display**: Badge with gray background
- **Values**: "draft", "published", "archived"
- **Default**: "draft"

### 8. **Tags**
- **Source**: `doc.tags` (array of strings)
- **Display**: Multiple badges with gray background
- **Examples**: ["doctrine", "joint-operations", "training", "analysis"]
- **Features**: 
  - Searchable
  - Filterable
  - Clickable (future feature)

### 9. **Description** (Optional)
- **Source**: `doc.metadata.description`
- **Display**: Small text below the document info, truncated to 2 lines
- **Format**: Line-clamped with ellipsis if too long

## Statistics Cards

The frontend displays four statistics cards:

1. **Total Documents**: Count of all documents in the library
2. **Filtered Results**: Count of documents matching current filters
3. **Categories**: Count of unique categories across all documents
4. **Organizations**: Count of unique organizations/sources across all documents

## Filtering

The frontend supports filtering by:

- **Search Term**: Searches across title, tags, and description
- **Category**: Filter by DOTMLPF-P category (dynamically populated from documents)
- **Source/Organization**: Filter by source organization (dynamically populated from documents)

## Data Flow

```
Backend API Response
  ↓
{
  "documents": [
    {
      "id": "doc_abc123",
      "title": "Document Title",
      "created_at": "2025-11-26T03:38:54.877484+00:00",
      "size": 1024,
      "tags": ["tag1", "tag2"],
      "status": "draft",
      "metadata": {
        "category": "Training",
        "source": "US Army",
        "description": "Document description"
      }
    }
  ]
}
  ↓
formatDocument() function
  ↓
{
  id: "doc_abc123",
  name: "Document Title",
  category: "Training",
  source: "US Army",
  uploadDate: "2025-11-26T03:38:54.877484+00:00",
  formattedDate: "Nov 26, 2025",
  size: "1.0 KB",
  sizeBytes: 1024,
  type: "PDF",
  tags: ["tag1", "tag2"],
  status: "draft",
  description: "Document description"
}
  ↓
React Component Rendering
```

## Backend Requirements

For the frontend to display all fields correctly, the backend must return:

1. **Metadata in list response**: The `list_documents` endpoint must include `metadata` field
2. **All document fields**: `id`, `title`, `created_at`, `size`, `tags`, `status`, `metadata`
3. **Metadata structure**: JSON object with `category`, `source`/`organization`, `description`, `format` (optional)

## Example API Response

```json
{
  "documents": [
    {
      "id": "doc_abc123def456",
      "title": "Joint Training Doctrine Manual 2024",
      "status": "published",
      "created_at": "2024-10-15T10:30:00Z",
      "updated_at": "2024-10-16T14:20:00Z",
      "size": 2457600,
      "tags": ["doctrine", "joint-operations", "training"],
      "metadata": {
        "category": "Training",
        "source": "US Army",
        "organization": "US Army",
        "description": "Comprehensive guide for joint training operations",
        "format": "pdf"
      }
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

## Frontend Component Structure

```
DocumentLibrary
├── Header
│   ├── Title
│   └── Upload Button
├── Search and Filters
│   ├── Search Input
│   └── Category/Source Filters
├── Statistics Cards
│   ├── Total Documents
│   ├── Filtered Results
│   ├── Categories Count
│   └── Organizations Count
└── Document List
    └── Document Card (for each document)
        ├── File Icon
        ├── Title
        ├── Badges (Category, Source, Status, Tags)
        ├── Metadata (Type, Size, Upload Date)
        └── Description (if available)
```

## Notes

- All dates are displayed in the user's local timezone
- File sizes are automatically formatted to the most appropriate unit
- Categories and sources are dynamically populated from actual document metadata
- Empty or missing fields use appropriate fallback values
- The frontend handles both string and object metadata formats

