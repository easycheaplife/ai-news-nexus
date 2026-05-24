import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.v1.news import router as news_router
from app.api.v1.insights import router as insights_router
from app.api.v1.discovery import router as discovery_router
from app.api.v1.targets import router as targets_router
from app.api.v1.media import router as media_router
from app.api.v1.clusters import router as clusters_router
from app.core.config import settings
from app.db.session import engine
from app.models.news import Base

# Redis Caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        encoding="utf8",
        decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news_router, prefix="/api/news", tags=["news"])
app.include_router(insights_router, prefix="/api/insights", tags=["insights"])
app.include_router(discovery_router, prefix="/api/discovery", tags=["discovery"])
app.include_router(targets_router, prefix="/api/targets", tags=["targets"])
app.include_router(media_router, prefix="/api/media", tags=["media"])
app.include_router(clusters_router, prefix="/api/clusters", tags=["clusters"])


# Legacy support (optional, if you want both to work)
app.include_router(news_router, prefix="/news", tags=["news"])
app.include_router(insights_router, prefix="/insights", tags=["insights"])
app.include_router(discovery_router, prefix="/discovery", tags=["discovery"])
app.include_router(targets_router, prefix="/targets", tags=["targets"])
app.include_router(media_router, prefix="/media", tags=["media"])
app.include_router(clusters_router, prefix="/clusters", tags=["clusters"])
# 挂载静态文件分发目录 (/f 开头)
app.mount("/f", StaticFiles(directory="data/media"), name="media")

# 挂载前端静态文件 (Assets)
dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))
if os.path.exists(os.path.join(dist_path, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

@app.get("/")
@app.get("/report")
@app.get("/reports-list")
def serve_frontend():
    index_path = os.path.join(dist_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not build yet. Run 'npm run build' in frontend directory."}

@app.get("/api-root")
def api_root():
    return {"message": "Welcome to AI News Nexus API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
