from __future__ import annotations

from typing import Any


def _snap_end(text: str, start: int, target_end: int, hard_end: int) -> int:
    if target_end >= len(text):
        return len(text)

    best_break = -1
    search_end = min(hard_end, len(text))
    for index in range(target_end, search_end):
        if text[index].isspace():
            best_break = index
            break

    if best_break != -1:
        return best_break
    return min(search_end, len(text))


def chunk_text(
    text: str,
    *,
    chunk_size: int = 500,
    chunk_overlap: int = 120,
) -> list[str]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    normalized_text = text.strip()
    if not normalized_text:
        return []

    chunks: list[str] = []
    start = 0
    hard_limit_padding = max(80, chunk_overlap)

    while start < len(normalized_text):
        target_end = min(start + chunk_size, len(normalized_text))
        hard_end = min(start + chunk_size + hard_limit_padding, len(normalized_text))
        end = _snap_end(normalized_text, start, target_end, hard_end)
        chunk = normalized_text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized_text):
            break

        next_start = max(0, end - chunk_overlap)
        while next_start < len(normalized_text) and normalized_text[next_start].isspace():
            next_start += 1
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks


def build_chunk_documents(
    source_document: dict[str, Any],
    *,
    chunk_size: int = 500,
    chunk_overlap: int = 120,
) -> list[dict[str, Any]]:
    chunks = chunk_text(
        source_document["plain_text_body"],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    documents: list[dict[str, Any]] = []
    for index, chunk_text_value in enumerate(chunks):
        documents.append(
            {
                "chunk_id": f"{source_document['document_id']}::chunk::{index:03d}",
                "parent_document_id": source_document["document_id"],
                "source_file": source_document["source_file"],
                "title": source_document["title"],
                "chunk_text": chunk_text_value,
                "chunk_index": index,
                "region": source_document["region"],
                "status": source_document["status"],
                "version": source_document["version"],
                "effective_date": source_document["effective_date"],
                "owner_team": source_document["owner_team"],
                "audience": source_document["audience"],
                "doc_type": source_document["doc_type"],
                "tags": source_document["tags"],
                "short_description": source_document["short_description"],
            }
        )
    return documents
