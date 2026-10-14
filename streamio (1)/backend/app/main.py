import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import SessionLocal
from app.routes import router


app = FastAPI(
    title="Streamio Streaming Platform API",
    version="1.0.0",
    description="Database-backed management API for the supplied Streamio dataset.",
)
logger = logging.getLogger(__name__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
@app.exception_handler(SQLAlchemyError)
async def database_error_handler(
    request: Request, error: SQLAlchemyError
) -> JSONResponse:
    original = getattr(error, "orig", None)
    error_args = getattr(original, "args", ())
    error_code = error_args[0] if error_args and isinstance(error_args[0], int) else None
    logger.error(
        "Database request failed for %s (error_type=%s, code=%s)",
        request.url.path,
        type(error).__name__,
        error_code,
    )
    if error_code == 1054:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database schema mismatch. Verify API mappings against the live columns and check backend logs."
            },
        )
    if error_code == 1146:
        return JSONResponse(
            status_code=500,
            content={"detail": "A required database table is missing. Check the live schema and backend logs."},
        )
    if error_code in {1045, 1049, 2002, 2003, 2005, 2013}:
        return JSONResponse(
            status_code=503,
            content={"detail": "Database connection failed. Check MySQL and the local backend settings."},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Database query failed. Check backend logs for safe diagnostics."},
    )



@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check MySQL is running and backend/.env is correct.",
        ) from error


app.include_router(router)