from fastapi import APIRouter,Header
from typing import Annotated

from example.app.dependencies import ConversationServiceDep,get_auth_service
from example.app.schemas.chat.conversation import CurrentConversationResponse,ConversationDetailResponse

router = APIRouter(prefix="/api/v1", tags=["聊天会话路由"])

@router.post("/conversation/current",response_model=CurrentConversationResponse)
async def get_current_conversation(conversation_service :ConversationServiceDep,
                      authorization: Annotated[str | None, Header()]=None):


    authorized_user = get_auth_service().get_auth_user(authorization,"customer")
    result = await  conversation_service.get_current_conversation(authorized_user)
    return result


@router.get("/conversations/{conversation_id}",response_model=ConversationDetailResponse)
async def get_conversation_detail(conversation_id: str,
                                  conversation_service :ConversationServiceDep,
                                  authorization: Annotated[str | None, Header()]=None):


    authorized_user = get_auth_service().get_auth_user(authorization,"agent", "admin")
    conversation_detail = conversation_service.get_conversation_detail(conversation_id)
    return conversation_detail







