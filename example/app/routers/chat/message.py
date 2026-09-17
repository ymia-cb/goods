from typing import Annotated

from fastapi import APIRouter
from fastapi import Header

from example.app.schemas.admin.user import CurrentUser
from example.app.dependencies import MessageServiceDep,get_auth_service
from example.app.schemas.chat.message import ChatMessageRequest
from example.app.schemas.chat.conversation import ConversationMessageResponse


router = APIRouter(tags=["聊天路由"],prefix="/api/v1/chat")


@router.post("/messages",response_model=ConversationMessageResponse)
async def accept_user_message(
        chat_message: ChatMessageRequest,
        message_service: MessageServiceDep,
        authorization: Annotated[str | None, Header()]=None
):
    authorization_user: CurrentUser = get_auth_service().get_auth_user(authorization,"customer")

    result = message_service.accept_message_user(chat_message, authorization_user.user_id)
    return result