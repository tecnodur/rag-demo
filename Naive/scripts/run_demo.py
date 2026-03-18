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
from src.retrieval import retrieve_naive


QUESTION_OPTIONS = {
    "1": "Can I reuse passwords in  EU?",
    "2": "What's the minimum password size?",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the naive RAG demo.")
    parser.add_argument(
        "--question",
        help="Question to ask the demo pipeline. If omitted, an interactive prompt is shown.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=6,
        help="Number of chunks to retrieve.",
    )
    return parser.parse_args()


def select_question(cli_question: str | None) -> str:
    if cli_question:
        return cli_question

    print("Choose the question to test:")
    for option, question in QUESTION_OPTIONS.items():
        print(f"{option} - {question}")

    while True:
        selection = input("Selection: ").strip()
        if selection in QUESTION_OPTIONS:
            return QUESTION_OPTIONS[selection]
        print("Invalid selection. Enter 1 or 2.")


def print_hits(label: str, hits: list[dict], *, include_metadata: bool) -> None:
    print(f"\n{label}")
    if not hits:
        print("  No chunks retrieved.")
        return

    for index, hit in enumerate(hits, start=1):
        preview = hit["chunk_text"][:180].replace("\n", " ").strip()
        if include_metadata:
            print(
                f"  {index}. {hit['title']} | version={hit['version']} | "
                f"status={hit['status']} | region={hit['region']} | "
                f"doc_type={hit['doc_type']} | parent_document_id={hit['parent_document_id']} | "
                f"score={hit.get('score', 0.0):.4f}"
            )
        else:
            print(
                f"  {index}. {hit['title']} | score={hit.get('score', 0.0):.4f}"
            )
        print(f"     chunk_id={hit['chunk_id']} | preview={preview}...")


def main() -> None:
    args = parse_args()
    question = select_question(args.question)
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

    print(f"Question: {question}")

    naive_hits = retrieve_naive(
        collection=chunks_collection,
        embedder=embedder,
        index_name=settings.vector_index_name,
        question=question,
        limit=args.limit,
    )

    print_hits("Naive Retrieval", naive_hits, include_metadata=False)

    naive_answer = generator.answer_question(
        question=question,
        retrieved_chunks=naive_hits,
        include_metadata=False,
    )

    print("\nNaive Answer")
    print(naive_answer)


if __name__ == "__main__":
    main()
