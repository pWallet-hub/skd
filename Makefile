# SmartKids developer commands. Run `make help` to list them.
COMPOSE ?= docker compose
BACKEND  = $(COMPOSE) exec backend
FRONTEND = $(COMPOSE) exec frontend

.DEFAULT_GOAL := help
.PHONY: help env up down restart build logs ps shell db-shell migrate migration seed test lint format frontend-lint clean reset

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example (if missing)
	@test -f .env || (cp .env.example .env && echo ".env created")

up: env ## Build and start the whole stack
	$(COMPOSE) up -d --build

down: ## Stop the stack
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

build: env ## Rebuild images
	$(COMPOSE) build

logs: ## Follow logs (make logs s=backend for one service)
	$(COMPOSE) logs -f $(s)

ps: ## Show running services
	$(COMPOSE) ps

shell: ## Open a shell in the backend container
	$(BACKEND) bash

db-shell: ## Open psql in the database
	$(COMPOSE) exec db sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB'

migrate: ## Apply database migrations
	$(BACKEND) alembic upgrade head

migration: ## Create a migration: make migration m="add something"
	$(BACKEND) alembic revision --autogenerate -m "$(m)"
	$(BACKEND) chown -R $(shell id -u):$(shell id -g) alembic/versions

seed: ## Load fictional demo data (safe to re-run)
	$(BACKEND) python -m app.scripts.seed

test: ## Run backend tests
	$(BACKEND) pytest

lint: ## Lint backend (ruff) and frontend (eslint + tsc)
	$(BACKEND) ruff check .
	$(BACKEND) ruff format --check .
	$(FRONTEND) npm run lint
	$(FRONTEND) npm run typecheck

format: ## Auto-format backend code
	$(BACKEND) ruff format .
	$(BACKEND) ruff check --fix .

clean: ## Stop the stack and remove containers (keeps data)
	$(COMPOSE) down --remove-orphans

reset: ## DANGER: stop the stack and delete ALL data volumes
	$(COMPOSE) down -v --remove-orphans
