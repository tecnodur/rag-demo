from __future__ import annotations

from typing import Sequence

from google import genai


class GeminiEmbedder:
    def __init__(self, *, api_key: str, model_name: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self.client.models.embed_content(
            model=self.model_name,
            contents=list(texts),
        )
        embeddings = getattr(response, "embeddings", None)
        if embeddings is None:
            raise RuntimeError("Gemini embedding response did not include embeddings")

        vectors: list[list[float]] = []
        for embedding in embeddings:
            values = getattr(embedding, "values", None)
            if values is None:
                if isinstance(embedding, dict):
                    values = embedding.get("values")
            if not values:
                raise RuntimeError("Gemini embedding item did not include vector values")
            vectors.append(list(values))
        return vectors

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
