import asyncio

from fastapi import APIRouter
from redis import RedisError
from starlette.websockets import WebSocket, WebSocketDisconnect

from example.app.dependencies import get_auth_service
from example.app.services.realtime import STAFF_CHANNEL, user_channel
from example.infrastucture.redis import redis_client

router = APIRouter()


@router.websocket("/api/v1/realtime")
async def realtime_socket(websocket: WebSocket):
    await websocket.accept()
    try:
        auth_message = await websocket.receive_json()
        current_user = get_auth_service().get_authorized_user(str(auth_message["token"]))

    except (KeyError, TypeError):
        await websocket.close(401, "无效的token")
        return


    channel = user_channel(current_user.user_id) if current_user.role == "customer" else STAFF_CHANNEL

    pubsub = redis_client.pubsub()

    try:
        await pubsub.subscribe(channel)
        await websocket.send_json({"type": "connected"})
        async def forward_events():
            try:
                async for item in pubsub.listen():
                    if item["type"] == "message":
                        await  websocket.send_text(item["data"])
            except RedisError:
                await websocket.close()

        forward_task = asyncio.create_task(forward_events())
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            forward_task.cancel()
            await asyncio.gather(forward_task,return_exceptions=True)
    finally:
        await pubsub.aclose()