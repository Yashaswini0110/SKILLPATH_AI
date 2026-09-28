from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession, ListParams
from app.schemas.common import APIResponse
from app.schemas.pagination import PagePublic
from app.schemas.role import TargetRolePublic, TargetRoleSummary
from app.schemas.skill import SkillPublic, SkillResolveRequest, SkillResolveResponse
from app.services.catalog_service import catalog_service
from app.services.pagination import paginate
from app.services.taxonomy_service import taxonomy_service

roles_router = APIRouter(prefix="/roles", tags=["roles"])
skills_router = APIRouter(prefix="/skills", tags=["skills"])

ROLE_SORT = {
    "title": lambda item: item.title.lower(),
    "category": lambda item: item.category.lower(),
}
SKILL_SORT = {
    "canonical_name": lambda item: item.canonical_name.lower(),
    "category": lambda item: item.category.lower(),
    "difficulty": lambda item: item.difficulty,
}


@roles_router.get("", response_model=APIResponse[PagePublic[TargetRoleSummary]])
def list_roles(
    _user: CurrentUser, db: DBSession, listing: ListParams
) -> APIResponse[PagePublic[TargetRoleSummary]]:
    return APIResponse(
        data=paginate(
            catalog_service.list_roles(db),
            page=listing.page,
            page_size=listing.page_size,
            sort=listing.sort,
            order=listing.order,
            allowed=ROLE_SORT,
        )
    )


@roles_router.get("/{role_id}", response_model=APIResponse[TargetRolePublic])
def get_role(
    role_id: UUID, _user: CurrentUser, db: DBSession
) -> APIResponse[TargetRolePublic]:
    return APIResponse(data=catalog_service.get_role(db, role_id))


@skills_router.get("", response_model=APIResponse[PagePublic[SkillPublic]])
def list_skills(
    _user: CurrentUser,
    db: DBSession,
    listing: ListParams,
    category: Annotated[str | None, Query()] = None,
) -> APIResponse[PagePublic[SkillPublic]]:
    return APIResponse(
        data=paginate(
            catalog_service.list_skills(db, category=category),
            page=listing.page,
            page_size=listing.page_size,
            sort=listing.sort,
            order=listing.order,
            allowed=SKILL_SORT,
        )
    )


@skills_router.post("/resolve", response_model=APIResponse[SkillResolveResponse])
def resolve_skills(
    payload: SkillResolveRequest,
    _user: CurrentUser,
    db: DBSession,
) -> APIResponse[SkillResolveResponse]:
    return APIResponse(data=taxonomy_service.resolve(db, payload.mentions))
