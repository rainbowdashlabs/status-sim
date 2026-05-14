from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import asyncio
from contextlib import asynccontextmanager

from api import router, frontend_dist  # type: ignore
from manager import manager  # type: ignore
from logging_conf import setup_logging  # type: ignore

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        await manager.init_redis(redis_url)

    tasks = [asyncio.create_task(cleanup_task())]

    if os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes"):
        from demo import run_demo  # type: ignore
        tasks.append(asyncio.create_task(run_demo()))

    yield

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await manager.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(router)

if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


async def cleanup_task():
    while True:
        await asyncio.sleep(60)
        await manager.cleanup_inactive()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
