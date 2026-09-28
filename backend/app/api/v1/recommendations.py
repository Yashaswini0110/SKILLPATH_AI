from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.recommendation import (
    MentorMatchListPublic,
    PracticePairListPublic,
    RecommendationListPublic,
)
from app.services.mentor_service import mentor_service
from app.services.practice_service import practice_service
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
RecMethod = Literal["POPULARITY", "CONTENT", "SEMANTIC", "KG", "HYBRID"]


@router.get("/courses", response_model=APIResponse[RecommendationListPublic])
def recommend_courses(
    user: CurrentUser,
    db: DBSession,
    method: Annotated[RecMethod, Query()] = "HYBRID",
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> APIResponse[RecommendationListPublic]:
    return APIResponse(
        data=recommendation_service.recommend(
            db,
            user,
            resource_type="COURSE",
            method=method,
            role_id=role_id,
            job_description_id=job_description_id,
            limit=limit,
        )
    )


@router.get("/projects", response_model=APIResponse[RecommendationListPublic])
def recommend_projects(
    user: CurrentUser,
    db: DBSession,
    method: Annotated[RecMethod, Query()] = "HYBRID",
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> APIResponse[RecommendationListPublic]:
    return APIResponse(
        data=recommendation_service.recommend(
            db,
            user,
            resource_type="PROJECT",
            method=method,
            role_id=role_id,
            job_description_id=job_description_id,
            limit=limit,
        )
    )


@router.get("/mentors", response_model=APIResponse[RecommendationListPublic])
def recommend_mentors(
    user: CurrentUser,
    db: DBSession,
    method: Annotated[RecMethod, Query()] = "HYBRID",
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> APIResponse[RecommendationListPublic]:
    return APIResponse(
        data=recommendation_service.recommend(
            db,
            user,
            resource_type="MENTOR",
            method=method,
            role_id=role_id,
            job_description_id=job_description_id,
            limit=limit,
        )
    )


@router.get("/practice-pairs", response_model=APIResponse[PracticePairListPublic])
def recommend_practice_pairs(
    user: CurrentUser,
    db: DBSession,
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> APIResponse[PracticePairListPublic]:
    return APIResponse(
        data=practice_service.pair(
            db,
            user,
            role_id=role_id,
            job_description_id=job_description_id,
            limit=limit,
        )
    )


@router.get("/mentor-matches", response_model=APIResponse[MentorMatchListPublic])
def recommend_mentor_matches(
    user: CurrentUser,
    db: DBSession,
    role_id: Annotated[UUID | None, Query()] = None,
    job_description_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> APIResponse[MentorMatchListPublic]:
    return APIResponse(
        data=mentor_service.match(
            db,
            user,
            role_id=role_id,
            job_description_id=job_description_id,
            limit=limit,
        )
    )
