from __future__ import annotations

from collections.abc import Sequence

from google import genai


def _extract_text(response: object) -> str:
    text = getattr(response, "text", None)
    if text:
        return str(text).strip()

    candidates = getattr(response, "candidates", None)
    if not candidates:
        raise RuntimeError("Gemini generation response did not include text")

    parts = getattr(candidates[0].content, "parts", [])
    rendered = []
    for part in parts:
        part_text = getattr(part, "text", None)
        if part_text:
            rendered.append(part_text)
    if not rendered:
        raise RuntimeError("Gemini generation response did not include text parts")
    return "\n".join(rendered).strip()


class GeminiGenerator:
    def __init__(self, *, api_key: str, model_name: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def answer_question(
        self,
        *,
        question: str,
        retrieved_chunks: Sequence[dict],
        include_metadata: bool = True,
    ) -> str:
        context_blocks = []
        for chunk in retrieved_chunks:
            if include_metadata:
                context_blocks.append(
                    "\n".join(
                        [
                            f"Parent Document ID: {chunk['parent_document_id']}",
                            f"Title: {chunk['title']}",
                            f"Version: {chunk['version']}",
                            f"Status: {chunk['status']}",
                            f"Region: {chunk['region']}",
                            f"Chunk Index: {chunk['chunk_index']}",
                            f"Chunk Text: {chunk['chunk_text']}",
                        ]
                    )
                )
            else:
                context_blocks.append(f"Chunk Text: {chunk['chunk_text']}")

        instructions = [
            "You are answering an enterprise knowledge question.",
            "Answer using only the provided context.",
            "If the answer is not in the context, say so plainly.",
            "Do not merge conflicting policy statements into a single unified answer.",
            "If the retrieved context contains conflicting rules from different documents or versions, call out the conflict explicitly before giving the best-supported answer.",
        ]
        if include_metadata:
            instructions.extend(
                [
                    "Use the provided metadata when it is present.",
                    "Cite the supporting source using the parent document ID or the title and version.",
                ]
            )
        else:
            instructions.extend(
                [
                    "The retrieval system did not provide document metadata.",
                    "Do not assume document status, region, or version unless the chunk text itself states it.",
                    "Answer strictly from the retrieved chunk text, even if the result may be incomplete or outdated.",
                    "Do not cite source titles, versions, or document IDs in this mode.",
                ]
            )

        prompt = "\n\n".join(
            instructions
            + [
                f"Question: {question}",
                "Context:",
                "\n\n---\n\n".join(context_blocks) if context_blocks else "No context provided.",
            ]
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return _extract_text(response)
