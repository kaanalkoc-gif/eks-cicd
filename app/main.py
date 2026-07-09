"""
FastAPI application factory.
Run with: uvicorn main:app --reload
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.exceptions import (
    CategoryInUseError,
    CategoryNameExistsError,
    CategoryNotFoundError,
    ItemNotFoundError,
    UserEmailExistsError,
)
from app.routers import auth, categories, health, items

logger = logging.getLogger("app")


def configure_logging() -> None:
    """Configure application logging from settings."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

    app_logger = logging.getLogger("app")
    app_logger.disabled = False
    app_logger.setLevel(log_level)
    app_logger.propagate = False
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(log_format))
        app_logger.addHandler(handler)


def run_migrations() -> None:
    """Apply pending Alembic migrations (same as docker compose startup)."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    run_migrations()
    configure_logging()  # after Alembic — its fileConfig resets logging handlers
    logger.info("Starting application")
    yield
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title="First FastAPI",
        description="A simple API to learn FastAPI basics",
        version="0.1.0",
        lifespan=lifespan,
        redoc_url=None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log each request with method, path, status, and duration."""
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        log = logger.warning if response.status_code >= 400 else logger.info
        log(
            "%s %s %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @application.exception_handler(ItemNotFoundError)
    async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
        """Return a consistent 404 for missing items."""
        return JSONResponse(
            status_code=404,
            content={"detail": "Item not found", "code": "ITEM_NOT_FOUND"},
        )

    @application.exception_handler(CategoryNotFoundError)
    async def category_not_found_handler(request: Request, exc: CategoryNotFoundError):
        """Return a consistent 404 for missing categories."""
        return JSONResponse(
            status_code=404,
            content={"detail": "Category not found", "code": "CATEGORY_NOT_FOUND"},
        )

    @application.exception_handler(CategoryInUseError)
    async def category_in_use_handler(request: Request, exc: CategoryInUseError):
        """Return 409 when a category still has items."""
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Category has items and cannot be deleted",
                "code": "CATEGORY_IN_USE",
            },
        )

    @application.exception_handler(CategoryNameExistsError)
    async def category_name_exists_handler(request: Request, exc: CategoryNameExistsError):
        """Return 409 when a category name is already taken."""
        return JSONResponse(
            status_code=409,
            content={
                "detail": f"Category name '{exc.name}' already exists",
                "code": "CATEGORY_NAME_EXISTS",
            },
        )

    @application.exception_handler(UserEmailExistsError)
    async def user_email_exists_handler(request: Request, exc: UserEmailExistsError):
        """Return 409 when a user email is already registered."""
        return JSONResponse(
            status_code=409,
            content={
                "detail": f"User email '{exc.email}' already exists",
                "code": "USER_EMAIL_EXISTS",
            },
        )

    @application.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError):
        """Return consistent 500 for database errors."""
        logger.exception("Database error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error", "code": "DB_ERROR"},
        )

    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(categories.router)
    application.include_router(items.router)

    @application.get("/redoc", include_in_schema=False)
    async def redoc_html() -> HTMLResponse:
        """ReDoc with a pinned JS bundle (FastAPI's default redoc@next 404s on jsdelivr)."""
        return get_redoc_html(
            openapi_url=application.openapi_url,
            title=f"{application.title} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
        )

    return application


app = create_app()
