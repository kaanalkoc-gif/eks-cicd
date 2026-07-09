"""Category CRUD routes."""

import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.rate_limit import limiter
from app.schemas import CategoryCreate, CategoryListResponse, CategoryResponse, CategoryUpdate
from app.services import CategoryService

logger = logging.getLogger("app")

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse)
def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List categories with pagination metadata."""
    rows, total = CategoryService.list_categories(db, skip=skip, limit=limit)
    return CategoryListResponse(
        items=[CategoryResponse.model_validate(row) for row in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a single category by id."""
    row = CategoryService.get_by_id(db, category_id)
    return CategoryResponse.model_validate(row)


@router.post("", response_model=CategoryResponse, status_code=201)
@limiter.limit("60/minute")
def create_category(
    request: Request,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new category (requires JWT authentication)."""
    row = CategoryService.create(db, category)
    return CategoryResponse.model_validate(row)


@router.patch("/{category_id}", response_model=CategoryResponse)
@limiter.limit("60/minute")
def update_category(
    request: Request,
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a category (requires JWT authentication)."""
    row = CategoryService.update(db, category_id, category)
    return CategoryResponse.model_validate(row)


@router.delete("/{category_id}", status_code=204)
@limiter.limit("60/minute")
def delete_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a category when no items reference it (requires JWT)."""
    CategoryService.delete(db, category_id)
    logger.info("Deleted category id=%s", category_id)
    return None
