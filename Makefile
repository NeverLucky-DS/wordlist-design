# Deutsch Essay Trainer — developer workflow.
# Run `make` (or `make help`) to see every command.
#
# Typical first run:   make setup   →   edit backend/.env   →   make up
# Day-to-day:          make up   /   make logs   /   make down

# Host → Docker Postgres (published on localhost). Used by migrate/migration.
DB_URL ?= postgresql+asyncpg://wordlist:wordlist@localhost:5432/wordlist

.DEFAULT_GOAL := help
.PHONY: help setup up down restart logs ps migrate migration test db dev links clean

help: ## Show this help
	@echo "Deutsch Essay Trainer — make targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-11s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## First-time setup: install deps (uv) + create backend/.env
	@command -v uv >/dev/null 2>&1     || { echo "uv not found — install: https://docs.astral.sh/uv/"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "docker not found — install Docker Desktop"; exit 1; }
	uv sync
	@test -f backend/.env || { cp backend/.env.example backend/.env && echo "-> created backend/.env — add your API keys"; }
	@echo "Setup done. Put API keys in backend/.env, then run: make up"

up: ## Build & start the whole stack (db + api + web), then print all links
	docker compose up --build -d
	@echo "waiting for the API to become healthy..."
	@for i in $$(seq 1 60); do curl -fsS http://localhost:8000/health >/dev/null 2>&1 && break; sleep 2; done
	@$(MAKE) --no-print-directory links

down: ## Stop the stack (data is kept)
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Follow logs from all services (Ctrl-C to stop)
	docker compose logs -f --tail=100

ps: ## Show container status
	docker compose ps

migrate: ## Apply pending DB migrations to the running database
	cd backend && DATABASE_URL="$(DB_URL)" uv run alembic upgrade head

migration: ## Create a migration from model changes:  make migration name="add x"
	@test -n "$(name)" || { echo 'usage: make migration name="describe the change"'; exit 1; }
	cd backend && DATABASE_URL="$(DB_URL)" uv run alembic revision --autogenerate -m "$(name)"

test: ## Run the backend test suite (pytest)
	uv run pytest -v

db: ## Open a psql shell inside the database container
	docker compose exec postgres psql -U wordlist -d wordlist

dev: ## Run the API locally without Docker (autoreload, uses backend/.env DB)
	cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8000

links: ## Print all local URLs
	@echo ""
	@echo "  Frontend (nginx :8753)"
	@echo "    Woerterbuch   http://localhost:8753/index.html"
	@echo "    Schreiben     http://localhost:8753/schreiben.html"
	@echo "    Pipeline      http://localhost:8753/pipeline.html"
	@echo "  API (FastAPI :8000)"
	@echo "    Swagger docs  http://localhost:8000/docs"
	@echo "    Health        http://localhost:8000/health"
	@echo "  Database"
	@echo "    Postgres      postgres://wordlist:wordlist@localhost:5432/wordlist"
	@echo ""

clean: ## Stop the stack and DELETE all data (drops the database volume)
	docker compose down -v
