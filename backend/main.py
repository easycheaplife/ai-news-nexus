from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.news import router as news_router
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

@app.get("/")
def root():
    return {"message": "Welcome to AI News Nexus API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
