from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data" / "source_docs"
ATLAS_DIR = ROOT_DIR / "atlas"


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    mongodb_db: str
    knowledge_items_collection: str
    knowledge_chunks_collection: str
    gemini_api_key: str
    gemini_model: str
    gemini_embedding_model: str
    vector_index_name: str
    source_docs_dir: Path = DATA_DIR
    atlas_dir: Path = ATLAS_DIR
    chunk_size: int = 500
    chunk_overlap: int = 120


def _require_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value:
        return value
    raise RuntimeError(f"Missing required environment variable: {name}")


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        mongodb_uri=_require_env("MONGODB_URI"),
        mongodb_db=_require_env("MONGODB_DB", "genai_knowledge_demo"),
        knowledge_items_collection=_require_env(
            "MONGODB_KNOWLEDGE_ITEMS_COLLECTION",
            "knowledge_items",
        ),
        knowledge_chunks_collection=_require_env(
            "MONGODB_KNOWLEDGE_CHUNKS_COLLECTION",
            "knowledge_chunks",
        ),
        gemini_api_key=_require_env("GEMINI_API_KEY"),
        gemini_model=_require_env("GEMINI_MODEL", "gemini-2.5-flash"),
        gemini_embedding_model=_require_env(
            "GEMINI_EMBEDDING_MODEL",
            "gemini-embedding-001",
        ),
        vector_index_name=_require_env(
            "VECTOR_INDEX_NAME",
            "knowledge_chunks_vector_index",
        ),
    )
