.PHONY: help dev up down restart stop logs rebuild rebuild-cache clean test test-api test-frontend build build-api build-frontend shell shell-api shell-frontend health ps status

# Default target
.DEFAULT_GOAL := help

# Docker Compose file
COMPOSE_FILE := docker-compose.yml

# Service names
API_SERVICE := api
FRONTEND_SERVICE := frontend

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

dev: ## Start development environment (API + Frontend)
	@echo "$(GREEN)Starting development environment...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)Services started. API: http://localhost:8000, Frontend: http://localhost:8080$(NC)"
	@echo "$(YELLOW)Use 'make logs' to view logs$(NC)"

up: dev ## Alias for dev

start: dev ## Alias for dev

down: ## Stop and remove containers
	@echo "$(YELLOW)Stopping containers...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down
	@echo "$(GREEN)Containers stopped$(NC)"

stop: ## Stop containers without removing
	@echo "$(YELLOW)Stopping containers...$(NC)"
	docker-compose -f $(COMPOSE_FILE) stop
	@echo "$(GREEN)Containers stopped$(NC)"

restart: ## Restart all containers
	@echo "$(YELLOW)Restarting containers...$(NC)"
	docker-compose -f $(COMPOSE_FILE) restart
	@echo "$(GREEN)Containers restarted$(NC)"

logs: ## View logs from all services
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-api: ## View API service logs
	docker-compose -f $(COMPOSE_FILE) logs -f $(API_SERVICE)

logs-frontend: ## View frontend service logs
	docker-compose -f $(COMPOSE_FILE) logs -f $(FRONTEND_SERVICE)

rebuild: ## Rebuild containers without cache
	@echo "$(YELLOW)Rebuilding containers...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	@echo "$(GREEN)Containers rebuilt$(NC)"

rebuild-cache: ## Rebuild containers with cache
	@echo "$(YELLOW)Rebuilding containers (with cache)...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build
	@echo "$(GREEN)Containers rebuilt$(NC)"

rebuild-api: ## Rebuild API container only
	@echo "$(YELLOW)Rebuilding API container...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build --no-cache $(API_SERVICE)
	@echo "$(GREEN)API container rebuilt$(NC)"

rebuild-frontend: ## Rebuild frontend container only
	@echo "$(YELLOW)Rebuilding frontend container...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build --no-cache $(FRONTEND_SERVICE)
	@echo "$(GREEN)Frontend container rebuilt$(NC)"

build: rebuild-cache ## Alias for rebuild-cache

build-api: ## Build API container (with cache)
	@echo "$(YELLOW)Building API container...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build $(API_SERVICE)

build-frontend: ## Build frontend container (with cache)
	@echo "$(YELLOW)Building frontend container...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build $(FRONTEND_SERVICE)

clean: ## Stop containers and remove volumes
	@echo "$(RED)Cleaning up containers and volumes...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down -v
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-all: clean ## Clean containers, volumes, and images
	@echo "$(RED)Removing images...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down -v --rmi all
	@echo "$(GREEN)Complete cleanup done$(NC)"

ps: ## Show container status
	docker-compose -f $(COMPOSE_FILE) ps

status: ps ## Alias for ps

health: ## Check health of all services
	@echo "$(GREEN)Checking service health...$(NC)"
	@echo "$(YELLOW)API Health:$(NC)"
	@curl -s http://localhost:8000/healthz | python3 -m json.tool || echo "$(RED)API not responding$(NC)"
	@echo ""
	@echo "$(YELLOW)Frontend:$(NC)"
	@curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8080 || echo "$(RED)Frontend not responding$(NC)"

test: test-api ## Run all tests

test-api: ## Run API endpoint tests
	@echo "$(GREEN)Running API endpoint tests...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) exec -T $(API_SERVICE) python test_all_endpoints.py --base-url http://localhost:8000 || \
		(docker cp test_all_endpoints.py $$(docker-compose -f $(COMPOSE_FILE) ps -q $(API_SERVICE)):/app/test_all_endpoints.py && \
		 docker-compose -f $(COMPOSE_FILE) exec -T $(API_SERVICE) pip install -q requests && \
		 docker-compose -f $(COMPOSE_FILE) exec -T $(API_SERVICE) python test_all_endpoints.py --base-url http://localhost:8000)

test-frontend: ## Test frontend accessibility
	@echo "$(GREEN)Testing frontend...$(NC)"
	@curl -s -o /dev/null -w "Frontend HTTP Status: %{http_code}\n" http://localhost:8080 || echo "$(RED)Frontend not accessible$(NC)"

shell: shell-api ## Open shell in API container

shell-api: ## Open shell in API container
	@echo "$(GREEN)Opening shell in API container...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(API_SERVICE) /bin/bash || \
	docker-compose -f $(COMPOSE_FILE) exec $(API_SERVICE) /bin/sh

shell-frontend: ## Open shell in frontend container
	@echo "$(GREEN)Opening shell in frontend container...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(FRONTEND_SERVICE) /bin/bash || \
	docker-compose -f $(COMPOSE_FILE) exec $(FRONTEND_SERVICE) /bin/sh

install-deps: ## Install dependencies in API container
	@echo "$(GREEN)Installing dependencies...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(API_SERVICE) pip install requests

setup: ## Initial setup - build and start services
	@echo "$(GREEN)Setting up project...$(NC)"
	@make build
	@make dev
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:8080$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(NC)"

update: rebuild dev ## Rebuild and restart services

pull: ## Pull latest images
	@echo "$(GREEN)Pulling latest images...$(NC)"
	docker-compose -f $(COMPOSE_FILE) pull

prune: ## Clean up Docker system (dangling images, containers, etc.)
	@echo "$(RED)Cleaning up Docker system...$(NC)"
	docker system prune -f
	@echo "$(GREEN)Docker cleanup complete$(NC)"

stats: ## Show container resource usage
	@echo "$(GREEN)Container resource usage:$(NC)"
	docker stats --no-stream $$(docker-compose -f $(COMPOSE_FILE) ps -q)

top: ## Show running processes in containers
	docker-compose -f $(COMPOSE_FILE) top

