# Быстрый старт

## Docker Compose (рекомендуется)

```bash
cp .env.example .env
# Отредактируйте .env и добавьте TG_BOT_TOKEN и CREATOR_ID
docker-compose up -d
docker-compose logs -f bot
```

## Локально (без Docker)

```bash
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env и добавьте TG_BOT_TOKEN и DATABASE_URL
createdb auction_db
python bot.py
```

## Railway

1. Создайте новый проект на [Railway.app](https://railway.app)
2. Подключите GitHub репозиторий
3. Добавьте PostgreSQL: "New" → "Database" → "Add PostgreSQL"
4. Добавьте переменные окружения в сервис с ботом:
   - `TG_BOT_TOKEN` = ваш токен от @BotFather
   - `CREATOR_ID` = ваш Telegram User ID (опционально)
   - `DATABASE_URL` = устанавливается автоматически
5. Deploy!

## Получение Telegram Bot Token

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

## Получение вашего Telegram User ID

1. Откройте [@userinfobot](https://t.me/userinfobot)
2. Отправьте `/start`
3. Скопируйте ваш ID

