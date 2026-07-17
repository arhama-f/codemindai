import asyncio

from sentence_transformers import SentenceTransformer

from codemind_embedding_provider.interface import EmbeddingProvider


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Real, local, free semantic embeddings — no API key required. Loads the
    model once at construction; callers should hold a single long-lived
    instance (see `get_default_provider`) rather than constructing this per
    request, since model load is the expensive part."""

    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    dimension = 384

    def __init__(self) -> None:
        self._model = SentenceTransformer(self.model_name)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # .encode() is sync/CPU-bound; keep it off the event loop.
        vectors = await asyncio.to_thread(
            self._model.encode, texts, normalize_embeddings=True
        )
        return vectors.tolist()
