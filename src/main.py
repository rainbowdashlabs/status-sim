from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import asyncio
from src.api import router
from src.manager import manager
from src.logging_conf import setup_logging

setup_logging()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    task = asyncio.create_task(cleanup_task())
    yield
    # Shutdown logic
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Ensure static directory exists
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include the API router
app.include_router(router)

async def cleanup_task():
    while True:
        await asyncio.sleep(60)
        await manager.cleanup_inactive()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, ws_ping_interval=20, ws_ping_timeout=20)
