from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import charts, geocode, matching, panchanga, transits

app = FastAPI(title="Grahika API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(charts.router)
app.include_router(geocode.router)
app.include_router(matching.router)
app.include_router(transits.router)
app.include_router(panchanga.router)


@app.middleware("http")
async def no_cache_frontend(request, call_next):
    # Without this, browsers may reuse a stale copy of the page/JS/CSS
    # indefinitely (no explicit Cache-Control = heuristic caching kicks in),
    # which is especially confusing when this is loaded inside an iframe --
    # a plain refresh of the embedding page doesn't necessarily re-fetch the
    # iframe's own cached resources. ETag-based revalidation is still cheap.
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith((".html", ".js", ".css")):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


# API routes above take priority; this catches everything else and serves
# the static frontend, so one free web service hosts both.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
