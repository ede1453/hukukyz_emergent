.PHONY: help build up down logs restart clean test migrate

help: ## Show this help
	@echo "HukukYZ - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "✅ Services started"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8001"
	@echo "   Qdrant:   http://localhost:6333"

down: ## Stop all services
	docker-compose down

logs: ## Show logs (use: make logs service=backend)
ifdef service
	docker-compose logs -f $(service)
else
	docker-compose logs -f
endif

restart: ## Restart all services
	docker-compose restart

clean: ## Stop and remove all containers, volumes
	docker-compose down -v
	@echo "⚠️  All data removed"

ps: ## Show running containers
	docker-compose ps

backend-shell: ## Open backend shell
	docker-compose exec backend bash

frontend-shell: ## Open frontend shell
	docker-compose exec frontend sh

qdrant-shell: ## Open Qdrant shell
	docker-compose exec qdrant sh

migrate: ## Migrate FAISS to Qdrant
	docker-compose exec backend python backend/scripts/migrate_faiss_to_qdrant.py

sample-data: ## Load sample legal data
	docker-compose exec backend python backend/scripts/create_sample_data.py

test-api: ## Test backend API
	curl http://localhost:8001/health
	@echo ""
	curl http://localhost:8001/api/documents/stats
	@echo ""

prod-up: ## Start in production mode
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-build: ## Build production images
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-down: ## Stop production services
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
