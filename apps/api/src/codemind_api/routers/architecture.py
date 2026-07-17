from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_ai_orchestrator import AIProvider
from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_api.providers import get_ai_provider
from codemind_api.repository_index_utils import get_latest_completed_index
from codemind_shared_types.models import File, Symbol, SymbolRelationship

router = APIRouter(prefix="/api/organizations/{org_id}/repositories/{repo_id}", tags=["architecture"])

EXTERNAL_NODE_ID = "external"


class ArchitectureNode(BaseModel):
    id: str
    type: str
    label: str
    file_id: UUID | None = None
    language: str | None = None
    symbol_count: int = 0
    subsystem: str | None = None


class ArchitectureEdge(BaseModel):
    id: str
    source: str
    target: str
    kind: str
    raw_specifier: str | None = None


class ArchitectureSubsystem(BaseModel):
    name: str
    file_ids: list[str]


class ArchitectureResponse(BaseModel):
    nodes: list[ArchitectureNode]
    edges: list[ArchitectureEdge]
    subsystems: list[ArchitectureSubsystem]


@router.get("/architecture", response_model=ArchitectureResponse)
async def get_architecture(
    org_id: UUID,
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
    _membership=Depends(get_org_membership),
) -> ArchitectureResponse:
    repository_index = await get_latest_completed_index(db, repo_id)
    if repository_index is None:
        return ArchitectureResponse(nodes=[], edges=[], subsystems=[])

    files_result = await db.execute(
        select(File).where(File.repository_index_id == repository_index.id)
    )
    files = files_result.scalars().all()

    symbol_count_result = await db.execute(
        select(Symbol.file_id, func.count(Symbol.id))
        .where(Symbol.file_id.in_([f.id for f in files]))
        .group_by(Symbol.file_id)
    )
    symbol_counts: dict[UUID, int] = dict(symbol_count_result.all())  # type: ignore[arg-type]

    subsystems = await ai_provider.identify_subsystems(file_paths=[f.path for f in files])
    subsystem_by_path = {
        path: subsystem.name for subsystem in subsystems for path in subsystem.file_paths
    }

    nodes = [
        ArchitectureNode(
            id=str(f.id),
            type="file",
            label=f.path,
            file_id=f.id,
            language=f.language,
            symbol_count=symbol_counts.get(f.id, 0),
            subsystem=subsystem_by_path.get(f.path),
        )
        for f in files
    ]
    file_id_by_id = {f.id: f for f in files}

    relationships_result = await db.execute(
        select(SymbolRelationship).where(
            SymbolRelationship.repository_index_id == repository_index.id,
            SymbolRelationship.relationship_type == "imports",
        )
    )
    relationships = relationships_result.scalars().all()

    edges: list[ArchitectureEdge] = []
    has_external = False
    for rel in relationships:
        if rel.to_file_id is not None and rel.to_file_id in file_id_by_id:
            edges.append(
                ArchitectureEdge(
                    id=str(rel.id),
                    source=str(rel.from_file_id),
                    target=str(rel.to_file_id),
                    kind="resolved",
                    raw_specifier=rel.raw_specifier,
                )
            )
        else:
            has_external = True
            edges.append(
                ArchitectureEdge(
                    id=str(rel.id),
                    source=str(rel.from_file_id),
                    target=EXTERNAL_NODE_ID,
                    kind="external",
                    raw_specifier=rel.raw_specifier,
                )
            )

    if has_external:
        nodes.append(
            ArchitectureNode(id=EXTERNAL_NODE_ID, type="external", label="External dependencies")
        )

    response_subsystems = [
        ArchitectureSubsystem(
            name=subsystem.name,
            file_ids=[
                str(f.id) for f in files if f.path in subsystem.file_paths
            ],
        )
        for subsystem in subsystems
    ]

    return ArchitectureResponse(nodes=nodes, edges=edges, subsystems=response_subsystems)
