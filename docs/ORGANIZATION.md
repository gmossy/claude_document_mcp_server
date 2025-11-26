# Project File Organization

This document describes the organization of files in the project.

## Directory Structure

### `/docs/` - Documentation
- **`/docs/setup/`** - Setup and configuration documentation
  - `CORS_FIX.md` - CORS configuration guide
  - `DOCKER_SETUP.md` - Docker setup instructions
  - `DOCKER_TEST_RESULTS.md` - Docker test results
  - `README_TESTING.md` - Testing guide
  - `RUN_APPLICATION.md` - Application run instructions

- **`/docs/frontend/`** - Frontend-specific documentation
  - `FRONTEND_INTEGRATION.md` - Frontend integration guide
  - `FRONTEND_LISTING_SUMMARY.md` - Frontend listing summary

- **`/docs/legacy/`** - Legacy documentation (archived)

### `/tests/` - Test Files
- `test_all_endpoints.py` - Comprehensive endpoint tests
- `test_all_file_types.py` - File type upload tests
- `test_endpoints.py` - Basic endpoint tests
- **`/tests/data/`** - Test data files
  - Test Excel files (`.xlsx`)
  - Test PowerPoint files (`.pptx`)
  - Test text files (`Text_*.txt`)
  - Sample templates

### `/config/` - Configuration Files
- `inspector.config.json` - MCP Inspector configuration
- `pyrightconfig.json` - Pyright type checker configuration
- `inspector.log` - Inspector log file

### `/backend/` - Backend Code
- **`/backend/requirements-dev.txt`** - Development dependencies
- **`/backend/requirements-test.txt`** - Test dependencies

### Root Level
- `README.md` - Main project documentation
- `Makefile` - Build and test commands
- `docker-compose.yml` - Docker orchestration
- `.gitignore` - Git ignore rules

## Path Updates

The following paths have been updated in code and documentation:

1. **Test scripts**: `test_*.py` → `tests/test_*.py`
2. **Requirements files**: `requirements-*.txt` → `backend/requirements-*.txt`
3. **Config files**: `*.config.json` → `config/*.config.json`
4. **Test data**: Test files → `tests/data/`
5. **Documentation**: Setup docs → `docs/setup/`, Frontend docs → `docs/frontend/`

## Updated References

- `Makefile`: Updated `test-api` target to use `tests/test_all_endpoints.py`
- `README.md`: Updated inspector config path to `config/inspector.config.json`
- `backend/mcp_document_server/README-mcp.md`: Updated config path
- `docs/setup/README_TESTING.md`: Updated all test script and requirements paths
- `tests/test_all_endpoints.py`: Updated requirements path to `backend/requirements-test.txt`
- `.gitignore`: Updated test output paths to `tests/data/`

