# Docker Setup for Full Stack Application

## Overview

This setup runs both the backend API and frontend in Docker containers.

## Services

### Backend API (FastAPI)
- **Port**: 8000
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/healthz

### Frontend (React + Vite)
- **Port**: 8080
- **URL**: http://localhost:8080
- **Built with**: Vite + React
- **Served by**: Nginx

## Quick Start

### Build and Run All Services

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Individual Service Commands

```bash
# Build only backend
docker-compose build api

# Build only frontend
docker-compose build frontend

# Start only backend
docker-compose up -d api

# Start only frontend
docker-compose up -d frontend

# View backend logs
docker-compose logs -f api

# View frontend logs
docker-compose logs -f frontend
```

## Configuration

### Backend Environment Variables
- `DATABASE_URL`: SQLite database path
- `STORAGE_DIR`: Document storage directory
- `API_VERSION`: API version string
- `ALLOW_ORIGINS`: CORS allowed origins (default: `["*"]`)

### Frontend Build Arguments
- `VITE_API_BASE_URL`: Backend API URL (default: `http://localhost:8000/api/v1`)

**Note**: For production, update `VITE_API_BASE_URL` to point to your production API URL.

## Accessing the Application

1. **Frontend**: http://localhost:8080
2. **Backend API**: http://localhost:8000
3. **API Documentation**: http://localhost:8000/docs

## Development vs Production

### Development
- Frontend runs with Vite dev server (hot reload)
- Backend runs in Docker

```bash
# Terminal 1: Backend
docker-compose up api

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Production (Docker)
- Both services run in Docker containers
- Frontend is built and served by Nginx
- Backend runs in Docker with all dependencies

```bash
docker-compose up -d
```

## Troubleshooting

### Frontend Can't Connect to Backend

1. **Check API URL**: Ensure `VITE_API_BASE_URL` is correct
2. **Check CORS**: Backend should allow frontend origin
3. **Check Network**: Both containers should be on same Docker network

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose build
docker-compose up -d

# Or rebuild specific service
docker-compose build frontend
docker-compose up -d frontend
```

### View Container Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
```

### Check Container Status

```bash
docker-compose ps
```

### Access Container Shell

```bash
# Backend
docker-compose exec api /bin/bash

# Frontend
docker-compose exec frontend /bin/sh
```

## Data Persistence

- **Database**: Stored in `./data/documents.db` (mounted volume)
- **Documents**: Stored in `./data/document_storage` (mounted volume)
- **Data persists** across container restarts

## Production Deployment

### Update API URL for Production

Edit `docker-compose.yml`:

```yaml
frontend:
  build:
    args:
      - VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
```

### Environment Variables

Create `.env` file or set environment variables:

```bash
export DATABASE_URL=sqlite:////data/documents.db
export STORAGE_DIR=/data/document_storage
export VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
```

## Health Checks

### Backend Health
```bash
curl http://localhost:8000/healthz
```

### Frontend Health
```bash
curl http://localhost:8080
```

## Network Configuration

Both services are on the same Docker network and can communicate:
- Frontend → Backend: `http://api:8000` (internal)
- External → Frontend: `http://localhost:8080`
- External → Backend: `http://localhost:8000`

## Volume Mounts

- `./data:/data` - Database and document storage
- Data persists in `./data` directory on host

## Ports

- **8000**: Backend API
- **8080**: Frontend (Nginx)

To change ports, edit `docker-compose.yml`:

```yaml
ports:
  - "3000:8000"  # Backend on port 3000
  - "80:80"      # Frontend on port 80
```

