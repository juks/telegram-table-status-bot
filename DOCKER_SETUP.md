# Docker Setup для SpreadsheetBot

## Конфигурация

1. Скопируйте файл `env.template` в `.env` и заполните необходимые переменные:
```bash
cp env.template .env
```

2. Отредактируйте `.env` файл:
```bash
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Google Service Account
GSA_FILE=telegram-table-status-fe3f4f8e8a0b.json

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# Optional: Redis password (leave empty for no password)
# REDIS_PASSWORD=your_redis_password_here
```

## Запуск

### С помощью Docker Compose (рекомендуется)

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f telegram-whitelist-bot

# Остановка
docker-compose down
```

### Отдельные команды

```bash
# Только Redis
docker-compose up redis

# Только бот (требует запущенный Redis)
docker-compose up telegram-whitelist-bot
```

## Сервисы

### Redis
- **Образ**: `redis:7-alpine`
- **Порт**: 6379
- **Данные**: сохраняются в volume `redis_data`
- **Конфигурация**: AOF включен для надежности

### Telegram Bot
- **Зависимости**: Redis
- **Переменные окружения**: читаются из `.env`
- **Данные**: сохраняются в volume `data`

## Volumes

- `data`: данные бота
- `redis_data`: данные Redis

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_TOKEN` | Токен Telegram бота | **обязательно** |
| `GSA_FILE` | Путь к файлу сервисного аккаунта Google | **обязательно** |
| `REDIS_HOST` | Хост Redis сервера | `redis` |
| `REDIS_PORT` | Порт Redis сервера | `6379` |
| `REDIS_PASSWORD` | Пароль Redis (опционально) | пустой |

## Устранение неполадок

### Redis не запускается
```bash
# Проверьте логи Redis
docker-compose logs redis

# Перезапустите Redis
docker-compose restart redis
```

### Бот не может подключиться к Redis
```bash
# Проверьте, что Redis запущен
docker-compose ps

# Проверьте переменные окружения
docker-compose exec telegram-whitelist-bot env | grep REDIS
```

### Очистка данных
```bash
# Остановить и удалить все контейнеры и volumes
docker-compose down -v

# Пересобрать образы
docker-compose build --no-cache
```
