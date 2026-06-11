from fastapi import FastAPI
from app.routes.agent import router

app = FastAPI(title="Cortex Backend API")

app.include_router(router)

@app.get("/")
def home():
    return {
        "message": "Backend running"
    }