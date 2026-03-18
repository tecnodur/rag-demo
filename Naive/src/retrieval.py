from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from typing import Any

from pymongo.collection import Collection

from src.embedder import GeminiEmbedder


def normalize_region(value: str | None) -> str | None:
    return value.upper() if value else None


def normalize_status(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().capitalize()


def normalize_doc_type(value: str | None) -> str | None:
    return value.lower() if value else None


def _to_iso_date_or_empty(value: str | None) -> str:
    if not value:
        return ""
    return str(date.fromisoformat(value))


def build_filter(
    *,
    region: str | None = None,
    status: str | None = None,
    doc_type: str | None = None,
) -> dict[str, Any] | None:
    clauses = []
    if region:
        clauses.append({"region": {"$eq": normalize_region(region)}})
    if status:
        clauses.append({"status": {"$eq": normalize_status(status)}})
    if doc_type:
        clauses.append({"doc_type": {"$eq": normalize_doc_type(doc_type)}})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _vector_search(
    *,
    collection: Collection,
    query_embedding: list[float],
    index_name: str,
    limit: int,
    num_candidates: int,
    pre_filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    vector_stage: dict[str, Any] = {
        "index": index_name,
        "path": "embedding",
        "queryVector": query_embedding,
        "numCandidates": num_candidates,
        "limit": limit,
    }
    if pre_filter:
        vector_stage["filter"] = pre_filter

    pipeline = [
        {"$vectorSearch": vector_stage},
        {
            "$project": {
                "_id": 0,
                "chunk_id": 1,
                "parent_document_id": 1,
                "source_file": 1,
                "title": 1,
                "chunk_text": 1,
                "chunk_index": 1,
                "region": 1,
                "status": 1,
                "version": 1,
                "effective_date": 1,
                "owner_team": 1,
                "audience": 1,
                "doc_type": 1,
                "tags": 1,
                "short_description": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    return list(collection.aggregate(pipeline))


def retrieve_naive(
    *,
    collection: Collection,
    embedder: GeminiEmbedder,
    index_name: str,
    question: str,
    limit: int = 6,
    num_candidates: int = 40,
) -> list[dict[str, Any]]:
    query_embedding = embedder.embed_text(question)
    return _vector_search(
        collection=collection,
        query_embedding=query_embedding,
        index_name=index_name,
        limit=limit,
        num_candidates=num_candidates,
    )


def prefer_latest_version(chunks: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        key = (chunk["title"], chunk["doc_type"])
        grouped[key].append(chunk)

    reranked: list[dict[str, Any]] = []
    for group in grouped.values():
        reranked.extend(
            sorted(
                group,
                key=lambda chunk: (
                    normalize_status(chunk.get("status")) == "Active",
                    int(chunk.get("version", 0)),
                    _to_iso_date_or_empty(chunk.get("effective_date")),
                    float(chunk.get("score", 0.0)),
                ),
                reverse=True,
            )
        )

    return sorted(
        reranked,
        key=lambda chunk: (
            normalize_status(chunk.get("status")) == "Active",
            int(chunk.get("version", 0)),
            _to_iso_date_or_empty(chunk.get("effective_date")),
            float(chunk.get("score", 0.0)),
        ),
        reverse=True,
    )


def retrieve_structured(
    *,
    collection: Collection,
    embedder: GeminiEmbedder,
    index_name: str,
    question: str,
    region: str | None = None,
    status: str | None = None,
    doc_type: str | None = None,
    limit: int = 6,
    num_candidates: int = 40,
) -> list[dict[str, Any]]:
    query_embedding = embedder.embed_text(question)
    pre_filter = build_filter(region=region, status=status, doc_type=doc_type)
    hits = _vector_search(
        collection=collection,
        query_embedding=query_embedding,
        index_name=index_name,
        limit=limit,
        num_candidates=num_candidates,
        pre_filter=pre_filter,
    )
    return prefer_latest_version(hits)
