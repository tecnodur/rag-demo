from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import get_settings
from src.embedder import GeminiEmbedder
from src.generator import GeminiGenerator
from src.retrieval import retrieve_structured


QUESTION_OPTIONS = [
    "Can I reuse passwords in EU?",
    "What's the minimum password size?",
]


def choose_question(default_question: str | None) -> str:
    if default_question:
        return default_question

    print("\nChoose a question to test:")
    for index, question in enumerate(QUESTION_OPTIONS, start=1):
        print(f"  {index}. {question}")

    while True:
        raw_choice = input("\nSelection: ").strip()
        try:
            choice = int(raw_choice)
        except ValueError:
            print("Enter a number from the list.")
            continue

        if 1 <= choice <= len(QUESTION_OPTIONS):
            return QUESTION_OPTIONS[choice - 1]

        print("Enter a valid selection.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the structured RAG demo.")
    parser.add_argument(
        "--question",
        default=None,
        help="Question to ask the demo pipeline.",
    )
    parser.add_argument("--region", default="EU", help="Structured retrieval filter: region")
    parser.add_argument("--status", default="Active", help="Structured retrieval filter: status")
    parser.add_argument(
        "--doc-type",
        default="policy",
        dest="doc_type",
        help="Structured retrieval filter: doc_type",
    )
    parser.add_argument(
        "--structured-limit",
        type=int,
        default=4,
        help="Number of chunks to retrieve for structured mode.",
    )
    return parser.parse_args()


def print_hits(label: str, hits: list[dict], *, include_metadata: bool) -> None:
    print(f"\n{label}")
    print("=" * len(label))
    if not hits:
        print("  No chunks retrieved.")
        return

    for index, hit in enumerate(hits, start=1):
        preview = hit["chunk_text"][:180].replace("\n", " ").strip()
        if include_metadata:
            print(f"\n[{index}] {hit['title']}")
            print(f"  score: {hit.get('score', 0.0):.4f}")
            print(f"  document_id: {hit['parent_document_id']}")
            print(f"  chunk_id: {hit['chunk_id']}")
            print(f"  version: {hit['version']}")
            print(f"  status: {hit['status']}")
            print(f"  region: {hit['region']}")
            print(f"  doc_type: {hit['doc_type']}")
            print(f"  preview: {preview}...")
        else:
            print(f"\n[{index}] {hit['title']}")
            print(f"  score: {hit.get('score', 0.0):.4f}")
            print(f"  chunk_id: {hit['chunk_id']}")
            print(f"  preview: {preview}...")


def main() -> None:
    args = parse_args()
    question = choose_question(args.question)
    settings = get_settings()

    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    chunks_collection = db[settings.knowledge_chunks_collection]

    embedder = GeminiEmbedder(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_embedding_model,
    )
    generator = GeminiGenerator(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model,
    )

    print(f"\nQuestion: {question}")
    print("Structured filters: " f"region={args.region}, status={args.status}, doc_type={args.doc_type}")

    structured_hits = retrieve_structured(
        collection=chunks_collection,
        embedder=embedder,
        index_name=settings.vector_index_name,
        question=question,
        region=args.region,
        status=args.status,
        doc_type=args.doc_type,
        limit=args.structured_limit,
    )

    print_hits("Structured Retrieval", structured_hits, include_metadata=True)

    structured_answer = generator.answer_question(
        question=question,
        retrieved_chunks=structured_hits,
        include_metadata=True,
    )

    answer_label = f"Structured Answer powered by {settings.gemini_model}"
    print(f"\n{answer_label}")
    print("=" * len(answer_label))
    print(structured_answer)


if __name__ == "__main__":
    main()
