# Naive Auction Bot

Простой Telegram-бот для проведения аукционов с SQLite персистентностью данных.

## Описание

Это standalone сервис для проведения онлайн-аукционов через Telegram. Бот позволяет:
- Просматривать список лотов
- Делать ставки (автоматическое повышение или индивидуальная ставка)
- Отслеживать свои ставки
- Получать уведомления о перебитии ставок
- Админ-функции для управления аукционом

## Технологии

- Python 3.11
- python-telegram-bot 20.7
- PostgreSQL (через asyncpg)
- Docker

## Локальный запуск

### Вариант 1: С Docker Compose (рекомендуется)

1. Создайте `.env` файл на основе `.env.example`:
```bash
cp .env.example .env
```

2. Отредактируйте `.env` и укажите ваши данные:
```
TG_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
CREATOR_ID=YOUR_TELEGRAM_USER_ID
```

3. Запустите проект:
```bash
docker-compose up -d
```

4. Просмотр логов:
```bash
docker-compose logs -f bot
```

5. Остановка:
```bash
docker-compose down
```

**Преимущества Docker Compose:**
- ✅ Не нужно устанавливать PostgreSQL локально
- ✅ Полная изоляция окружения
- ✅ Автоматическая настройка связи между сервисами
- ✅ Персистентность данных через Docker volumes

### Вариант 2: Без Docker

**Требования:**
- Python 3.11+
- PostgreSQL 12+
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

**Установка:**

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте `.env` файл на основе `.env.example`:
```bash
cp .env.example .env
```

3. Отредактируйте `.env` и укажите ваши данные:
```
TG_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
CREATOR_ID=YOUR_TELEGRAM_USER_ID
DATABASE_URL=postgresql://user:password@localhost:5432/auction_db
```

4. Создайте базу данных PostgreSQL:
```bash
createdb auction_db
```

5. Запустите бота:
```bash
python bot.py
```

Таблицы в базе данных будут созданы автоматически при первом запуске.

## Деплой на Railway

### Шаг 1: Подготовка

1. Создайте аккаунт на [Railway.app](https://railway.app/)
2. Убедитесь, что ваш репозиторий находится на GitHub

### Шаг 2: Создание проекта

1. Войдите в Railway и нажмите "New Project"
2. Выберите "Deploy from GitHub repo"
3. Выберите ваш репозиторий
4. Railway автоматически обнаружит Dockerfile

### Шаг 3: Добавление PostgreSQL

1. В вашем проекте нажмите "New" → "Database" → "Add PostgreSQL"
2. Railway автоматически создаст базу данных и установит переменную окружения `DATABASE_URL`

### Шаг 4: Настройка переменных окружения

1. Перейдите в раздел "Variables" вашего сервиса с ботом
2. Добавьте следующие переменные:
   - `TG_BOT_TOKEN` - ваш токен бота от BotFather
   - `CREATOR_ID` - ваш Telegram User ID (опционально, по умолчанию 1337)
3. `DATABASE_URL` будет добавлена автоматически после создания PostgreSQL

### Шаг 5: Деплой

1. Railway автоматически задеплоит ваш сервис после настройки
2. Проверьте логи в разделе "Deployments" → выберите последний деплой → "View Logs"
3. Вы должны увидеть сообщение: `Bot started successfully`

### Переменные окружения Railway

**Обязательные:**
- `TG_BOT_TOKEN` - токен бота от BotFather
- `DATABASE_URL` - URL подключения к PostgreSQL (устанавливается автоматически)

**Опциональные:**
- `CREATOR_ID` - ваш Telegram User ID для админ-функций (по умолчанию 1337)

**Системные (не требуются):**
- `PORT` - не используется (бот работает через polling, а не webhook)

## Команды бота

### Для пользователей:
- `/start` - начать работу с ботом
- `/auction` - информация об аукционе
- `/info` - информация о боте
- Кнопки в меню:
  - "Показать лоты" - список всех лотов
  - "Показать свои ставки" - ваши текущие ставки

### Для администратора:
- `/delete <bid_id>` - удалить ставку (требуется CREATOR_ID)

## Структура данных

### База данных PostgreSQL

Таблица `bids`:
| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL | Автоинкремент, первичный ключ |
| lot_id | INTEGER | ID лота |
| user_id | BIGINT | Telegram User ID |
| amount | DECIMAL(10, 2) | Сумма ставки |
| created_at | TIMESTAMP | Время создания |

### Лоты

Лоты определены в коде (`bot.py`, переменная `auction_lots`) и включают:
- `title` - название лота
- `description` - описание
- `starting_price` - начальная цена
- `min_bid_step` - минимальный шаг ставки
- `image_url` - ссылка на изображение

**Важно:** Для корректной работы Telegram API необходимо использовать прямые ссылки на изображения (например, `https://i.imgur.com/XXX.jpg`), а не ссылки на альбомы (`https://imgur.com/a/XXX`). Текущие ссылки в коде указывают на альбомы и требуют обновления для работы функции отправки изображений.

## Архитектура

```
naive-auction-bot/
├── bot.py              # Основная логика бота
├── database.py         # Слой работы с PostgreSQL
├── requirements.txt    # Python зависимости
├── Dockerfile          # Конфигурация Docker
├── docker-compose.yml  # Оркестрация Docker контейнеров
├── .dockerignore       # Игнорируемые файлы
├── .env.example        # Шаблон конфигурации
├── railway.toml        # Конфигурация Railway
├── QUICKSTART.md       # Быстрый старт
└── README.md           # Этот файл
```

## Graceful Shutdown

Бот корректно обрабатывает сигналы `SIGINT` и `SIGTERM`, что позволяет ему:
- Завершить обработку текущих сообщений
- Закрыть соединения с Telegram API
- Закрыть соединение с БД

Это важно для Railway, который отправляет `SIGTERM` при остановке контейнера.

## Troubleshooting

### Docker Compose

**Бот не запускается:**
```bash
docker-compose logs bot
```
- Проверьте, что `.env` файл содержит `TG_BOT_TOKEN`
- Убедитесь, что PostgreSQL контейнер запущен: `docker-compose ps`

**PostgreSQL не отвечает:**
```bash
docker-compose restart postgres
docker-compose logs postgres
```

**Очистка и пересоздание:**
```bash
docker-compose down -v
docker-compose up -d --build
```

### Общие проблемы

**Бот не запускается:**
- Проверьте логи: убедитесь, что `TG_BOT_TOKEN` и `DATABASE_URL` установлены
- Проверьте валидность токена через BotFather
- Убедитесь, что PostgreSQL база данных создана и доступна

**Ошибка подключения к базе данных:**
- Проверьте правильность `DATABASE_URL`
- Убедитесь, что PostgreSQL сервис запущен
- Проверьте сетевую доступность между сервисами

**Уведомления не приходят:**
- Пользователь должен хотя бы раз написать боту
- Проверьте логи на ошибки отправки сообщений

## Лицензия

Часть проекта Solguficky Hub.

