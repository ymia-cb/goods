from fastapi import APIRouter,Header
from typing import Annotated


from example.app.dependencies import conversation_service_dep
router = APIRouter(prefix="/api/v1", tags=["聊天会话路由"])

@router.get("/conversation/current")
async def get_current(service:conversation_service_dep,
                      auth=Annotated[str | None, Header()]):
    pass




