from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from example.app.respositories.turn import ConversationTurnRepository


from example.common.config import get_settings
from example.common.utils import get_utcnow
from example.models.models import Message, Conversation, ConversationTurn


class TurnService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.turn_repo = ConversationTurnRepository(session)


    async def add_message_to_turn(self, message: Message, conversation: Conversation) ->ConversationTurn:

        conversation.input_revision += 1
        message.input_revision = conversation.input_revision
        turn = await self.turn_repo.find_conversation_by_id(conversation.id)

        now = get_utcnow()

        delay = timedelta(milliseconds=self.settings.message_merge_delay_ms)

        if turn:
            turn.collect_until = min(now + delay, turn.max_collect_until)
            return turn
        turn = ConversationTurn(
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            status="COLLECTING",
            collect_until=now + delay,
            start_revision=conversation.answered_revision+1,
            max_collect_until=now + timedelta(milliseconds=self.settings.message_merge_max_wait_ms)
        )
        self.turn_repo.add_turn(turn)
        return turn