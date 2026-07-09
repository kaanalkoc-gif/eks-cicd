"""Unit tests for CategoryService (no HTTP layer)."""

from decimal import Decimal

import pytest

from app.exceptions import CategoryInUseError, CategoryNameExistsError, CategoryNotFoundError
from app.schemas import CategoryCreate, CategoryUpdate, ItemCreate
from app.services import CategoryService, ItemService


def test_get_by_id_returns_category(db):
    """get_by_id returns the category when it exists."""
    created = CategoryService.create(db, CategoryCreate(name="Tools", description="Hand tools"))
    category = CategoryService.get_by_id(db, created.id)
    assert category.name == "Tools"
    assert category.description == "Hand tools"


def test_get_by_id_raises_when_missing(db):
    """get_by_id raises CategoryNotFoundError for unknown ids."""
    with pytest.raises(CategoryNotFoundError) as exc_info:
        CategoryService.get_by_id(db, 999)
    assert exc_info.value.category_id == 999


def test_create_persists_category(db):
    """create adds a category to the database."""
    category = CategoryService.create(db, CategoryCreate(name="Books"))
    assert category.id is not None
    assert category.name == "Books"
    assert CategoryService.get_by_id(db, category.id).name == "Books"


def test_create_raises_duplicate_name(db):
    """create raises CategoryNameExistsError when the name is taken."""
    CategoryService.create(db, CategoryCreate(name="Tools"))
    with pytest.raises(CategoryNameExistsError) as exc_info:
        CategoryService.create(db, CategoryCreate(name="Tools"))
    assert exc_info.value.name == "Tools"


def test_update_partial(db):
    """update changes only provided fields."""
    created = CategoryService.create(db, CategoryCreate(name="Tools", description="Old"))
    updated = CategoryService.update(
        db,
        created.id,
        CategoryUpdate(description="New description"),
    )
    assert updated.name == "Tools"
    assert updated.description == "New description"


def test_update_raises_duplicate_name(db):
    """update raises CategoryNameExistsError when renaming to an existing name."""
    CategoryService.create(db, CategoryCreate(name="Tools"))
    books = CategoryService.create(db, CategoryCreate(name="Books"))
    with pytest.raises(CategoryNameExistsError) as exc_info:
        CategoryService.update(db, books.id, CategoryUpdate(name="Tools"))
    assert exc_info.value.name == "Tools"


def test_delete_removes_category(db):
    """delete removes the category when no items reference it."""
    created = CategoryService.create(db, CategoryCreate(name="Tools"))
    CategoryService.delete(db, created.id)
    with pytest.raises(CategoryNotFoundError):
        CategoryService.get_by_id(db, created.id)


def test_delete_raises_when_in_use(db):
    """delete raises CategoryInUseError when items reference the category."""
    category = CategoryService.create(db, CategoryCreate(name="Tools"))
    ItemService.create(
        db,
        ItemCreate(name="Hammer", price=Decimal("10.00"), category_id=category.id),
    )
    with pytest.raises(CategoryInUseError) as exc_info:
        CategoryService.delete(db, category.id)
    assert exc_info.value.category_id == category.id


def test_list_categories_paginated(db):
    """list_categories returns a page of rows and the total count."""
    CategoryService.create(db, CategoryCreate(name="Alpha"))
    CategoryService.create(db, CategoryCreate(name="Beta"))
    CategoryService.create(db, CategoryCreate(name="Gamma"))

    rows, total = CategoryService.list_categories(db, skip=1, limit=1)
    assert total == 3
    assert len(rows) == 1
    assert rows[0].name == "Beta"
