from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pymongo import MongoClient, UpdateOne

from src.chunker import build_chunk_documents
from src.config import Settings
from src.embedder import GeminiEmbedder
from src.utils import ensure_json_serializable, load_source_documents, utc_now


def build_knowledge_item(source_document: Any) -> dict[str, Any]:
    metadata = dict(source_document.metadata)
    return ensure_json_serializable(
        {
            "document_id": metadata["document_id"],
            "source_file": metadata["source_file"],
            "title": metadata["title"],
            "raw_markdown": source_document.raw_markdown,
            "markdown_body": source_document.markdown_body,
            "plain_text_body": source_document.plain_text_body,
            "updated_at": utc_now(),
        }
    )


def _write_vector_index_definition(
    atlas_dir: Path,
    *,
    file_name: str,
    vector_path: str,
    dimensions: int,
) -> None:
    atlas_dir.mkdir(parents=True, exist_ok=True)
    index_definition = {
        "name": file_name.replace(".json", ""),
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": vector_path,
                    "numDimensions": dimensions,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "parent_document_id"},
            ]
        },
    }
    output_path = atlas_dir / file_name
    output_path.write_text(json.dumps(index_definition, indent=2), encoding="utf-8")


def ingest_documents(
    settings: Settings,
    *,
    exclude_source_files: set[str] | None = None,
) -> dict[str, Any]:
    print(f"Loading source documents from {settings.source_docs_dir} ...")
    source_documents = load_source_documents(settings.source_docs_dir)
    print(f"Loaded {len(source_documents)} markdown source documents")

    excluded_files = exclude_source_files or set()
    if excluded_files:
        source_documents = [
            source_document
            for source_document in source_documents
            if source_document.file_name not in excluded_files
        ]
        print(
            "Excluded source files: "
            + ", ".join(sorted(excluded_files))
        )
        print(f"Remaining source documents: {len(source_documents)}")

    if not source_documents:
        raise RuntimeError("No source documents remain after exclusions")

    knowledge_items = [build_knowledge_item(source_document) for source_document in source_documents]
    return _ingest_knowledge_items(settings, knowledge_items)


def _ingest_knowledge_items(
    settings: Settings,
    knowledge_items: list[dict[str, Any]],
) -> dict[str, Any]:
    chunk_documents: list[dict[str, Any]] = []
    for item in knowledge_items:
        chunk_documents.extend(
            build_chunk_documents(
                item,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
        )
    if not chunk_documents:
        raise RuntimeError("Chunking produced zero chunk documents")

    print(f"Created {len(chunk_documents)} deterministic chunks")
    embedder = GeminiEmbedder(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_embedding_model,
    )

    print(f"Generating embeddings with model {settings.gemini_embedding_model} ...")
    embeddings = embedder.embed_texts([chunk["chunk_text"] for chunk in chunk_documents])
    embedding_dimensions = len(embeddings[0])
    for chunk, embedding in zip(chunk_documents, embeddings, strict=True):
        chunk["embedding"] = embedding
        chunk["embedding_dimensions"] = embedding_dimensions
        chunk["updated_at"] = utc_now()

    _write_vector_index_definition(
        settings.atlas_dir,
        file_name="knowledge_chunks_vector_index.json",
        vector_path="embedding",
        dimensions=embedding_dimensions,
    )
    print(
        f"Wrote Atlas vector index definition with {embedding_dimensions} dimensions "
        f"to {settings.atlas_dir / 'knowledge_chunks_vector_index.json'}"
    )

    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    items_collection = db[settings.knowledge_items_collection]
    chunks_collection = db[settings.knowledge_chunks_collection]

    source_files = [item["source_file"] for item in knowledge_items]
    document_ids = [item["document_id"] for item in knowledge_items]

    print("Upserting source documents into MongoDB Atlas ...")
    items_collection.delete_many({"source_file": {"$in": source_files}})
    item_ops = [
        UpdateOne({"document_id": item["document_id"]}, {"$set": item}, upsert=True)
        for item in knowledge_items
    ]
    if item_ops:
        items_collection.bulk_write(item_ops, ordered=False)

    print("Replacing chunk documents for the current source set ...")
    chunks_collection.delete_many({"parent_document_id": {"$in": document_ids}})
    chunk_ops = [
        UpdateOne({"chunk_id": chunk["chunk_id"]}, {"$set": chunk}, upsert=True)
        for chunk in chunk_documents
    ]
    if chunk_ops:
        chunks_collection.bulk_write(chunk_ops, ordered=False)

    items_collection.create_index("document_id", unique=True)
    chunks_collection.create_index("chunk_id", unique=True)
    chunks_collection.create_index("parent_document_id")

    print(
        "Ingestion complete: "
        f"{items_collection.count_documents({})} source docs, "
        f"{chunks_collection.count_documents({})} chunks"
    )
    return {
        "source_documents": len(knowledge_items),
        "chunks": len(chunk_documents),
        "embedding_dimensions": embedding_dimensions,
        "items_collection": settings.knowledge_items_collection,
        "chunks_collection": settings.knowledge_chunks_collection,
    }
