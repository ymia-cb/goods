import uvicorn


from example.common.config import Settings
from example.common.event_loop import run_async

async def server():
    settings = Settings()
    server = uvicorn.Server(
        uvicorn.Config(
            app="app.app:app",
            host=settings.api_host,
            port=settings.api_port,
            loop="none"
        )
    )
    await server.serve()



if __name__ == '__main__':
    run_async(server())


