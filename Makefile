.PHONY: help run lint format test check clean \
        db-up db-down db-reset db-logs db-ps \
        bot-up bot-down bot-logs bot-rebuild \
        migrate migration

help:
	@echo "Available commands:"
	@echo ""
	@echo "  Application:"
	@echo "    make run       - Run the Telegram bot"
	@echo "    make lint      - Check code with ruff"
	@echo "    make format    - Format code with ruff"
	@echo "    make test      - Run tests with pytest"
	@echo "    make check     - Run lint + test (before commit)"
	@echo "    make clean     - Remove caches and build artifacts"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate   - Apply all pending migrations (alembic upgrade head)"
	@echo "    make migration - Create new migration (make migration m=\"message\")"
	@echo ""
	@echo "  Docker:"
	@echo "    make db-up        - Start postgres + redis containers"
	@echo "    make db-down      - Stop containers (data preserved)"
	@echo "    make db-reset     - Stop containers and WIPE data"
	@echo "    make db-logs      - Tail postgres/redis logs"
	@echo "    make db-ps        - Show container status"
	@echo ""
	@echo "  Bot in Docker:"
	@echo "    make bot-up       - Build (if needed) and start the bot"
	@echo "    make bot-down     - Stop the bot container"
	@echo "    make bot-logs     - Tail bot logs"
	@echo "    make bot-rebuild  - Rebuild image and restart the bot"

# === Application ===

run:
	uv run python -m tg_order_bot

lint:
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

test-ci:
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest -v

check: lint test

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# === Database (Alembic) ===

migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision --autogenerate -m "$(m)"

# === Docker ===

db-up:
	docker compose up -d

db-down:
	docker compose down

db-reset:
	docker compose down -v

db-logs:
	docker compose logs -f

db-ps:
	docker compose ps

# === Bot in Docker ===

bot-up:
	docker compose up -d bot

bot-down:
	docker compose stop bot

bot-logs:
	docker compose logs -f bot

bot-rebuild:
	docker compose up -d --build bot
