"""FastAPI application entrypoint.

Wires routers, CORS, static frontend and healthcheck.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import activities, auth, destinations, favorites, recommendations

settings = get_settings()

app = FastAPI(
    title="Travel Recommendation API",
    version="1.0.0",
    description="Personalized travel recommendations based on user preferences.",
)

# Configure CORS_ORIGINS in .env for real domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(destinations.router)
app.include_router(activities.router)
app.include_router(recommendations.router)
app.include_router(favorites.router)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    """Return HTTP 200 when the app is running."""
    return {"status": "ok"}


# Serve the SPA from /static and expose the index at the root.
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        """Serve the SPA entry point for all non-API root requests."""
        return FileResponse(str(STATIC_DIR / "index.html"))
