# tg-order-bot

🇷🇺 Русский · [🇬🇧 English](README.md)

Telegram-бот для приёма заказов с админ-панелью и выгрузкой в Google Sheets.

> ⚠️ **Проект в разработке.** Это портфолио-проект, находится в активной разработке.
> Полная документация с бизнес-ценностью, GIF-демо и инструкцией по деплою
> будет добавлена по завершении.

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
git clone https://github.com/<your-username>/tg-order-bot.git
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

## Статус проекта

🚧 **В разработке.** См. [Issues](https://github.com/<your-username>/tg-order-bot/issues) для дорожной карты.

## Лицензия

[MIT](LICENSE)
