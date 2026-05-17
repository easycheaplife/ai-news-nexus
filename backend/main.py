from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.news import router as news_router
from app.api.v1.insights import router as insights_router
from app.api.v1.discovery import router as discovery_router
from app.api.v1.targets import router as targets_router
from app.api.v1.media import router as media_router
from app.core.config import settings
from app.db.session import engine
from app.models.news import Base

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news_router, prefix="/news", tags=["news"])
app.include_router(insights_router, prefix="/insights", tags=["insights"])
app.include_router(discovery_router, prefix="/discovery", tags=["discovery"])
app.include_router(targets_router, prefix="/targets", tags=["targets"])
app.include_router(media_router, prefix="/media", tags=["media"])

# 挂载静态文件分发目录 (/f 开头)
app.mount("/f", StaticFiles(directory="data/media"), name="media")

@app.get("/")
def root():
    return {"message": "Welcome to AI News Nexus API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
