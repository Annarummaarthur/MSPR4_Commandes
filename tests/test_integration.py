# tests/test_integration.py


def test_health_endpoint(client):
    """Test du health check"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Orders API is running"


def test_orders_workflow(client, auth_headers):
    """Test du workflow complet des commandes"""

    order_data = {
        "customer_id": "TEST_CLIENT_001",
        "customer_name": "Test Client",
        "items": [
            {
                "product_id": "PROD_001",
                "product_name": "Test Coffee",
                "product_price": 19.99,
                "quantity": 1,
            }
        ],
    }

    response = client.post("/orders", json=order_data, headers=auth_headers)
    assert response.status_code == 200
    order_id = response.json()["order_id"]

    response = client.get(f"/orders/{order_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["order_id"] == order_id


def test_multiple_requests_performance(client, auth_headers):
    """Test de performance basique avec requêtes multiples"""

    for i in range(5):
        response = client.get("/orders", headers=auth_headers)
        assert response.status_code == 200
