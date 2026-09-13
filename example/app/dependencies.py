from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from example.app.services.auth import AuthService
from example.app.services.chat.conversation import ConversationService
from example.infrastucture.db import get_db_session

def get_auth_service():
    return AuthService()

def get_conversation_service(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return get_conversation_service(session)




ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]