from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_api.repository_index_utils import get_latest_completed_index
from codemind_shared_types.models import File, Symbol

router = APIRouter(prefix="/api/organizations/{org_id}/repositories/{repo_id}", tags=["files"])


class FileListItem(BaseModel):
    id: UUID
    path: str
    language: str
    size_bytes: int


class SymbolSummary(BaseModel):
    id: UUID
    name: str
    kind: str
    start_line: int
    end_line: int


class FileDetailResponse(BaseModel):
    path: str
    content: str
    language: str
    symbols: list[SymbolSummary]


class SymbolSearchResult(BaseModel):
    id: UUID
    name: str
    kind: str
    file_id: UUID
    file_path: str
    start_line: int
    end_line: int


@router.get("/files", response_model=list[FileListItem])
async def list_files(
    org_id: UUID,
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> list[FileListItem]:
    repository_index = await get_latest_completed_index(db, repo_id)
    if repository_index is None:
        return []

    result = await db.execute(
        select(File).where(File.repository_index_id == repository_index.id).order_by(File.path)
    )
    return [
        FileListItem(id=f.id, path=f.path, language=f.language, size_bytes=f.size_bytes)
        for f in result.scalars().all()
    ]


@router.get("/files/{file_id}", response_model=FileDetailResponse)
async def get_file(
    org_id: UUID,
    repo_id: UUID,
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> FileDetailResponse:
    file_row = await db.get(File, file_id)
    if file_row is None or file_row.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    symbols_result = await db.execute(
        select(Symbol).where(Symbol.file_id == file_id).order_by(Symbol.start_line)
    )
    symbols = [
        SymbolSummary(
            id=s.id, name=s.name, kind=s.kind, start_line=s.start_line, end_line=s.end_line
        )
        for s in symbols_result.scalars().all()
    ]

    return FileDetailResponse(
        path=file_row.path, content=file_row.content, language=file_row.language, symbols=symbols
    )


@router.get("/symbols", response_model=list[SymbolSearchResult])
async def search_symbols(
    org_id: UUID,
    repo_id: UUID,
    query: str = "",
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> list[SymbolSearchResult]:
    repository_index = await get_latest_completed_index(db, repo_id)
    if repository_index is None:
        return []

    stmt = (
        select(Symbol, File.path)
        .join(File, File.id == Symbol.file_id)
        .where(File.repository_index_id == repository_index.id)
    )
    if query:
        stmt = stmt.where(Symbol.name.ilike(f"%{query}%"))
    stmt = stmt.order_by(Symbol.name)

    result = await db.execute(stmt)
    return [
        SymbolSearchResult(
            id=symbol.id,
            name=symbol.name,
            kind=symbol.kind,
            file_id=symbol.file_id,
            file_path=file_path,
            start_line=symbol.start_line,
            end_line=symbol.end_line,
        )
        for symbol, file_path in result.all()
    ]
