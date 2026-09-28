from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.assistant import AssistantAnswerPublic, AssistantAskRequest
from app.schemas.common import APIResponse
from app.services.assistant_service import assistant_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=APIResponse[AssistantAnswerPublic])
def ask_assistant(
    user: CurrentUser,
    db: DBSession,
    payload: AssistantAskRequest,
) -> APIResponse[AssistantAnswerPublic]:
    return APIResponse(data=assistant_service.ask(db, user, payload.question))


@router.get("/turns", response_model=APIResponse[list[AssistantAnswerPublic]])
def list_assistant_turns(
    user: CurrentUser,
    db: DBSession,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> APIResponse[list[AssistantAnswerPublic]]:
    return APIResponse(data=assistant_service.list_turns(db, user, limit=limit))
