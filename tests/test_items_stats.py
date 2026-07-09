"""Integration tests for GET /items/stats/summary."""


def test_get_items_stats_empty(client):
    """GET /items/stats/summary returns stats for empty database."""
    response = client.get("/items/stats/summary")
    assert response.status_code == 200
    assert response.json() == {
        "total_items": 0,
        "average_price": 0.0,
        "min_price": None,
        "max_price": None,
        "uncategorized_count": 0,
        "by_category": [],
    }


def test_get_items_stats(client, create_item):
    """GET /items/stats/summary returns statistics about items."""
    create_item(name="A", price=10.0)
    create_item(name="B", price=20.0)
    create_item(name="C", price=30.0)
    response = client.get("/items/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 3
    assert data["average_price"] == 20.0
    assert data["min_price"] == 10.0
    assert data["max_price"] == 30.0
    assert data["uncategorized_count"] == 3
    assert data["by_category"] == []


def test_get_items_stats_by_category(client, auth_headers, create_category, create_item):
    """GET /items/stats/summary includes per-category breakdown."""
    tools = create_category(name="Tools")
    books = create_category(name="Books")
    create_item(name="Hammer", price=10.0, category_id=tools["id"])
    create_item(name="Drill", price=30.0, category_id=tools["id"])
    create_item(name="Novel", price=15.0, category_id=books["id"])
    create_item(name="Loose", price=5.0)

    response = client.get("/items/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 4
    assert data["uncategorized_count"] == 1
    assert len(data["by_category"]) == 2
    assert data["by_category"][0] == {
        "category_id": books["id"],
        "category_name": "Books",
        "item_count": 1,
        "average_price": 15.0,
    }
    assert data["by_category"][1] == {
        "category_id": tools["id"],
        "category_name": "Tools",
        "item_count": 2,
        "average_price": 20.0,
    }
