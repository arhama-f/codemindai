from datetime import datetime
from uuid import UUID

from codemind_ai_orchestrator import AIProvider, ClaudeAIProvider
from codemind_shared_types.models import File, Finding, FindingExplanation
from codemind_shared_types.schemas import FindingDetailDTO
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_api.providers import get_real_ai_provider

router = APIRouter(prefix="/api/organizations/{org_id}/repositories/{repo_id}", tags=["finding-explanations"])


class FindingExplanationResponse(BaseModel):
    id: UUID
    finding_id: UUID
    explanation: str
    generated_by: str
    created_at: datetime


def _to_response(finding_explanation: FindingExplanation) -> FindingExplanationResponse:
    return FindingExplanationResponse(
        id=finding_explanation.id,
        finding_id=finding_explanation.finding_id,
        explanation=finding_explanation.explanation,
        generated_by=finding_explanation.generated_by,
        created_at=finding_explanation.created_at,
    )


async def _get_org_scoped_finding(db: AsyncSession, org_id: UUID, finding_id: UUID) -> Finding:
    finding = await db.get(Finding, finding_id)
    if finding is None or finding.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding


async def _get_org_scoped_explanation(
    db: AsyncSession, org_id: UUID, explanation_id: UUID
) -> FindingExplanation:
    finding_explanation = await db.get(FindingExplanation, explanation_id)
    if finding_explanation is None or finding_explanation.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Finding explanation not found"
        )
    return finding_explanation


@router.post(
    "/findings/{finding_id}/explain",
    response_model=FindingExplanationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def explain_finding(
    org_id: UUID,
    repo_id: UUID,
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_real_ai_provider),
    _membership=Depends(get_org_membership),
) -> FindingExplanationResponse:
    finding = await _get_org_scoped_finding(db, org_id, finding_id)
    file_row = await db.get(File, finding.file_id)
    if file_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    finding_dto = FindingDetailDTO(
        check_id=finding.check_id,
        category=finding.category,
        title=finding.title,
        severity=finding.severity,
        confidence=finding.confidence,
        explanation=finding.explanation,
        recommended_fix=finding.recommended_fix,
        suggested_test=finding.suggested_test,
        execution_path=finding.execution_path,
        file_path=file_row.path,
        start_line=finding.start_line,
        end_line=finding.end_line,
        evidence=finding.evidence,
    )
    explanation_text = await ai_provider.explain_finding(finding=finding_dto)

    finding_explanation = FindingExplanation(
        organization_id=org_id,
        finding_id=finding.id,
        explanation=explanation_text,
        generated_by="claude" if isinstance(ai_provider, ClaudeAIProvider) else "mock",
    )
    db.add(finding_explanation)
    await db.commit()
    await db.refresh(finding_explanation)

    return _to_response(finding_explanation)


@router.get("/finding-explanations/{explanation_id}", response_model=FindingExplanationResponse)
async def get_finding_explanation(
    org_id: UUID,
    repo_id: UUID,
    explanation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> FindingExplanationResponse:
    finding_explanation = await _get_org_scoped_explanation(db, org_id, explanation_id)
    return _to_response(finding_explanation)
