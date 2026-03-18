from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceDocument:
    file_name: str
    metadata: dict[str, Any]
    raw_markdown: str
    markdown_body: str
    plain_text_body: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def markdown_to_plain_text(markdown_text: str) -> str:
    text = markdown_text.replace("\r\n", "\n")
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_]{1,3}", "", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return normalize_whitespace(text)


def extract_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def load_source_documents(source_docs_dir: Path) -> list[SourceDocument]:
    markdown_paths = sorted(source_docs_dir.glob("*.md"))
    if not markdown_paths:
        raise RuntimeError(f"No markdown source documents found in {source_docs_dir}")

    source_documents: list[SourceDocument] = []
    for path in markdown_paths:
        raw_markdown = path.read_text(encoding="utf-8")
        title = extract_title(raw_markdown, fallback=path.stem.replace("_", " "))
        derived_metadata = {
            "document_id": path.stem,
            "source_file": path.name,
            "title": title,
            "region": None,
            "status": None,
            "version": None,
            "effective_date": None,
            "owner_team": None,
            "audience": None,
            "doc_type": None,
            "tags": [],
            "short_description": "",
        }

        source_documents.append(
            SourceDocument(
                file_name=path.name,
                metadata=derived_metadata,
                raw_markdown=raw_markdown,
                markdown_body=raw_markdown,
                plain_text_body=markdown_to_plain_text(raw_markdown),
            )
        )

    return source_documents


def ensure_json_serializable(document: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(document, default=str))
