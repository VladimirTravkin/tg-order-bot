# tg-order-bot

[🇷🇺 Русская версия](README.ru.md) · 🇬🇧 English

[![CI](https://github.com/VladimirTravkin/tg-order-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/VladimirTravkin/tg-order-bot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Telegram bot for accepting orders with an admin panel and Google Sheets export.

**Live demo:** [@vm13_tg_order_bot](https://t.me/vm13_tg_order_bot)

A full-featured Telegram bot for accepting orders: product catalog, shopping
cart, checkout flow, admin panel with order management, and one-click export
to Google Sheets.

## What it does

- 🛍 **Product catalog** — categories and product cards
- 🛒 **Shopping cart** — add, remove, view items
- 📝 **Order checkout** — name, phone, comment
- 🔧 **Admin panel** — view orders, change status, broadcast messages
- 🔔 **Notifications** — admin gets pinged on every new order
- 📊 **Google Sheets export** — one-click export of orders

## Tech stack

- **Python 3.11+**
- **aiogram 3** — Telegram Bot API framework
- **PostgreSQL** + **SQLAlchemy 2.0** (async) + **asyncpg**
- **Redis** — FSM state storage
- **pydantic-settings** — configuration
- **uv** — dependency management
- **Ruff** — linter and formatter
- **pytest** — testing
- **Docker** + **docker-compose** — local infrastructure and deployment

## Quick start

> Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and [Docker](https://www.docker.com/products/docker-desktop/).

```bash
# 1. Clone the repository
git clone https://github.com/VladimirTravkin/tg-order-bot.git
cd tg-order-bot

# 2. Install dependencies
uv sync

# 3. Set up environment
cp .env.example .env
# Edit .env: set BOT_TOKEN (from @BotFather) and ADMIN_IDS (from @userinfobot)

# 4. Start PostgreSQL and Redis
make db-up

# 5. Apply database migrations
make migrate

# 6. Run the bot
make run
```

## Local development

### Infrastructure

PostgreSQL 16 and Redis 7 run in Docker containers:

```bash
make db-up      # start containers
make db-ps      # check status (should be "healthy")
make db-logs    # tail logs
make db-down    # stop (data preserved)
make db-reset   # stop and WIPE all data
```

### Quality checks

```bash
make lint       # ruff check
make format     # ruff format
make test       # pytest
make check      # lint + test (before commit)
```

### Database migrations

```bash
make migrate                     # apply all pending migrations
make migration m="add users"     # create new migration
```

### Running in Docker

The whole stack (Postgres + Redis + bot) can run in Docker:

```bash
# Build the bot image and start it along with infrastructure
make bot-up

# Tail bot logs
make bot-logs

# Stop the bot (infrastructure keeps running)
make bot-down

# Rebuild after code changes
make bot-rebuild
```

Alternatively, with plain Docker Compose:

```bash
docker compose up -d         # start postgres + redis only
docker compose up -d bot     # add the bot
docker compose ps            # check status
docker compose logs -f bot   # tail bot logs
docker compose down          # stop everything (data preserved)
```

> **Note:** The bot only runs on a machine that has a real `BOT_TOKEN` in `.env`.
> When someone clones this repository, they must create their own bot via
> [@BotFather](https://t.me/BotFather) and put the new token into their `.env`.

## Project status

✅ **Live** — the bot is deployed on a VPS and running 24/7.

- ✅ 46 tests passing
- ✅ Docker + docker-compose
- ✅ GitHub Actions CI
- ✅ Google Sheets export

See [Issues](https://github.com/VladimirTravkin/tg-order-bot/issues) for the roadmap.

## License

[MIT](LICENSE)
