from __future__ import annotations

from pymongo.collection import Collection

from src.embedder import GeminiEmbedder


def _vector_search(
    *,
    collection: Collection,
    query_embedding: list[float],
    index_name: str,
    limit: int,
    num_candidates: int,
) -> list[dict[str, Any]]:
    vector_stage = {
        "index": index_name,
        "path": "embedding",
        "queryVector": query_embedding,
        "numCandidates": num_candidates,
        "limit": limit,
    }

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
