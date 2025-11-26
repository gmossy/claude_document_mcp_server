# Running the Application

## Quick Start

### Backend API (FastAPI)

The backend runs in a Docker container:

```bash
# Start the API server
docker-compose up -d api

# Check status
docker-compose ps

# View logs
docker-compose logs api -f

# Stop the server
docker-compose down
```

**API URL**: http://localhost:8000
**API Docs**: http://localhost:8000/docs
**Health Check**: http://localhost:8000/healthz

### Frontend (React + Vite)

The frontend runs as a development server:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Frontend URL**: http://localhost:5173

## Running Both Services

### Option 1: Separate Terminals

**Terminal 1 - Backend:**
```bash
docker-compose up api
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Background Processes

**Backend (Docker - runs in background):**
```bash
docker-compose up -d api
```

**Frontend (npm - runs in foreground):**
```bash
cd frontend
npm run dev
```

## Environment Configuration

### Backend
- Configured via Docker environment variables
- Database: `/data/documents.db` (SQLite)
- Storage: `/data/document_storage`

### Frontend
Create `frontend/.env` file:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Or use the default (already configured in code).

## Accessing the Application

1. **Frontend UI**: Open http://localhost:5173 in your browser
2. **API Documentation**: Open http://localhost:8000/docs for interactive API docs
3. **Health Check**: http://localhost:8000/healthz

## Troubleshooting

### Backend Not Starting
```bash
# Check container logs
docker-compose logs api

# Restart container
docker-compose restart api

# Rebuild if needed
docker-compose build api
docker-compose up -d api
```

### Frontend Not Starting
```bash
# Check if port 5173 is available
lsof -i :5173

# Install dependencies
cd frontend
npm install

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### CORS Errors
- Verify backend is running: `curl http://localhost:8000/healthz`
- Check `VITE_API_BASE_URL` in frontend `.env` file
- Verify CORS configuration in `backend/app/config.py`

### Connection Refused
- Ensure backend is running: `docker-compose ps`
- Check API is accessible: `curl http://localhost:8000/healthz`
- Verify frontend `.env` has correct API URL

## Development Workflow

1. **Start Backend**: `docker-compose up -d api`
2. **Start Frontend**: `cd frontend && npm run dev`
3. **Open Browser**: http://localhost:5173
4. **Make Changes**: Frontend hot-reloads automatically
5. **View API Docs**: http://localhost:8000/docs

## Production Build

### Frontend Build
```bash
cd frontend
npm run build
# Output in frontend/dist/
```

### Backend Production
```bash
# Use production Docker image
docker-compose -f docker-compose.prod.yml up -d
```

## Stopping Services

```bash
# Stop frontend (Ctrl+C in terminal)

# Stop backend
docker-compose down
```

