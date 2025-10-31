## Telegram Table Status — бот для получения данных из Google-таблиц

Бот по идентификатору строки ищет запись в Google Spreadsheet и возвращает заданные столбцы. Хранит пользовательские настройки (текущий источник данных и его параметры) в Redis.

### Возможности
- Поиск строки по значению в указанной колонке и вывод выбранных колонок
- Настойка неограниченного количества источников именнованных источников данных

## Переменные окружения
- TELEGRAM_TOKEN — токен Telegram бота (обязательно)
- GSA_FILE — путь к JSON-файлу сервисного аккаунта Google (обязательно)
- REDIS_HOST — хост Redis (по умолчанию `redis` в docker-compose, локально может быть `localhost`)
- REDIS_PORT — порт Redis (по умолчанию `6379`)
- REDIS_PASSWORD — пароль Redis (необязательно)

## Запуск

### 1) Docker Compose (рекомендуется)
1. Скопируйте переменные окружения:
   ```bash
   cp env.template .env
   # отредактируйте .env согласно вашему окружению
   ```
2. Запустите:
   ```bash
   docker-compose up -d --build
   ```
3. Просмотр логов:
   ```bash
   docker-compose logs -f telegram-table-status-bot
   ```
4. Остановка:
   ```bash
   docker-compose down
   ```

## Настройка доступа Google
1. Создайте сервисный аккаунт в Google Cloud и выдайте ему доступ (как минимум «Читатель») к вашей Google Таблице.
2. Скачайте JSON-ключ сервисного аккаунта и положите в проект (или укажите абсолютный путь).
3. Передайте путь к файлу в переменной `GSA_FILE`.

## Команды Telegram-бота
Бот использует формат HTML для ответов, аргументы в командах:
- /start — Показать приветствие
- /help — Показать справку с перечнем команд
- /get_source — Показать мой текущий источник
- /set_source <source name> — Установить мой источник (имя ранее добавленного источника)
- /i <key> — Найти строку по значению в колонке поиска и вывести выбранные столбцы текущего источника
- /cfg_set_source <source name> <source url> <sheet_number> <seek column> <return columns> — Добавить/обновить источник данных
  - `source url` — ссылка на Google Spreadsheet
  - `sheet_number` — номер листа (1-базная нумерация)
  - `seek column` — номер колонки для поиска ключа (1-базная)
  - `return columns` — список колонок через запятую (например: `2,3,5`), 1-базные индексы
- /cfg_get_source <source name> — Показать конфигурацию источника

Пример использования:
```text
/cfg_set_source my https://docs.google.com/spreadsheets/d/XXXX 1 2 3,4,5
/set_source my
/i 12345
```

Ответ на `/i` содержит заголовок и выровненные по ширине имена колонок.

## Тесты
Пример интеграционного теста для Redis находится в `tests/test_redis_integration.py`.
Запуск тестов (при наличии pytest):
```bash
pytest -q
```

## Структура проекта
- `src/main.py` — входная точка, парсинг env/CLI и запуск бота
- `src/lib/tg_bot.py` — логика команд Telegram-бота
- `src/lib/gspread_reader.py` — доступ к Google Sheets
- `src/lib/options.py`, `src/lib/redis.py` — хранилище настроек в Redis
- `docker-compose.yml`, `Dockerfile` — контейнеризация

## Лицензия
MIT
