from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth_routes import router as auth_router
from app.config import get_settings
from app.privacy_routes import account_router
from app.privacy_routes import router as privacy_router
from app.routers import contacts_router, outreach_router
from app.routers import router as student_profiles_router

settings = get_settings()
app = FastAPI(
    title="Career Network Copilot API",
    version="0.1.0",
    description="Human-in-the-loop career networking assistant API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        settings.frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def enforce_request_origin(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        trusted = {
            item.strip().rstrip("/") for item in settings.trusted_origins.split(",") if item.strip()
        }
        if not origin or origin.rstrip("/") not in trusted:
            return JSONResponse(status_code=403, content={"detail": "Invalid request origin"})
    return await call_next(request)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(student_profiles_router)
app.include_router(contacts_router)
app.include_router(outreach_router)
app.include_router(auth_router)
app.include_router(privacy_router)
app.include_router(account_router)
