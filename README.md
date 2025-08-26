# TECCOD_testing_task

## Запуск (Docker Compose)

1. Требования:
   - Docker, Docker Compose

2. Запуск сервисов:
```bash
docker compose up -d --build
```

Будут подняты:
- OpenSearch (https, порт `9200`, пользователь `admin`, пароль в `docker-compose.yml`)
- FastAPI приложение (http://localhost:8000)

3. Инициализация индекса и загрузка тестовых данных:
```bash
curl http://localhost:8000/init
curl -X POST http://localhost:8000/seed
```

4. Поиск с фильтром `content_type` (radio):
```bash
# пример: поиск по слову "Поисковые" и фильтр только article
curl "http://localhost:8000/search?q=%D0%9F%D0%BE%D0%B8%D1%81%D0%BA%D0%BE%D0%B2%D1%8B%D0%B5&content_type=article"
```

## Детали реализации

- Индекс `articles_index` с полями:
  - `title`: text
  - `content`: text
  - `content_type`: keyword (допустимые значения: `article`, `blog`, `news`, `faq`)

- Эндпоинты FastAPI:
  - `GET /init` — создать индекс при отсутствии
  - `POST /seed` — загрузить 3–5 документов
  - `GET /search?q=...&content_type=...` — поиск по `title` и `content`, фильтр по `content_type`

## Переменные окружения приложения

Задаются в `docker-compose.yml`:
- `OS_HOST`, `OS_PORT`, `OS_USER`, `OS_PASS`, `INDEX_NAME`
