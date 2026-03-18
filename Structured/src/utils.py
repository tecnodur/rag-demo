from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


METADATA_FIELD_MAP = {
    "Document ID": "document_id",
    "Title": "title",
    "Region": "region",
    "Status": "status",
    "Version": "version",
    "Effective Date": "effective_date",
    "Owner Team": "owner_team",
    "Audience": "audience",
    "Doc Type": "doc_type",
}

REQUIRED_MANIFEST_FIELDS = [
    "file_name",
    "document_id",
    "title",
    "region",
    "status",
    "version",
    "effective_date",
    "owner_team",
    "audience",
    "doc_type",
    "tags",
    "short_description",
]


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


def parse_metadata_block(markdown_text: str) -> tuple[dict[str, Any], str]:
    lines = markdown_text.splitlines()
    metadata: dict[str, Any] = {}
    body_start = 0

    for index, line in enumerate(lines):
        if not line.strip():
            body_start = index + 1
            break
        if ":" not in line:
            raise ValueError(f"Invalid metadata line: {line!r}")
        label, value = [part.strip() for part in line.split(":", 1)]
        if label not in METADATA_FIELD_MAP:
            raise ValueError(f"Unexpected metadata field: {label}")
        metadata[METADATA_FIELD_MAP[label]] = value
    else:
        body_start = len(lines)

    missing = [field for field in METADATA_FIELD_MAP.values() if field not in metadata]
    if missing:
        raise ValueError(f"Missing metadata fields: {missing}")

    metadata["version"] = int(metadata["version"])
    body = "\n".join(lines[body_start:]).strip()
    return metadata, body


def _normalize_manifest_entry(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)
    normalized["version"] = int(normalized["version"])
    normalized["tags"] = list(normalized["tags"])
    return normalized


def load_manifest(source_docs_dir: Path) -> dict[str, dict[str, Any]]:
    manifest_path = source_docs_dir / "metadata_manifest.json"
    manifest_data = read_json(manifest_path)
    if not isinstance(manifest_data, list):
        raise ValueError("metadata_manifest.json must contain a JSON array")

    manifest_by_file: dict[str, dict[str, Any]] = {}
    for entry in manifest_data:
        missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in entry]
        if missing:
            raise ValueError(
                f"Manifest entry missing fields {missing}: {entry.get('file_name', '<unknown>')}"
            )
        file_name = entry["file_name"]
        if file_name in manifest_by_file:
            raise ValueError(f"Duplicate manifest entry for {file_name}")
        manifest_by_file[file_name] = _normalize_manifest_entry(entry)
    return manifest_by_file


def load_source_documents(source_docs_dir: Path) -> list[SourceDocument]:
    manifest_by_file = load_manifest(source_docs_dir)
    markdown_paths = sorted(source_docs_dir.glob("*.md"))
    if not markdown_paths:
        raise RuntimeError(f"No markdown source documents found in {source_docs_dir}")

    source_documents: list[SourceDocument] = []
    for path in markdown_paths:
        if path.name not in manifest_by_file:
            raise ValueError(f"{path.name} exists on disk but is missing from metadata_manifest.json")

        raw_markdown = path.read_text(encoding="utf-8")
        file_metadata, body = parse_metadata_block(raw_markdown)
        manifest_entry = manifest_by_file[path.name]

        for field, value in file_metadata.items():
            manifest_value = manifest_entry[field]
            if manifest_value != value:
                raise ValueError(
                    f"Metadata mismatch for {path.name} field {field!r}: "
                    f"markdown={value!r}, manifest={manifest_value!r}"
                )

        combined_metadata = dict(manifest_entry)
        combined_metadata["source_file"] = path.name

        source_documents.append(
            SourceDocument(
                file_name=path.name,
                metadata=combined_metadata,
                raw_markdown=raw_markdown,
                markdown_body=body,
                plain_text_body=markdown_to_plain_text(body),
            )
        )

    manifest_only = sorted(set(manifest_by_file) - {path.name for path in markdown_paths})
    if manifest_only:
        raise ValueError(f"Manifest entries missing markdown files: {manifest_only}")

    return source_documents


def ensure_json_serializable(document: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(document, default=str))
