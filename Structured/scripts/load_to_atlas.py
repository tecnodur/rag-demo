from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import get_settings
from src.ingest import ingest_documents


def main() -> None:
    settings = get_settings()
    result = ingest_documents(settings)
    print("\nSummary")
    print(f"- Source documents ingested: {result['source_documents']}")
    print(f"- Chunk documents ingested: {result['chunks']}")
    print(f"- Embedding dimensions: {result['embedding_dimensions']}")
    print(
        "- Collections: "
        f"{result['items_collection']}, {result['chunks_collection']}"
    )


if __name__ == "__main__":
    main()
