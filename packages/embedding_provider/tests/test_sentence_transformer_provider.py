import pytest

from codemind_embedding_provider import get_default_provider


@pytest.fixture(scope="module")
def provider():
    return get_default_provider()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


async def test_embed_returns_vectors_with_the_expected_dimension(provider):
    vectors = await provider.embed(["hello world", "a second sentence"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384


async def test_semantically_related_sentences_are_more_similar_than_unrelated_ones(provider):
    query, related, unrelated = await provider.embed(
        [
            "divide two numbers",
            "function that divides a by b",
            "a recipe for cooking pasta",
        ]
    )

    similarity_to_related = _cosine_similarity(query, related)
    similarity_to_unrelated = _cosine_similarity(query, unrelated)

    assert similarity_to_related > similarity_to_unrelated
