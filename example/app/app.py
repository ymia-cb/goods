from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from example.common.config import get_settings
from example.app.routers.chat import conversation
app = FastAPI(description="fastapi集成的客服服务")
app.include_router(conversation.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)