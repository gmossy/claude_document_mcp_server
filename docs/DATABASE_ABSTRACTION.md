# Database Abstraction Layer

## Overview

This document describes the database abstraction layer that enables switching between SQLite and PostgreSQL (or other databases) without changing application code.

## Architecture

### Abstract Base Class

**Location**: `backend/core/db/base.py`

The `DatabaseAdapter` abstract base class defines the interface that all database implementations must follow:

- **Connection Management**: `connect()`, `close()`
- **Query Execution**: `execute()`, `fetchone()`, `fetchall()`
- **Transaction Management**: `commit()`, `rollback()`
- **Schema Management**: `init_schema()`
- **Database-Specific Helpers**: 
  - `get_parameter_placeholder()` - Returns `?` for SQLite, `%s` for PostgreSQL
  - `get_text_type()` - Returns appropriate TEXT type
  - `get_integer_primary_key()` - Returns appropriate auto-increment syntax
  - `supports_fts()` - Whether full-text search is supported
  - `create_fts_index()` - Create full-text search index
  - `create_fts_triggers()` - Create triggers for FTS sync

### Implementations

#### SQLite Adapter

**Location**: `backend/core/db/sqlite_adapter.py`

- **Status**: ✅ Fully implemented
- **Connection**: Uses `sqlite3.connect()` with `row_factory=sqlite3.Row`
- **FTS**: Uses SQLite FTS5 virtual tables
- **Parameter Placeholder**: `?`
- **Primary Key**: `INTEGER PRIMARY KEY AUTOINCREMENT`

#### PostgreSQL Adapter

**Location**: `backend/core/db/postgres_adapter.py`

- **Status**: 🚧 Stub implementation (ready for completion)
- **Connection**: Will use `psycopg2` with `RealDictCursor`
- **FTS**: Will use PostgreSQL `tsvector` and GIN indexes
- **Parameter Placeholder**: `%s`
- **Primary Key**: `BIGSERIAL PRIMARY KEY`

## Current Database Usage

### Files Using Direct SQLite Access

1. **`backend/mcp_document_server/document_mcp_server.py`**
   - Line 15: `import sqlite3`
   - Line 468: `sqlite3.connect(DATABASE_PATH)` in `init_database()`
   - Multiple locations: Direct SQLite connection usage via `document_service.connect()`

2. **`backend/core/services/documents.py`**
   - Line 5: `import sqlite3`
   - Line 46-49: `_connect()` method returns `sqlite3.Connection`
   - All CRUD operations use direct SQLite connections

3. **`backend/app/api/deps.py`**
   - Line 2: `import sqlite3`
   - Line 13-19: `get_db()` function returns `sqlite3.Connection`
   - Line 8: Direct path extraction from `sqlite:///` URL

4. **`backend/app/config.py`**
   - Line 6: `database_url: str = "sqlite:///./documents.db"`

## Migration Plan

### Phase 1: Update DocumentService ✅ (In Progress)

**File**: `backend/core/services/documents.py`

**Changes Needed**:
1. Replace `db_path: Path` with `db_adapter: DatabaseAdapter`
2. Replace `_connect()` to use `db_adapter.connect()`
3. Replace all `cursor.execute()` calls to use `db_adapter.execute()`
4. Replace `cursor.fetchone()` with `db_adapter.fetchone()`
5. Replace `cursor.fetchall()` with `db_adapter.fetchall()`
6. Replace `conn.commit()` with `db_adapter.commit()`
7. Replace `conn.close()` with `db_adapter.close()`
8. Update SQL queries to use `db_adapter.get_parameter_placeholder()`

**Example**:
```python
# Before
def _connect(self) -> sqlite3.Connection:
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    return conn

# After
def __init__(self, db_adapter: DatabaseAdapter, storage_dir: Path):
    self.db_adapter = db_adapter
    self.storage_dir = storage_dir

def _connect(self):
    return self.db_adapter.connect()
```

### Phase 2: Update MCP Server ✅ (In Progress)

**File**: `backend/mcp_document_server/document_mcp_server.py`

**Changes Needed**:
1. Replace `init_database()` to use adapter's `init_schema()`
2. Update `document_service` initialization to use adapter
3. Remove direct `sqlite3` imports where possible
4. Update all direct database access to use adapter

**Example**:
```python
# Before
def init_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS documents...")
    conn.commit()
    conn.close()

# After
def init_database():
    adapter = SQLiteAdapter(DATABASE_PATH)
    conn = adapter.connect()
    adapter.init_schema(conn)
    adapter.close(conn)
```

### Phase 3: Update FastAPI Dependencies

**File**: `backend/app/api/deps.py`

**Changes Needed**:
1. Replace `get_db()` to use adapter pattern
2. Update `get_document_service()` to use adapter
3. Parse `database_url` to determine adapter type

**Example**:
```python
# Before
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# After
def get_db_adapter() -> DatabaseAdapter:
    if settings.database_url.startswith("sqlite:///"):
        db_path = Path(settings.database_url.replace("sqlite:///", ""))
        return SQLiteAdapter(db_path)
    elif settings.database_url.startswith("postgresql://"):
        return PostgreSQLAdapter(settings.database_url)
    else:
        raise ValueError(f"Unsupported database URL: {settings.database_url}")
```

### Phase 4: Configuration Updates

**File**: `backend/app/config.py`

**Changes Needed**:
1. Add database type detection
2. Support both SQLite and PostgreSQL connection strings

**Example**:
```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./documents.db"
    # Could be:
    # - sqlite:///./documents.db
    # - postgresql://user:pass@localhost:5432/dbname
    
    @property
    def database_type(self) -> str:
        if self.database_url.startswith("sqlite:///"):
            return "sqlite"
        elif self.database_url.startswith("postgresql://"):
            return "postgresql"
        else:
            raise ValueError(f"Unknown database type: {self.database_url}")
```

## Database Schema Differences

### SQLite vs PostgreSQL

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Parameter Placeholder | `?` | `%s` |
| Primary Key | `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGSERIAL PRIMARY KEY` |
| TEXT Type | `TEXT` | `TEXT` (same) |
| Full-Text Search | FTS5 Virtual Tables | `tsvector` + GIN Index |
| Triggers | SQLite syntax | PostgreSQL syntax |
| Row Factory | `sqlite3.Row` | `psycopg2.extras.RealDictCursor` |

### Full-Text Search Differences

**SQLite (FTS5)**:
```sql
CREATE VIRTUAL TABLE documents_fts USING fts5(
    id, title, content, tags,
    content='documents',
    content_rowid='rowid'
);
```

**PostgreSQL (tsvector)**:
```sql
ALTER TABLE documents ADD COLUMN fts_vector tsvector;
CREATE INDEX documents_fts_idx ON documents USING GIN(fts_vector);

CREATE TRIGGER documents_fts_update BEFORE INSERT OR UPDATE
ON documents FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(
    fts_vector, 'pg_catalog.english', title, content
);
```

## Usage Examples

### Initializing with SQLite (Current)

```python
from backend.core.db import SQLiteAdapter
from backend.core.services import DocumentService
from pathlib import Path

# Create adapter
adapter = SQLiteAdapter(Path("./documents.db"))

# Initialize schema
conn = adapter.connect()
adapter.init_schema(conn)
adapter.close(conn)

# Create service
service = DocumentService(adapter, Path("./storage"))
```

### Initializing with PostgreSQL (Future)

```python
from backend.core.db import PostgreSQLAdapter
from backend.core.services import DocumentService
from pathlib import Path

# Create adapter
adapter = PostgreSQLAdapter("postgresql://user:pass@localhost:5432/dbname")

# Initialize schema
conn = adapter.connect()
adapter.init_schema(conn)
adapter.close(conn)

# Create service (same interface!)
service = DocumentService(adapter, Path("./storage"))
```

### Switching Database at Runtime

```python
from backend.core.db import SQLiteAdapter, PostgreSQLAdapter
from backend.core.services import DocumentService
from backend.app.config import settings

# Determine adapter from config
if settings.database_type == "sqlite":
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    adapter = SQLiteAdapter(db_path)
elif settings.database_type == "postgresql":
    adapter = PostgreSQLAdapter(settings.database_url)
else:
    raise ValueError(f"Unsupported database: {settings.database_type}")

# Service works the same regardless of database!
service = DocumentService(adapter, Path(settings.storage_dir))
```

## Testing

### Unit Tests

Create tests for each adapter:

- `tests/test_sqlite_adapter.py` - Test SQLite implementation
- `tests/test_postgres_adapter.py` - Test PostgreSQL implementation
- `tests/test_database_abstraction.py` - Test adapter interface compliance

### Integration Tests

Test that `DocumentService` works with both adapters:

```python
def test_document_service_with_sqlite():
    adapter = SQLiteAdapter(Path(":memory:"))
    service = DocumentService(adapter, Path("./test_storage"))
    # Test operations...

def test_document_service_with_postgresql():
    adapter = PostgreSQLAdapter("postgresql://...")
    service = DocumentService(adapter, Path("./test_storage"))
    # Test operations...
```

## Benefits

1. **Database Agnostic**: Application code doesn't depend on specific database
2. **Easy Migration**: Switch databases by changing adapter initialization
3. **Testability**: Use in-memory SQLite for fast tests
4. **Flexibility**: Support multiple databases in same codebase
5. **Maintainability**: Database-specific code isolated in adapters

## Next Steps

1. ✅ Create abstraction layer (base.py, sqlite_adapter.py, postgres_adapter.py)
2. 🔄 Refactor DocumentService to use adapter
3. 🔄 Refactor document_mcp_server.py to use adapter
4. ⏳ Refactor FastAPI deps.py to use adapter
5. ⏳ Complete PostgreSQL adapter implementation
6. ⏳ Add comprehensive tests
7. ⏳ Update documentation

## References

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)

