from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router as v1_router
from app.api.v2.routes import router as v2_router
from app.core.config import settings


app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.API_V1_STR, tags=["v1"])
app.include_router(v2_router, prefix=settings.API_V2_STR, tags=["v2"])


@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
