# Архитектура tg-order-bot

Документ описывает фактическую архитектуру проекта: структуру модулей,
модель данных, поток оформления заказа и схему деплоя.

## Общий подход

Проект организован по **feature-based** принципу: код группируется по доменам
(каталог, корзина, заказы, админка), а не по типам файлов. Каждый домен
изолирован — изменения в каталоге не задевают корзину.

## Структура модулей

```
src/tg_order_bot/
├── __init__.py
├── __main__.py          # точка входа: запуск polling
├── config.py            # настройки через pydantic-settings
├── bot.py               # создание Bot и Dispatcher, регистрация роутеров
├── database/
│   ├── base.py          # DeclarativeBase
│   ├── session.py       # async engine, sessionmaker
│   └── models/          # SQLAlchemy-модели по доменам
├── common/
│   ├── middlewares/     # db session, throttling, admin filter
│   ├── keyboards/       # общие клавиатуры (отмена, назад)
│   ├── handlers.py      # /start, /help
│   └── labels.py        # русские названия статусов заказа
├── catalog/             # каталог товаров
│   ├── handlers.py
│   ├── keyboards.py
│   ├── callbacks.py
│   ├── service.py
├── cart/                # корзина
│   ├── handlers.py
│   ├── keyboards.py
│   └── service.py
├── orders/              # оформление заказов
│   ├── handlers.py
│   ├── keyboards.py
│   ├── service.py
│   └── states.py        # OrderFSM
├── admin/               # админ-панель
│   ├── handlers.py
│   ├── keyboards.py
│   ├── service.py
└── infrastructure/
    └── google_sheets.py # выгрузка заказов
```

## Ответственности модулей

| Модуль | Отвечает за | НЕ знает про |
|---|---|---|
| `config.py` | Загрузка `.env`, валидация настроек | Бизнес-логику |
| `bot.py` | Создание Bot/Dispatcher, регистрация роутеров | Детали хендлеров |
| `database/` | Подключение к PostgreSQL, модели, сессии | Telegram-логику |
| `common/labels.py` | Русские названия статусов заказа | Telegram, БД |
| `catalog/` | Показ категорий и товаров (с фото) | Заказы, корзину |
| `cart/` | Добавление/удаление/просмотр корзины | Оформление заказа |
| `orders/` | FSM оформления, сохранение заказа, уведомление админу | Каталог, админку |
| `admin/` | Просмотр заказов, смена статуса, рассылка | Клиентские сценарии |
| `infrastructure/google_sheets.py` | Экспорт в Google Sheets | Telegram, БД |

## Модель данных

Шесть таблиц, связанных по доменам:

```
users (1) ───< cart_items >─── (1) products
  │                                │
  │                                │ category_id
  │                                ▼
  │                            categories
  │
  └──< orders ───< order_items >─── (0..1) products
```

### users

| Поле | Тип | Примечание |
|---|---|---|
| `id` | int, PK | |
| `telegram_id` | BigInteger, unique | Может превышать 32-битный int |
| `username` | str(64), nullable | |
| `full_name` | str(255) | |
| `phone` | str(20), nullable | Заполняется при первом заказе |
| `created_at`, `updated_at` | datetime(tz) | `TimestampMixin` |

### categories

| Поле | Тип | Примечание |
|---|---|---|
| `id` | int, PK | |
| `name` | str(100) | |
| `description` | text, nullable | |
| `sort_order` | int, default 0 | |
| `is_active` | bool, default true | |

### products

| Поле | Тип | Примечание |
|---|---|---|
| `id` | int, PK | |
| `category_id` | FK → categories, CASCADE | |
| `name` | str(200) | |
| `description` | text, nullable | |
| `price` | Numeric(10, 2) | |
| `photo_url` | str(500), nullable | `file_id` Telegram или https-URL |
| `sort_order` | int, default 0 | |
| `is_active` | bool, default true | |

### cart_items

| Поле | Тип | Примечание |
|---|---|---|
| `id` | int, PK | |
| `user_id` | FK → users, CASCADE | |
| `product_id` | FK → products, CASCADE | |
| `quantity` | int, > 0 | Unique по `(user_id, product_id)` |

### orders

| Поле | Тип | Примечание |
|---|---|---|
| `id` | int, PK | |
| `user_id` | FK → users, CASCADE | |
| `status` | enum (StrEnum) | `new / confirmed / paid / shipped / done / cancelled` |
| `total` | Numeric(10, 2) | Снапшот на момент оформления |
| `customer_name` | str(255) | Снапшот |
| `customer_phone` | str(20) | Снапшот |
| `comment` | text, nullable | |

### order_items

| Поле | Тип | Примечание |
|---|---|---|
| `id` | int, PK | |
| `order_id` | FK → orders, CASCADE | |
| `product_id` | FK → products, SET NULL, nullable | Товар мог быть удалён |
| `product_name` | str(200) | Снапшот |
| `product_price` | Numeric(10, 2) | Снапшот |
| `quantity` | int | |

### Ключевые решения по модели данных

- **Снапшоты в `orders` и `order_items`.** Имя, телефон, цена и название
  товара сохраняются на момент заказа. Последующее изменение профиля,
  переименование или удаление товара не искажает историю.
- **`lazy="raise"` на критичных связях.** Защита от случайных N+1-запросов
  и неявных подгрузок — разработчик обязан явно указать `selectinload`.
- **`OrderStatus` через `StrEnum` и `native_enum=False`.** Статус хранится
  как строка — переносимо между СУБД, легко читается в Google Sheets.
- **Каскады.** `CASCADE` на `user → orders / cart_items`, `SET NULL` на
  `product → order_items`, чтобы удаление товара не ломало историю.

## Поток данных: оформление заказа

```
Клиент в Telegram
    │
    ▼
handlers (orders/) ── FSM-состояния в Redis (OrderFSM)
    │
    ▼
service.py (бизнес-логика)
    │
    ▼
database/ (SQLAlchemy + asyncpg) ──► PostgreSQL
    │
    ├─► Уведомление админу (bot.send_message)
    │   └─► статус через common/labels.py (русские названия)
    └─► Подтверждение клиенту
```

## FSM-сценарии

В проекте один FSM — `orders/states.py`, описывающий пошаговое оформление
заказа:

1. Запрос имени (с кнопкой «Оставить как есть» — подставляет имя из Telegram)
2. Запрос телефона
3. Запрос комментария (необязательно, кнопка «Пропустить»)
4. Подтверждение и сохранение заказа

Состояния хранятся в Redis (см. `REDIS_HOST`, `REDIS_DB` в `.env`) — не
теряются при перезапуске бота.

## Каталог и навигация

Особенность UI: карточка товара — это **сообщение с фото** (`answer_photo`),
а списки категорий/товаров — **текстовые сообщения**. Из-за этого переходы
«фото → текст» и «текст → фото» нельзя делать через `edit_text` / `edit_media`.

Решение: в `catalog/handlers.py` используется стратегия **replace** —
текущее сообщение удаляется, отправляется новое:

- `_replace_with_text()` — удалить + `answer(text)`
- `_replace_with_product_card()` — удалить + `answer_photo(...)` или `answer(text)`

Плюс: работает стабильно с любыми типами сообщений. Минус: нет плавности
`edit_text` (сообщение «прыгает» вниз).

## Google Sheets

Экспорт реализован в `infrastructure/google_sheets.py`:

- Авторизация через **Service Account** (`GOOGLE_CREDENTIALS_PATH`).
- Целевая таблица задаётся `GOOGLE_SPREADSHEET_ID`. Если переменная пуста —
  кнопка выгрузки отключена.
- Статусы заказов выгружаются **на русском** через `common/labels.py`
  (`test_labels.py` гарантирует соответствие).

## Тесты

46 тестов в `tests/`:

| Файл | Что покрывает |
|---|---|
| `test_models.py` | ORM-модели, связи, каскады |
| `test_database.py` | Подключение к БД, сессии |
| `test_cart_service.py` | Логика корзины |
| `test_orders_service.py` | Логика заказов |
| `test_admin_service.py` | Логика админ-панели |
| `test_common_services.py` | Общие сервисы |
| `test_google_sheets.py` | Выгрузка в Sheets |
| `test_labels.py` | Русские названия статусов |
| `test_smoke.py` | Smoke-тест импортов |

Запуск: `make test` (или `uv run pytest`).

## Деплой

Стек разворачивается на VPS через Docker Compose. Три контейнера:

| Контейнер | Образ | Назначение |
|---|---|---|
| `tg_order_bot_app` | собирается из `Dockerfile` | сам бот (polling) |
| `tg_order_bot_postgres` | `postgres:16-alpine` | база данных |
| `tg_order_bot_redis` | `redis:7-alpine` | FSM-состояния |

Данные сохраняются в Docker-волюмах `postgres_data` и `redis_data` — не
теряются при `docker compose down`.

### Типовой сценарий деплоя

```bash
git clone https://github.com/VladimirTravkin/tg-order-bot.git /opt/tg-order-bot
cd /opt/tg-order-bot
cp .env.example .env   # заполнить BOT_TOKEN, ADMIN_IDS, ...
docker compose up -d
docker compose exec bot alembic upgrade head
```

Секреты Google Sheets хранятся в `secrets/google-credentials.json` (права
`644`, файл не коммитится — см. `.gitignore`).

## Ключевые технологические решения

| Решение | Обоснование |
|---|---|
| **aiogram 3** | Актуальная версия, async-first, роутеры, middleware |
| **PostgreSQL + SQLAlchemy 2.0** | Надёжность, типизация, async-драйвер asyncpg |
| **Redis для FSM** | Состояния не теряются при рестарте бота |
| **pydantic-settings** | Типизированный конфиг, валидация на старте |
| **uv** | Скорость установки, lock-файл, единый инструмент |
| **feature-based структура** | Изоляция доменов, лёгкость навигации |
| **Middleware для DB-сессии** | Сессия живёт один апдейт, автоматом закрывается |
| **Снапшоты в заказах** | История не ломается при изменении каталога |
| **Стратегия replace в навигации** | Стабильная работа с сообщениями «текст ↔ фото» |
