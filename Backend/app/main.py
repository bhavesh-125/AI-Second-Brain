
from fastapi import FastAPI

from app.database import engine, Base
from app.models.user import User
from app.routes import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Second Brain API",
              description="Your personal AI-powered knowledge system",
    version="0.1.0")

app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "AI Second Brain backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}
