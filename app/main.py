"""
main.py — FastAPI application entry point.

Global exception handler ensures raw tracebacks are never exposed to clients.
All error responses follow the structured format: {"error": "...", "detail": "..."}.
"""
import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import engine, Base
from app.routers import applications

# ---------------------------------------------------------------------------
# Create tables on startup (for SQLite / quick-start without Alembic)
# In production the Alembic migration (alembic upgrade head) handles this.
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Consumer Credit Risk Verification API",
    description=(
        "A transparent, rule-based credit risk scoring API that mirrors the "
        "consumer-data-to-risk-signal pipelines operated by credit reporting "
        "companies. Scoring is deterministic and fully auditable — not a "
        "black-box ML model."
    ),
    version="1.0.0",
    contact={
        "name": "Credit Risk API",
    },
    license_info={
        "name": "MIT",
    },
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(applications.router)


# ---------------------------------------------------------------------------
# Global exception handler — never leak raw tracebacks
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full traceback server-side (visible in Render / GitHub Actions logs)
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please contact support.",
        },
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"], summary="Health check")
def health_check():
    """Returns service status. Useful for Render health probes."""
    return {"status": "ok", "service": "credit-risk-api"}
