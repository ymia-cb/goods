from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from example.app.respositories.admin.admin import AdminMetricsRepository
from example.app.services.admin.admin import AdminMetricsService
from example.app.services.admin.auth import AuthService
from example.app.services.chat.conversation import ConversationService
from example.app.services.chat.turn import TurnService
from example.app.services.admin.handoff import HandoffService
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


def get_message_service(session: Annotated[AsyncSession, Depends(get_db_session)],
                        conversation_service: ConversationServiceDep,
                        turn_service: TurnServiceDep,
                        outbox_service: RealTimeOutBoxServiceDep):

    return MessageService(session, conversation_service, turn_service, outbox_service)


MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]


async def get_handoff_service(
        session: Annotated[AsyncSession, Depends(get_db_session)]
) -> HandoffService:
    return HandoffService(session)


HandoffServiceDep = Annotated[
    HandoffService,
    Depends(get_handoff_service)
]



async def get_admin_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AdminMetricsService:
    return AdminMetricsService(AdminMetricsRepository(session))


AdminMetricsServiceDep = Annotated[AdminMetricsService, Depends(get_admin_service)]

