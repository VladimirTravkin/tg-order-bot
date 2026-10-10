# tg-order-bot

🇷🇺 Русский · [🇬🇧 English](README.md)

Telegram-бот для приёма заказов с админ-панелью и выгрузкой в Google Sheets.

**Живой бот:** [@vm13_tg_order_bot](https://t.me/vm13_tg_order_bot)

Полнофункциональный Telegram-бот для приёма заказов: каталог товаров, корзина,
оформление заказа, админ-панель с управлением заказами и экспорт в Google Sheets.

## Что умеет

- 🛍 **Каталог товаров** — категории и карточки товаров
- 🛒 **Корзина** — добавление, удаление, просмотр
- 📝 **Оформление заказа** — имя, телефон, комментарий
- 🔧 **Админ-панель** — просмотр заказов, смена статуса, рассылка
- 🔔 **Уведомления** — админ получает сообщение о каждом новом заказе
- 📊 **Выгрузка в Google Sheets** — экспорт заказов одной кнопкой

## Стек

- **Python 3.11+**
- **aiogram 3** — фреймворк для Telegram Bot API
- **PostgreSQL** + **SQLAlchemy 2.0** (async) + **asyncpg**
- **Redis** — хранение FSM-состояний
- **pydantic-settings** — конфигурация
- **uv** — управление зависимостями
- **Ruff** — линтер и форматтер
- **pytest** — тестирование
- **Docker** + **docker-compose** — локальная инфраструктура и деплой

## Быстрый старт

> Требуется Python 3.11+, [uv](https://docs.astral.sh/uv/) и [Docker](https://www.docker.com/products/docker-desktop/).

```bash
# 1. Клонировать репозиторий
git clone https://github.com/VladimirTravkin/tg-order-bot.git
cd tg-order-bot

# 2. Установить зависимости
uv sync

# 3. Настроить окружение
cp .env.example .env
# Отредактировать .env: указать BOT_TOKEN (от @BotFather) и ADMIN_IDS (от @userinfobot)

# 4. Поднять PostgreSQL и Redis
make db-up

# 5. Применить миграции БД
make migrate

# 6. Запустить бота
make run
```

## Локальная разработка

### Инфраструктура

PostgreSQL 16 и Redis 7 работают в Docker-контейнерах:

```bash
make db-up      # поднять контейнеры
make db-ps      # проверить статус (должно быть "healthy")
make db-logs    # смотреть логи
make db-down    # остановить (данные сохраняются)
make db-reset   # остановить и УДАЛИТЬ все данные
```

### Проверки качества

```bash
make lint       # ruff check
make format     # ruff format
make test       # pytest
make check      # lint + test (перед коммитом)
```

### Миграции БД

```bash
make migrate                     # применить все миграции
make migration m="add users"     # создать новую миграцию
```

### Запуск в Docker

Весь стек (PostgreSQL + Redis + бот) можно запустить в Docker:

```bash
# Собрать образ бота и запустить его вместе с инфраструктурой
make bot-up

# Смотреть логи бота
make bot-logs

# Остановить бота (инфраструктура продолжает работать)
make bot-down

# Пересобрать после изменения кода
make bot-rebuild
```

Альтернатива — напрямую через Docker Compose:

```bash
docker compose up -d         # только postgres + redis
docker compose up -d bot     # добавить бота
docker compose ps            # проверить статус
docker compose logs -f bot   # логи бота
docker compose down          # остановить всё (данные сохраняются)
```

> **Важно:** бот работает только на машине, где в `.env` указан **реальный** `BOT_TOKEN`.
> Тот, кто клонирует репозиторий, должен создать **своего** бота через
> [@BotFather](https://t.me/BotFather) и вписать **свой** токен в `.env`.

## Статус проекта

✅ **Работает** — бот развёрнут на VPS и работает 24/7.

- ✅ 46 тестов
- ✅ Docker + docker-compose
- ✅ GitHub Actions CI
- ✅ Google Sheets export

См. [Issues](https://github.com/VladimirTravkin/tg-order-bot/issues) для дорожной карты.

## Лицензия

[MIT](LICENSE)
