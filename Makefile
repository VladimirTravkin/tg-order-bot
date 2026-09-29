.PHONY: help run lint format test check clean

help:
	@echo "Available commands:"
	@echo "  make run     - Run the Telegram bot"
	@echo "  make lint    - Check code with ruff"
	@echo "  make format  - Format code with ruff"
	@echo "  make test    - Run tests with pytest"
	@echo "  make check   - Run lint + test (before commit)"
	@echo "  make clean   - Remove caches and build artifacts"

run:
	uv run python -m tg_order_bot

lint:
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

check: lint test

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
