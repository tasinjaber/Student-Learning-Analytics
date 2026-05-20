from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_routes import router as auth_router
from app.api.dataset_routes import router as dataset_router
from app.api.routes import router as analytics_router

app = FastAPI(
    title="Student Learning Analytics API",
    description="REST API for student engagement analytics dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "https://project2.tasinjaber.com",
        "https://www.project2.tasinjaber.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health():
    return {"message": "Student Learning Analytics API is running"}


app.include_router(analytics_router)
app.include_router(auth_router)
app.include_router(dataset_router)
