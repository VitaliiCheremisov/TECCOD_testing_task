import os
from typing import Optional
from opensearchpy import OpenSearch

ALLOWED_CONTENT_TYPES = ["article", "blog", "news", "faq"]


def get_opensearch_client() -> OpenSearch:
    """
    Создает и возвращает клиент OpenSearch, подключаясь к кластеру по данным
    из переменных окружения:

    - OS_HOST (по умолчанию: "localhost") — хост OpenSearch
    - OS_PORT (по умолчанию: 9200) — порт OpenSearch
    - OS_USER (по умолчанию: "admin") — имя пользователя
    - OS_PASS (по умолчанию: "admin") — пароль

    В официальном Docker-образе безопасность включена по умолчанию, поэтому
    используется SSL-подключение с отключенной проверкой сертификатов
    (verify_certs=False) для локальной разработки.
    """
    host = os.getenv("OS_HOST", "localhost")
    port = int(os.getenv("OS_PORT", "9200"))
    user = os.getenv("OS_USER", "admin")
    password = os.getenv("OS_PASS", "admin")
    # Security is enabled by default in the official image; use SSL with disabled cert verification
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(user, password),
        use_ssl=True,
        verify_certs=False,
    )
    return client


def ensure_index(index_name: str) -> None:
    """
    Гарантирует наличие индекса с заданным именем и схемой.

    Если индекс не существует, создаёт его с настройками (1 шард, 0 реплик)
    и маппингом полей:
      - title: text — полнотекстовый поиск по заголовку
      - content: text — полнотекстовый поиск по содержимому
      - content_type: keyword — точное значение типа контента
    """
    client = get_opensearch_client()
    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "content_type": {"type": "keyword"},
            }
        },
    }
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, body=mapping)


def seed_documents(index_name: str) -> int:
    """
    Загружает тестовые документы в указанный индекс.

    Создаёт 5 документов разных типов (article, blog, news, faq) с русскими
    заголовками и содержимым для демонстрации поиска. Каждый документ
    индексируется с refresh=True для немедленной доступности при поиске.

    Возвращает количество успешно загруженных документов.
    """
    client = get_opensearch_client()
    documents = [
        {
            "title": "Новости компании",
            "content": "Наша компания запустила новый продукт для анализа данных.",
            "content_type": "news",
        },
        {
            "title": "Как пользоваться приложением",
            "content": "В этом руководстве мы расскажем, как начать работу шаг за шагом.",
            "content_type": "faq",
        },
        {
            "title": "Статья о поиске",
            "content": "Поисковые системы используют индексы для быстрого поиска по тексту.",
            "content_type": "article",
        },
        {
            "title": "Блог о продуктивности",
            "content": "Несколько советов о том, как повысить продуктивность на работе.",
            "content_type": "blog",
        },
        {
            "title": "FAQ: учетная запись",
            "content": "Частые вопросы о восстановлении пароля и настройке профиля.",
            "content_type": "faq",
        },
    ]
    indexed = 0
    for doc in documents:
        if doc["content_type"] not in ALLOWED_CONTENT_TYPES:
            continue
        client.index(index=index_name, body=doc, refresh=True)
        indexed += 1
    return indexed


def search_documents(index_name: str, query: str, content_type: Optional[str] = None):
    """
    Выполняет поиск документов в указанном индексе по ключевому слову.

    Параметры:
        index_name: имя индекса для поиска
        query: поисковый запрос (ключевое слово)
        content_type: опциональный фильтр по типу контента (article, blog, news, faq)

    Поиск выполняется по полям title (с весом 2) и content (вес 1).
    Результаты фильтруются по content_type если указан.
    Возвращает список словарей с полями title и snippet (первые 50 символов content).
    """
    client = get_opensearch_client()
    must_clauses = [
        {
            "multi_match": {
                "query": query,
                "fields": ["title^2", "content"],
                "type": "best_fields",
            }
        }
    ]
    filter_clauses = []
    if content_type:
        if content_type not in ALLOWED_CONTENT_TYPES:
            return []
        filter_clauses.append({"term": {"content_type": content_type}})
    body = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses,
            }
        },
        "_source": ["title", "content"],
        "size": 50,
    }
    resp = client.search(index=index_name, body=body)
    results = []
    for hit in resp.get("hits", {}).get("hits", []):
        source = hit.get("_source", {})
        title = source.get("title", "")
        content = source.get("content", "")
        snippet = content[:50]
        results.append({"title": title, "snippet": snippet})
    return results
