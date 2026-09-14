from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from example.app.services.auth import AuthService
from example.app.services.chat.conversation import ConversationService
from example.app.services.chat.turn import TurnService
from example.app.services.realtime import RealTimeOutBoxService
from example.infrastucture.db import get_db_session
from example.app.services.chat.message import MessageService

def get_auth_service():
    return AuthService()

def get_conversation_service(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return get_conversation_service(session)


ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]

def get_turn_service(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return TurnService(session)


TurnServiceDep = Annotated[TurnService, Depends(get_turn_service)]

def get_outbox_service(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return RealTimeOutBoxService(session)


RealTimeOutBoxServiceDep = Annotated[RealTimeOutBoxService, Depends(get_outbox_service)]


def get_message_service(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return get_message_service(session)


MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]


