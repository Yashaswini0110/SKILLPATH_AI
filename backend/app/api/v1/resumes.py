from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.resume import ResumePublic, ResumeSummary
from app.services.resume_service import resume_service

router = APIRouter(prefix="/employees", tags=["resumes"])


@router.get("/me/resumes", response_model=APIResponse[list[ResumeSummary]])
def list_resumes(user: CurrentUser, db: DBSession) -> APIResponse[list[ResumeSummary]]:
    return APIResponse(data=resume_service.list_resumes(db, user))


@router.post(
    "/me/resumes",
    response_model=APIResponse[ResumePublic],
    status_code=status.HTTP_201_CREATED,
)
def upload_resume(
    user: CurrentUser,
    db: DBSession,
    file: Annotated[UploadFile, File()],
) -> APIResponse[ResumePublic]:
    return APIResponse(
        data=resume_service.upload(db, user, file),
        message="Resume processed. Extracted skills are inferred, not verified facts.",
    )


@router.get("/me/resumes/{resume_id}", response_model=APIResponse[ResumePublic])
def get_resume(
    resume_id: UUID, user: CurrentUser, db: DBSession
) -> APIResponse[ResumePublic]:
    return APIResponse(data=resume_service.get_resume(db, user, resume_id))
