import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_api.providers import get_ai_provider, get_embedding_provider
from codemind_api.repository_index_utils import get_latest_completed_index
from codemind_ai_orchestrator import AIProvider
from codemind_embedding_provider import EmbeddingProvider
from codemind_shared_types.models import CodeChunk, Embedding, File, Symbol
from codemind_shared_types.schemas import RetrievedChunkDTO

router = APIRouter(prefix="/api/organizations/{org_id}/repositories/{repo_id}", tags=["ask"])

_STOPWORDS = {
    "the", "is", "a", "an", "of", "to", "in", "on", "for", "and", "or", "what",
    "how", "does", "do", "which", "that", "this", "i", "my", "code", "are", "be",
}
_SYMBOL_MATCH_BONUS = 5
_MAX_CITATIONS = 3
_PREFILTER_LIMIT = 200
_SNIPPET_LENGTH = 200

# Cosine distance cutoff for the embedding-search tier: a real embedding model
# never returns "no match" (every chunk has *some* similarity), so without a
# cutoff this tier would always return its 3 least-dissimilar chunks even for
# nonsense queries. Measured empirically against the demo repo (all-MiniLM-L6-v2):
# genuinely relevant matches (e.g. "how do I split a number into pieces?" ->
# math.ts's divide, no keyword overlap) score ~0.45-0.53; nonsense queries
# ("zzz nonexistent qqqq keyword xyzzy", an unrelated weather question) score
# ~0.92-0.98 against everything. 0.6 sits well clear of both.
_MAX_COSINE_DISTANCE = 0.6


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    citations: list[RetrievedChunkDTO]


def _tokenize(question: str) -> list[str]:
    tokens = re.findall(r"\w+", question.lower())
    keywords = [t for t in dict.fromkeys(tokens) if t not in _STOPWORDS]
    return keywords or list(dict.fromkeys(tokens))


async def _score_candidates(
    db: AsyncSession, repository_index_id: UUID, organization_id: UUID, keywords: list[str]
) -> list[tuple[int, CodeChunk, str]]:
    conditions = [CodeChunk.content.ilike(f"%{kw}%") for kw in keywords]
    result = await db.execute(
        select(CodeChunk, File.path)
        .join(File, File.id == CodeChunk.file_id)
        .where(
            CodeChunk.repository_index_id == repository_index_id,
            CodeChunk.organization_id == organization_id,
            or_(*conditions),
        )
        .limit(_PREFILTER_LIMIT)
    )
    candidates = result.all()
    if not candidates:
        return []

    file_ids = {chunk.file_id for chunk, _ in candidates}
    symbol_result = await db.execute(select(Symbol).where(Symbol.file_id.in_(file_ids)))
    symbols_by_file: dict[UUID, list[Symbol]] = {}
    for symbol in symbol_result.scalars().all():
        symbols_by_file.setdefault(symbol.file_id, []).append(symbol)

    scored = []
    for chunk, path in candidates:
        lowered = chunk.content.lower()
        score = sum(lowered.count(kw) for kw in keywords)
        for symbol in symbols_by_file.get(chunk.file_id, []):
            if chunk.start_line <= symbol.start_line <= chunk.end_line:
                if symbol.name.lower() in keywords:
                    score += _SYMBOL_MATCH_BONUS
        scored.append((score, chunk, path))

    scored.sort(key=lambda t: t[0], reverse=True)
    return scored


async def _embedding_candidates(
    db: AsyncSession,
    repository_index_id: UUID,
    organization_id: UUID,
    question_vector: list[float],
    model_name: str,
) -> list[tuple[CodeChunk, str]]:
    distance = Embedding.vector.cosine_distance(question_vector)
    result = await db.execute(
        select(CodeChunk, File.path, distance.label("distance"))
        .join(File, File.id == CodeChunk.file_id)
        .join(Embedding, Embedding.code_chunk_id == CodeChunk.id)
        .where(
            CodeChunk.repository_index_id == repository_index_id,
            CodeChunk.organization_id == organization_id,
            Embedding.model_name == model_name,
        )
        .order_by(distance)
        .limit(_MAX_CITATIONS)
    )
    return [
        (chunk, path)
        for chunk, path, chunk_distance in result.all()
        if chunk_distance <= _MAX_COSINE_DISTANCE
    ]


async def _fallback_symbol_citations(
    db: AsyncSession, repository_index_id: UUID, keywords: list[str]
) -> list[tuple[CodeChunk, str]]:
    conditions = [Symbol.name.ilike(f"%{kw}%") for kw in keywords]
    result = await db.execute(
        select(Symbol, File.path)
        .join(File, File.id == Symbol.file_id)
        .where(File.repository_index_id == repository_index_id, or_(*conditions))
    )

    citations: list[tuple[CodeChunk, str]] = []
    seen_chunk_ids: set[UUID] = set()
    for symbol, path in result.all():
        chunk_result = await db.execute(
            select(CodeChunk)
            .where(
                CodeChunk.file_id == symbol.file_id,
                CodeChunk.start_line <= symbol.start_line,
                CodeChunk.end_line >= symbol.start_line,
            )
            .limit(1)
        )
        chunk = chunk_result.scalar_one_or_none()
        if chunk is None or chunk.id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk.id)
        citations.append((chunk, path))
        if len(citations) >= _MAX_CITATIONS:
            break

    return citations


@router.post("/ask", response_model=AskResponse)
async def ask_repository_question(
    org_id: UUID,
    repo_id: UUID,
    payload: AskRequest,
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    _membership=Depends(get_org_membership),
) -> AskResponse:
    repository_index = await get_latest_completed_index(db, repo_id)
    if repository_index is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Repository has not been indexed yet"
        )

    question_vectors = await embedding_provider.embed([payload.question])
    citation_chunks = await _embedding_candidates(
        db, repository_index.id, org_id, question_vectors[0], embedding_provider.model_name
    )

    keywords = _tokenize(payload.question)
    if not citation_chunks and keywords:
        scored = await _score_candidates(db, repository_index.id, org_id, keywords)
        top_scored = [(chunk, path) for score, chunk, path in scored if score > 0][:_MAX_CITATIONS]
        citation_chunks = top_scored or await _fallback_symbol_citations(
            db, repository_index.id, keywords
        )

    citations = [
        RetrievedChunkDTO(
            file_path=path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            snippet=chunk.content[:_SNIPPET_LENGTH],
        )
        for chunk, path in citation_chunks
    ]

    answer = await ai_provider.answer_repository_question(
        question=payload.question, citations=citations
    )

    return AskResponse(answer=answer, citations=citations)
