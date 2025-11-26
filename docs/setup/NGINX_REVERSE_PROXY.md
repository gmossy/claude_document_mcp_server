# Nginx Reverse Proxy Setup

## Overview

The application now uses nginx as a reverse proxy, providing:
- Single entry point (port 80)
- No CORS issues (same origin)
- Better security (backend not directly exposed)
- Compression and caching
- SSL/HTTPS ready

## Architecture

```
Browser
   ↓
nginx (port 80)
   ├─ / → Frontend static files (React)
   ├─ /api/* → Backend API (uvicorn:8000)
   ├─ /docs → API documentation
   └─ /healthz → Health check
```

## Services

### nginx (Reverse Proxy)
- **Port**: 80
- **Container**: `document-processing-gateway-nginx`
- **Configuration**: `nginx/nginx.conf`
- **Responsibilities**:
  - Serve frontend static files
  - Proxy API requests to backend
  - Handle compression
  - Security headers
  - SSL termination (when configured)

### api (Backend)
- **Internal Port**: 8000 (not exposed externally)
- **Container**: `document-processing-gateway-api`
- **Access**: Via nginx at `/api/*`

### frontend (Build Only)
- **Container**: `document-processing-gateway-frontend`
- **Purpose**: Builds React app and shares via volume
- **Access**: Via nginx at `/`

## Configuration

### nginx Configuration

Location: `nginx/nginx.conf`

Key features:
- **Upstream**: `backend_api` → `api:8000`
- **API Proxy**: `/api/*` → `http://backend_api`
- **Static Files**: `/` → `/usr/share/nginx/html`
- **Compression**: Gzip enabled
- **Caching**: Static assets cached for 1 year
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **File Upload**: 50MB max body size

### Frontend API Configuration

The frontend now uses relative API paths:
```javascript
// Before: http://localhost:8000/api/v1
// After: /api/v1 (no CORS needed!)
```

Set via build arg:
```yaml
VITE_API_BASE_URL: /api/v1
```

## Usage

### Start All Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f nginx
docker-compose logs -f api
docker-compose logs -f frontend
```

### Access Points

- **Frontend**: http://localhost/
- **API**: http://localhost/api/v1/
- **API Docs**: http://localhost/docs
- **Health Check**: http://localhost/healthz

### Individual Service Management

```bash
# Rebuild nginx
docker-compose build nginx

# Restart nginx
docker-compose restart nginx

# View nginx logs
docker-compose logs -f nginx

# Test nginx configuration
docker-compose exec nginx nginx -t
```

## Benefits

### 1. No CORS Issues
- Frontend and API on same domain
- No CORS headers needed
- Simpler frontend code

### 2. Security
- Backend not directly exposed
- Security headers added
- Rate limiting ready
- DDoS protection ready

### 3. Performance
- Gzip compression (60-80% smaller responses)
- Static file caching
- Better connection handling

### 4. Production Ready
- Single entry point
- SSL/HTTPS ready
- Load balancing ready
- Industry standard pattern

## SSL/HTTPS Setup (Future)

To add SSL, update `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

## Troubleshooting

### nginx not starting
```bash
# Check nginx logs
docker-compose logs nginx

# Test configuration
docker-compose exec nginx nginx -t

# Check if port 80 is in use
sudo lsof -i :80
```

### Frontend not loading
```bash
# Check if frontend built successfully
docker-compose logs frontend

# Verify files in volume
docker-compose exec nginx ls -la /usr/share/nginx/html
```

### API not accessible
```bash
# Check backend is running
docker-compose ps api

# Test backend directly (internal network)
docker-compose exec nginx wget -O- http://api:8000/healthz

# Check nginx proxy logs
docker-compose logs nginx | grep api
```

### CORS errors
- Should not occur with reverse proxy
- If you see CORS errors, check:
  - Frontend is using relative paths (`/api/v1` not `http://localhost:8000/api/v1`)
  - nginx is properly proxying `/api/*`

## Migration from Old Setup

### Before (Direct Access)
- Frontend: `http://localhost:8080`
- API: `http://localhost:8000`
- CORS: Required

### After (Reverse Proxy)
- Frontend: `http://localhost/`
- API: `http://localhost/api/v1/`
- CORS: Not needed

### Update Frontend Code
No code changes needed if using `VITE_API_BASE_URL` environment variable. The build process automatically uses the relative path.

## Performance Tuning

### Increase Worker Processes
Edit `nginx/nginx.conf`:
```nginx
worker_processes auto;
worker_connections 1024;
```

### Enable Caching
Already configured for static assets. For API responses, add:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;
proxy_cache api_cache;
```

## Monitoring

### Health Checks
- nginx: `http://localhost/healthz`
- Backend: `http://localhost/api/v1/healthz`

### Logs
```bash
# All services
docker-compose logs -f

# Just nginx
docker-compose logs -f nginx

# Access logs
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

## Next Steps

1. **SSL/HTTPS**: Add Let's Encrypt certificates
2. **Rate Limiting**: Add nginx rate limiting rules
3. **Load Balancing**: Add multiple backend instances
4. **Monitoring**: Add Prometheus/Grafana
5. **CDN**: Serve static assets via CDN

