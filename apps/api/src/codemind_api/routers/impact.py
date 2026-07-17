from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_shared_types.models import File, Symbol, SymbolRelationship

router = APIRouter(prefix="/api/organizations/{org_id}/repositories/{repo_id}", tags=["impact"])


class ImpactedFile(BaseModel):
    file_id: UUID
    file_path: str
    confidence: str
    raw_specifier: str | None = None


class SymbolImpactResponse(BaseModel):
    symbol_id: UUID
    symbol_name: str
    file_path: str
    direct_dependent_files: list[ImpactedFile]
    transitive_dependent_files: list[ImpactedFile]


@router.get("/symbols/{symbol_id}/impact", response_model=SymbolImpactResponse)
async def get_symbol_impact(
    org_id: UUID,
    repo_id: UUID,
    symbol_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> SymbolImpactResponse:
    """"What breaks if I change this?" — honestly scoped to file-level blast
    radius (not a true call graph): direct dependents are files that import
    this exact symbol; transitive dependents are files that import *those*
    files, one hop further. `from_symbol_id` isn't populated (would need
    in-body reference resolution), so this can't tell you which *symbol* in a
    dependent file uses the target — only that the file does."""
    symbol = await db.get(Symbol, symbol_id)
    if symbol is None or symbol.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol not found")

    symbol_file = await db.get(File, symbol.file_id)

    direct_result = await db.execute(
        select(SymbolRelationship, File.id, File.path)
        .join(File, File.id == SymbolRelationship.from_file_id)
        .where(SymbolRelationship.to_symbol_id == symbol_id)
    )

    direct_dependent_files: list[ImpactedFile] = []
    direct_file_ids: set[UUID] = set()
    for rel, file_id, file_path in direct_result.all():
        if file_id in direct_file_ids:
            continue
        direct_file_ids.add(file_id)
        direct_dependent_files.append(
            ImpactedFile(
                file_id=file_id,
                file_path=file_path,
                confidence=rel.confidence or "unknown",
                raw_specifier=rel.raw_specifier,
            )
        )

    transitive_dependent_files: list[ImpactedFile] = []
    if direct_file_ids:
        transitive_result = await db.execute(
            select(SymbolRelationship, File.id, File.path)
            .join(File, File.id == SymbolRelationship.from_file_id)
            .where(SymbolRelationship.to_file_id.in_(direct_file_ids))
        )
        seen_file_ids = set(direct_file_ids)
        for rel, file_id, file_path in transitive_result.all():
            if file_id in seen_file_ids:
                continue
            seen_file_ids.add(file_id)
            transitive_dependent_files.append(
                ImpactedFile(
                    file_id=file_id,
                    file_path=file_path,
                    confidence=rel.confidence or "unknown",
                    raw_specifier=rel.raw_specifier,
                )
            )

    return SymbolImpactResponse(
        symbol_id=symbol.id,
        symbol_name=symbol.name,
        file_path=symbol_file.path if symbol_file is not None else "",
        direct_dependent_files=direct_dependent_files,
        transitive_dependent_files=transitive_dependent_files,
    )
