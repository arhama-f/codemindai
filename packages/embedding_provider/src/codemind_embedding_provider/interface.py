from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    model_name: str
    dimension: int

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
