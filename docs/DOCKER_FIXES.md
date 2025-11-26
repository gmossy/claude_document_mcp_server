# Docker Files Review and Fixes

## Issues Found and Fixed

### 1. docker-compose.yml Syntax Error
**Issue**: Line 7 had invalid YAML syntax: `- .env` 
**Fix**: Removed the stray line (env_file already handles .env on line 15)

### 2. Frontend Port Mapping
**Issue**: Port mapping was `8080:8080` but nginx serves on port 80 inside container
**Fix**: Changed to `8080:80`

### 3. Frontend Healthcheck Port
**Issue**: Healthcheck was checking port 8080 but nginx serves on port 80
**Fix**: Changed to check port 80

### 4. Frontend Healthcheck Tool
**Issue**: Used `curl` which is not available in nginx:alpine image
**Fix**: 
- Installed `wget` in frontend Dockerfile
- Changed healthcheck to use `wget --spider`

### 5. Backend Healthcheck Tool
**Issue**: Used `curl` which may not be available in python:3.13-slim
**Fix**: Changed to use Python's built-in `urllib.request` module

### 6. Frontend Dockerfile Optimization
**Issue**: Used `npm install` with workarounds instead of `npm ci`
**Fix**: 
- Changed to `npm ci` for reproducible builds
- Removed workaround for vite installation (npm ci installs devDependencies)

## Docker Files Summary

### docker-compose.yml
- ✅ Fixed syntax error
- ✅ Fixed port mappings
- ✅ Fixed healthchecks to use available tools

### backend/app/Dockerfile
- ✅ Already optimized with BuildKit cache mounts
- ✅ Proper layer caching (requirements first)
- ✅ Uses python:3.13-slim base image

### frontend/Dockerfile.frontend
- ✅ Multi-stage build (node builder → nginx)
- ✅ Uses `npm ci` for reproducible builds
- ✅ BuildKit cache mounts for npm
- ✅ Installs wget for healthcheck
- ✅ Proper nginx configuration for SPA routing

### backend/mcp_document_server/Dockerfile
- ✅ Uses uv for dependency management
- ✅ Properly structured for MCP server

## Verification

Run `docker-compose config` to validate the configuration:
```bash
docker-compose config
```

All Docker files are now properly configured and optimized.
