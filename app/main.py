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
    return os.getenv("INDEX_NAME", "articles_index")


@app.get("/init")
def init_index() -> dict:
    index_name = get_index_name()
    ensure_index(index_name)
    return {"status": "ok", "index": index_name}


@app.post("/seed")
def seed() -> dict:
    index_name = get_index_name()
    ensure_index(index_name)
    count = seed_documents(index_name)
    return {"indexed": count}


@app.get("/search")
def search(q: str = Query(..., min_length=1), content_type: Optional[str] = None) -> List[dict]:
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"content_type must be one of {ALLOWED_CONTENT_TYPES}")
    index_name = get_index_name()
    ensure_index(index_name)
    return search_documents(index_name, q, content_type)
