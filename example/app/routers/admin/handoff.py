from typing import Annotated

from fastapi import APIRouter, Header, status

from example.app.dependencies import HandoffServiceDep, get_auth_service
from example.app.schemas.admin.handoff import OpenHandoffResponse, HandoffReplyRequest

router = APIRouter(
    prefix="/api/v1/handoffs",
    tags=["人工工单路由"]
)


@router.get("", response_model=list[OpenHandoffResponse])
async def list_handoffs(
        handoff_service: HandoffServiceDep,
        authorization: Annotated[str | None, Header()] = None
):
    """返回客服可以处理的开放工单。"""
    get_auth_service().auth_service.get_authorized_user(authorization, "agent")
    return await handoff_service.list_open_handoffs()

@router.post("/{handoff_id}/accept",
    status_code=status.HTTP_204_NO_CONTENT)
async def  accept_handoff(
        handoff_id: str,
        handoff_service: HandoffServiceDep,
        authorization: Annotated[str | None, Header()] = None
):
    current_user = await get_auth_service().get_authorized_user(authorization, "agent")
    await handoff_service.accept_handoff(handoff_id, current_user.user_id)


@router.post("/{handoff_id}/messages", status_code=status.HTTP_204_NO_CONTENT)
async def replay_handoff(handoff_id: str, reply_request: HandoffReplyRequest, authorization: Annotated[str | None, Header()] = None):
    current_user = await get_auth_service().get_authorized_user(authorization, "agent")
    await reply_request.replay_handoff(handoff_id, current_user.user_id,message_id=reply_request.message_id, text=reply_request.text)


@router.post("/{handoff_id}/resolve",
    status_code=status.HTTP_204_NO_CONTENT)
async def resolve_handoff(
        handoff_id: str,
        handoff_service: HandoffServiceDep,
        authorization: Annotated[str | None, Header()] = None
):
    current_user = await get_auth_service().get_authorized_user(authorization, "agent")
    await handoff_service.resolve_handoff(handoff_id, current_user.user_id)




