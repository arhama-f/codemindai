import re
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_current_user, get_org_membership
from codemind_shared_types.models import Organization, OrganizationMember, User

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


class CreateOrganizationRequest(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str


class OrganizationWithRoleResponse(OrganizationResponse):
    role: str


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "org"


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: CreateOrganizationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    base_slug = _slugify(payload.name)
    slug = base_slug
    while (
        await db.execute(select(Organization).where(Organization.slug == slug))
    ).scalar_one_or_none() is not None:
        slug = f"{base_slug}-{secrets.token_hex(3)}"

    organization = Organization(name=payload.name, slug=slug)
    db.add(organization)
    await db.flush()

    membership = OrganizationMember(organization_id=organization.id, user_id=user.id, role="owner")
    db.add(membership)
    await db.commit()
    await db.refresh(organization)

    return organization


@router.get("", response_model=list[OrganizationWithRoleResponse])
async def list_organizations(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[OrganizationWithRoleResponse]:
    result = await db.execute(
        select(Organization, OrganizationMember.role)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(OrganizationMember.user_id == user.id)
    )
    return [
        OrganizationWithRoleResponse(id=org.id, name=org.name, slug=org.slug, role=role)
        for org, role in result.all()
    ]


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> Organization:
    organization = await db.get(Organization, org_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization
