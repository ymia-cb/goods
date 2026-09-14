from enum import StrEnum
from typing import Any

from pydantic import Field
from pydantic import BaseModel

from example.app.schemas.conversation import ConversationMode


class MessageType(StrEnum):
    TEXT = "text"
    OBJECT = "object"



class MessageRole(StrEnum):
    AI = "ai"
    USER = "user"
    HUMAN = "human"



class ChatMessageRequest(BaseModel):
    message_id: str = Field(min_length=4, max_length=80)
    type: MessageType
    content: dict[str, Any]


class ChatMessageResponse(BaseModel):
    conversation_id: str
    mode: ConversationMode


