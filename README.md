# tg-order-bot

[🇷🇺 Русская версия](README.ru.md) · 🇬🇧 English

Telegram bot for accepting orders with an admin panel and Google Sheets export.

> ⚠️ **Work in progress.** This is a portfolio project under active development.
> Full documentation with business value, demo GIF, and deployment guide
> will be added upon completion.

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
- **Docker** + **docker-compose** — containerization

## Quick start

> Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/) installed.

```bash
# Clone the repository
git clone https://github.com/<your-username>/tg-order-bot.git
cd tg-order-bot

# Install dependencies
uv sync

# Copy environment template and fill in your values
cp .env.example .env

# Run the bot
uv run python -m tg_order_bot
```

## Project status

🚧 **In development.** See [Issues](https://github.com/<your-username>/tg-order-bot/issues) for the roadmap.

## License

[MIT](LICENSE)
