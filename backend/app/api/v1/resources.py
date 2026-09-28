from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession, ListParams
from app.schemas.common import APIResponse
from app.schemas.pagination import PagePublic
from app.schemas.resource import CoursePublic, MentorPublic, ProjectPublic
from app.services.pagination import paginate
from app.services.resource_service import resource_service

courses_router = APIRouter(prefix="/courses", tags=["courses"])
projects_router = APIRouter(prefix="/projects", tags=["projects"])
mentors_router = APIRouter(prefix="/mentors", tags=["mentors"])

COURSE_SORT = {
    "title": lambda item: item.title.lower(),
    "difficulty": lambda item: item.difficulty,
    "duration_hours": lambda item: item.duration_hours,
    "rating": lambda item: float(item.rating),
}
PROJECT_SORT = {
    "title": lambda item: item.title.lower(),
    "difficulty": lambda item: item.difficulty,
    "duration_hours": lambda item: item.duration_hours,
}
MENTOR_SORT = {
    "name": lambda item: item.name.lower(),
    "years_experience": lambda item: item.years_experience,
}


@courses_router.get("", response_model=APIResponse[PagePublic[CoursePublic]])
def list_courses(
    _user: CurrentUser,
    db: DBSession,
    listing: ListParams,
    skill_id: Annotated[UUID | None, Query()] = None,
) -> APIResponse[PagePublic[CoursePublic]]:
    return APIResponse(
        data=paginate(
            resource_service.list_courses(db, skill_id=skill_id),
            page=listing.page,
            page_size=listing.page_size,
            sort=listing.sort,
            order=listing.order,
            allowed=COURSE_SORT,
        )
    )


@courses_router.get("/{course_id}", response_model=APIResponse[CoursePublic])
def get_course(
    course_id: UUID, _user: CurrentUser, db: DBSession
) -> APIResponse[CoursePublic]:
    return APIResponse(data=resource_service.get_course(db, course_id))


@projects_router.get("", response_model=APIResponse[PagePublic[ProjectPublic]])
def list_projects(
    _user: CurrentUser,
    db: DBSession,
    listing: ListParams,
    skill_id: Annotated[UUID | None, Query()] = None,
) -> APIResponse[PagePublic[ProjectPublic]]:
    return APIResponse(
        data=paginate(
            resource_service.list_projects(db, skill_id=skill_id),
            page=listing.page,
            page_size=listing.page_size,
            sort=listing.sort,
            order=listing.order,
            allowed=PROJECT_SORT,
        )
    )


@projects_router.get("/{project_id}", response_model=APIResponse[ProjectPublic])
def get_project(
    project_id: UUID, _user: CurrentUser, db: DBSession
) -> APIResponse[ProjectPublic]:
    return APIResponse(data=resource_service.get_project(db, project_id))


@mentors_router.get("", response_model=APIResponse[PagePublic[MentorPublic]])
def list_mentors(
    _user: CurrentUser,
    db: DBSession,
    listing: ListParams,
    skill_id: Annotated[UUID | None, Query()] = None,
) -> APIResponse[PagePublic[MentorPublic]]:
    return APIResponse(
        data=paginate(
            resource_service.list_mentors(db, skill_id=skill_id),
            page=listing.page,
            page_size=listing.page_size,
            sort=listing.sort,
            order=listing.order,
            allowed=MENTOR_SORT,
        )
    )


@mentors_router.get("/{mentor_id}", response_model=APIResponse[MentorPublic])
def get_mentor(
    mentor_id: UUID, _user: CurrentUser, db: DBSession
) -> APIResponse[MentorPublic]:
    return APIResponse(data=resource_service.get_mentor(db, mentor_id))
