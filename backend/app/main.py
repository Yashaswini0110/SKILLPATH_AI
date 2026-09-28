from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models as _models  # noqa: F401
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError, UnavailableError
from app.core.logging import configure_logging, get_logger
from app.db.seed import seed_catalog
from app.db.session import SessionLocal
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.graph_service import graph_service

configure_logging()
logger = get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.seed_on_startup:
        db = SessionLocal()
        try:
            seed_catalog(db)
            db.commit()
            logger.info("catalog seed complete")
        except Exception:
            db.rollback()
            logger.exception("catalog seed failed")
            raise
        finally:
            db.close()
    if settings.neo4j_sync_on_startup:
        db = SessionLocal()
        try:
            graph_service.sync(db)
            logger.info("graph sync complete")
        except UnavailableError:
            logger.warning("neo4j unavailable; graph sync skipped")
        except Exception:
            logger.exception("graph sync failed")
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "SkillPath AI — evidence-based competency development. "
        "Phase 25 paginates catalog lists and rate-limits /api/v1."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.code, "message": exc.message, "details": exc.details}
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = []
    for err in exc.errors():
        details.append(
            {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
        )
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    codes = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "RATE_LIMIT_EXCEEDED",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": codes.get(exc.status_code, "HTTP_ERROR"),
                "message": str(exc.detail),
                "details": [],
            }
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("integrity error: %s", exc.orig)
    return JSONResponse(
        status_code=409,
        content={
            "error": {
                "code": "CONFLICT",
                "message": "The request conflicts with existing data",
                "details": [],
            }
        },
    )
