# Real-Time Climate Dashboard - Development Commands
# Professional Makefile for streamlined development workflow

.PHONY: help install dev-setup start stop restart logs clean test lint format

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
RESET := \033[0m

help: ## Show this help message
	@echo "$(CYAN)Real-Time Climate Dashboard - Development Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "$(BLUE)Installing Python dependencies...$(RESET)"
	cd backend && pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(RESET)"

dev-setup: ## Complete development environment setup
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)📋 Created .env file from template$(RESET)"; fi
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	make install
	@echo "$(BLUE)Starting infrastructure services...$(RESET)"
	docker-compose up -d postgres redis
	@echo "$(GREEN)🚀 Development environment ready!$(RESET)"
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  1. Update .env file with your settings"
	@echo "  2. Run 'make start' to start all services"
	@echo "  3. Visit http://localhost:8000/docs for API documentation"

start: ## Start all services
	@echo "$(BLUE)Starting all services...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)✅ All services started!$(RESET)"
	@echo "$(CYAN)Services available at:$(RESET)"
	@echo "  🌐 API Documentation: http://localhost:8000/docs"
	@echo "  🔄 Airflow UI: http://localhost:8080"
	@echo "  📊 Grafana: http://localhost:3001"
	@echo "  🎨 Frontend: http://localhost:3000"

start-dev: ## Start services in development mode with logs
	@echo "$(BLUE)Starting services in development mode...$(RESET)"
	docker-compose up --build

start-backend: ## Start only backend services (API, DB, Redis)
	@echo "$(BLUE)Starting backend services...$(RESET)"
	docker-compose up -d postgres redis backend
	@echo "$(GREEN)✅ Backend services started!$(RESET)"

start-frontend: ## Start only frontend service
	@echo "$(BLUE)Starting frontend service...$(RESET)"
	docker-compose up -d frontend
	@echo "$(GREEN)✅ Frontend service started!$(RESET)"

stop: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(RESET)"
	docker-compose down
	@echo "$(GREEN)✅ All services stopped!$(RESET)"

restart: ## Restart all services
	@echo "$(YELLOW)Restarting all services...$(RESET)"
	docker-compose restart
	@echo "$(GREEN)✅ All services restarted!$(RESET)"

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-db: ## Show database logs
	docker-compose logs -f postgres

logs-redis: ## Show Redis logs
	docker-compose logs -f redis

clean: ## Clean up containers and volumes
	@echo "$(YELLOW)Cleaning up Docker resources...$(RESET)"
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✅ Cleanup completed!$(RESET)"

reset: ## Reset entire development environment
	@echo "$(RED)⚠️  This will delete all data! Press Ctrl+C to cancel...$(RESET)"
	@sleep 5
	make clean
	docker volume prune -f
	@echo "$(GREEN)✅ Environment reset completed!$(RESET)"

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(RESET)"
	cd backend && python -m pytest tests/ -v
	@echo "$(GREEN)✅ Tests completed!$(RESET)"

test-backend: ## Run backend tests only
	@echo "$(BLUE)Running backend tests...$(RESET)"
	cd backend && python -m pytest tests/ -v --cov=app

lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(RESET)"
	cd backend && flake8 app/
	cd backend && black --check app/
	cd backend && isort --check-only app/
	@echo "$(GREEN)✅ Linting checks passed!$(RESET)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(RESET)"
	cd backend && black app/
	cd backend && isort app/
	@echo "$(GREEN)✅ Code formatted!$(RESET)"

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(RESET)"
	cd backend && alembic upgrade head
	@echo "$(GREEN)✅ Migrations completed!$(RESET)"

shell: ## Open Python shell with app context
	@echo "$(BLUE)Opening Python shell...$(RESET)"
	cd backend && python -c "from app.main import app; import asyncio; print('🐍 Python shell ready!')"

db-shell: ## Connect to PostgreSQL database
	@echo "$(BLUE)Connecting to database...$(RESET)"
	docker-compose exec postgres psql -U climate_user -d climate_dashboard

redis-shell: ## Connect to Redis
	@echo "$(BLUE)Connecting to Redis...$(RESET)"
	docker-compose exec redis redis-cli

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(RESET)"
	@echo "$(CYAN)API Health:$(RESET)"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "$(RED)❌ API not responding$(RESET)"
	@echo "$(CYAN)Database Status:$(RESET)"
	@docker-compose exec postgres pg_isready -U climate_user || echo "$(RED)❌ Database not ready$(RESET)"
	@echo "$(CYAN)Redis Status:$(RESET)"
	@docker-compose exec redis redis-cli ping || echo "$(RED)❌ Redis not responding$(RESET)"

monitor: ## Open monitoring dashboard
	@echo "$(BLUE)Opening monitoring dashboard...$(RESET)"
	@echo "$(CYAN)Available monitoring:$(RESET)"
	@echo "  📊 Grafana: http://localhost:3001"
	@echo "  📈 Prometheus: http://localhost:9090"
	@echo "  🔄 Airflow: http://localhost:8080"

docs: ## Generate and serve documentation
	@echo "$(BLUE)Serving API documentation...$(RESET)"
	@echo "$(CYAN)Documentation available at:$(RESET)"
	@echo "  📚 Swagger UI: http://localhost:8000/docs"
	@echo "  📖 ReDoc: http://localhost:8000/redoc"

backup-db: ## Backup database
	@echo "$(BLUE)Creating database backup...$(RESET)"
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U climate_user climate_dashboard > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backup created!$(RESET)"

# Development shortcuts
dev: dev-setup ## Alias for dev-setup
up: start ## Alias for start
down: stop ## Alias for stop
build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(RESET)"
	docker-compose build
	@echo "$(GREEN)✅ Images built!$(RESET)"

# Show current status
status: ## Show status of all services
	@echo "$(CYAN)Service Status:$(RESET)"
	docker-compose ps