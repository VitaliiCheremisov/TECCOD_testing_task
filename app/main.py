import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from .opensearch_client import (
    ensure_index,
    search_documents,
    seed_documents,
    ALLOWED_CONTENT_TYPES,
)

app = FastAPI(title="OpenSearch Demo")


def get_index_name() -> str:
    """
    Возвращает имя индекса из переменной окружения INDEX_NAME.
    По умолчанию использует 'articles_index'.
    """
    return os.getenv("INDEX_NAME", "articles_index")


@app.get("/init")
def init_index() -> dict:
    """
    Инициализирует индекс OpenSearch с заданной схемой.
    
    Создаёт индекс если он не существует, с полями:
    - title (text)
    - content (text) 
    - content_type (keyword)
    
    Возвращает статус операции и имя созданного индекса.
    """
    index_name = get_index_name()
    ensure_index(index_name)
    return {"status": "ok", "index": index_name}


@app.post("/seed")
def seed() -> dict:
    """
    Загружает тестовые документы в индекс.
    
    Создаёт 5 документов разных типов (article, blog, news, faq)
    с русскими заголовками и содержимым для демонстрации поиска.
    
    Возвращает количество успешно загруженных документов.
    """
    index_name = get_index_name()
    ensure_index(index_name)
    count = seed_documents(index_name)
    return {"indexed": count}


@app.get("/search")
def search(q: str = Query(..., min_length=1), content_type: Optional[str] = None) -> List[dict]:
    """
    Выполняет поиск документов по ключевому слову с опциональной фильтрацией.
    
    Параметры:
        q: поисковый запрос (минимум 1 символ)
        content_type: опциональный фильтр по типу контента
        
    Поиск выполняется по полям title и content.
    Поле title имеет больший вес при ранжировании результатов.
    Возвращает список документов с заголовком и сниппетом (первые 50 символов).
    
    Допустимые значения content_type: article, blog, news, faq
    """
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"content_type must be one of {ALLOWED_CONTENT_TYPES}")
    index_name = get_index_name()
    ensure_index(index_name)
    return search_documents(index_name, q, content_type)
