from functools import lru_cache

from codemind_embedding_provider.interface import EmbeddingProvider
from codemind_embedding_provider.sentence_transformer_provider import (
    SentenceTransformerEmbeddingProvider,
)


@lru_cache
def get_default_provider() -> SentenceTransformerEmbeddingProvider:
    return SentenceTransformerEmbeddingProvider()


__all__ = ["EmbeddingProvider", "SentenceTransformerEmbeddingProvider", "get_default_provider"]
