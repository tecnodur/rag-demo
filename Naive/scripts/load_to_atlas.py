from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load markdown source docs into Atlas for the Naive RAG demo."
    )
    parser.add_argument(
        "--exclude-source-file",
        action="append",
        default=[],
        help=(
            "Source markdown file name to exclude from ingestion "
            "(repeat flag to exclude multiple files)."
        ),
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help=(
            "Keep existing Atlas documents and only replace records for the current "
            "source set. By default, collections are cleared before ingestion."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    from src.config import get_settings
    from src.ingest import ingest_documents

    settings = get_settings()
    excluded_files = set(args.exclude_source_file)
    clear_existing = not args.keep_existing
    result = ingest_documents(
        settings,
        exclude_source_files=excluded_files,
        clear_existing=clear_existing,
    )
    print("\nSummary")
    print(f"- Source documents ingested: {result['source_documents']}")
    print(f"- Chunk documents ingested: {result['chunks']}")
    print(f"- Embedding dimensions: {result['embedding_dimensions']}")
    print(
        "- Collections: "
        f"{result['items_collection']}, {result['chunks_collection']}"
    )
    if excluded_files:
        print(f"- Excluded source files: {', '.join(sorted(excluded_files))}")
    print(f"- Cleared existing records first: {clear_existing}")


if __name__ == "__main__":
    main()
