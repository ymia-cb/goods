from typing import Annotated

from fastapi import Depends


def get_conversation_service():
    return get_conversation_service()


conversation_service_dep = Annotated[get_conversation_service, Depends(get_conversation_service)]