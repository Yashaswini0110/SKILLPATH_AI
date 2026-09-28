from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.job_description import (
    JobDescriptionCreate,
    JobDescriptionPublic,
    JobDescriptionSummary,
)
from app.services.job_description_service import job_description_service

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])


@router.get("", response_model=APIResponse[list[JobDescriptionSummary]])
def list_job_descriptions(
    user: CurrentUser, db: DBSession
) -> APIResponse[list[JobDescriptionSummary]]:
    return APIResponse(data=job_description_service.list_job_descriptions(db, user))


@router.post(
    "",
    response_model=APIResponse[JobDescriptionPublic],
    status_code=status.HTTP_201_CREATED,
)
def analyze_pasted_job_description(
    payload: JobDescriptionCreate, user: CurrentUser, db: DBSession
) -> APIResponse[JobDescriptionPublic]:
    return APIResponse(
        data=job_description_service.create_from_text(db, user, payload),
        message="Job description analyzed. Unknown terms are left unmatched.",
    )


@router.post(
    "/upload",
    response_model=APIResponse[JobDescriptionPublic],
    status_code=status.HTTP_201_CREATED,
)
def upload_job_description(
    user: CurrentUser,
    db: DBSession,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
) -> APIResponse[JobDescriptionPublic]:
    return APIResponse(
        data=job_description_service.create_from_file(db, user, file, title),
        message="Job description analyzed. Unknown terms are left unmatched.",
    )


@router.get("/{job_description_id}", response_model=APIResponse[JobDescriptionPublic])
def get_job_description(
    job_description_id: UUID, user: CurrentUser, db: DBSession
) -> APIResponse[JobDescriptionPublic]:
    return APIResponse(
        data=job_description_service.get_job_description(db, user, job_description_id)
    )
