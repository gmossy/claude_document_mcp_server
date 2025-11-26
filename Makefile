.PHONY: dev rebuild rebuild-frontend rebuild-backend logs test test-api health ps down clean build-fast

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Development
dev:
	docker-compose up -d

# Rebuild all services
rebuild:
	docker-compose build --no-cache

# Rebuild with cache (faster)
rebuild-fast:
	docker-compose build

# Rebuild frontend only
rebuild-frontend:
	docker-compose build --no-cache frontend

# Rebuild backend only
rebuild-backend:
	docker-compose build --no-cache api

# Rebuild with cache (faster)
rebuild-frontend-fast:
	docker-compose build frontend

rebuild-backend-fast:
	docker-compose build api

# View logs
logs:
	docker-compose logs -f

# Run tests
test:
	python3 -m pytest backend/app/tests/ -v

# Run API endpoint tests
test-api:
	python3 test_all_endpoints.py

# Health check
health:
	curl -f http://localhost:8000/healthz && echo "✓ API healthy" || echo "✗ API unhealthy"

# Show running containers
ps:
	docker-compose ps

# Stop services
down:
	docker-compose down

# Clean up (remove containers, volumes, networks)
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Build with BuildKit cache
build-fast:
	DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build
