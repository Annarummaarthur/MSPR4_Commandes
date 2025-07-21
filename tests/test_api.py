# tests/test_api.py

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Orders API is running"}


def test_create_order(client, auth_headers):
    order_data = {
        "customer_id": "CUST_001",
        "customer_name": "Jean Dupont",
        "customer_email": "jean.dupont@example.com",
        "shipping_address": "123 Rue du Café",
        "shipping_city": "Paris",
        "shipping_postal_code": "75001",
        "shipping_country": "France",
        "currency": "EUR",
        "items": [
            {
                "product_id": "PROD_001",
                "product_name": "Café Colombien",
                "product_price": 15.99,
                "quantity": 2,
                "product_sku": "COL001",
                "product_description": "Café colombien premium"
            },
            {
                "product_id": "PROD_002",
                "product_name": "Café Éthiopien",
                "product_price": 18.50,
                "quantity": 1,
                "product_sku": "ETH001",
                "product_description": "Café éthiopien single origin"
            }
        ]
    }

    response = client.post("/orders", json=order_data, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["customer_id"] == "CUST_001"
    assert data["customer_name"] == "Jean Dupont"
    assert data["status"] == "pending"
    assert len(data["items"]) == 2

    # Vérifier le calcul du montant total
    expected_total = (15.99 * 2) + (18.50 * 1)
    assert float(data["total_amount"]) == expected_total

    return data["order_id"]


def test_get_order(client, auth_headers):
    # Créer d'abord une commande
    order_id = test_create_order(client, auth_headers)

    # Récupérer la commande
    response = client.get(f"/orders/{order_id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["order_id"] == order_id
    assert data["customer_id"] == "CUST_001"


def test_list_orders(client, auth_headers):
    # Créer une commande
    test_create_order(client, auth_headers)

    # Lister les commandes
    response = client.get("/orders", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Vérifier la structure d'un résumé de commande
    order_summary = data[0]
    assert "order_id" in order_summary
    assert "customer_id" in order_summary
    assert "total_amount" in order_summary
    assert "status" in order_summary
    assert "items_count" in order_summary
    assert "created_at" in order_summary


def test_update_order_status(client, auth_headers):
    # Créer une commande
    order_id = test_create_order(client, auth_headers)

    # Mettre à jour le statut
    status_update = {
        "status": "confirmed",
        "notes": "Commande confirmée par le client"
    }

    response = client.put(f"/orders/{order_id}/status", json=status_update, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "confirmed"


def test_cancel_order(client, auth_headers):
    # Créer une commande
    order_id = test_create_order(client, auth_headers)

    # Annuler la commande
    response = client.post(f"/orders/{order_id}/cancel?reason=Demande client", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "cancelled"


def test_search_orders(client, auth_headers):
    # Créer une commande
    test_create_order(client, auth_headers)

    # Rechercher par ID client
    response = client.get("/orders/search?q=CUST_001", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_customer_orders(client, auth_headers):
    # Créer une commande
    test_create_order(client, auth_headers)

    # Récupérer les commandes du client
    response = client.get("/customers/CUST_001/orders", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(order["customer_id"] == "CUST_001" for order in data)


def test_get_orders_by_status(client, auth_headers):
    # Créer une commande
    test_create_order(client, auth_headers)

    # Récupérer les commandes par statut
    response = client.get("/orders/status/pending", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert all(order["status"] == "pending" for order in data)


def test_get_statistics(client, auth_headers):
    # Créer quelques commandes
    test_create_order(client, auth_headers)

    response = client.get("/stats", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "total_orders" in data
    assert "total_revenue" in data
    assert "average_order_value" in data
    assert "orders_by_status" in data
    assert "recent_orders_count" in data
    assert "top_customers" in data

    assert isinstance(data["total_orders"], int)
    assert data["total_orders"] >= 1


def test_unauthorized_access(client):
    # Test sans token
    response = client.get("/orders")
    assert response.status_code == 403

    # Test avec mauvais token
    bad_headers = {"Authorization": "Bearer wrong_token"}
    response = client.get("/orders", headers=bad_headers)
    assert response.status_code == 403


def test_create_order_validation(client, auth_headers):
    # Test avec données invalides - pas d'items
    invalid_order = {
        "customer_id": "CUST_001",
        "items": []
    }

    response = client.post("/orders", json=invalid_order, headers=auth_headers)
    assert response.status_code == 422

    # Test avec prix négatif
    invalid_order = {
        "customer_id": "CUST_001",
        "items": [
            {
                "product_id": "PROD_001",
                "product_name": "Test Product",
                "product_price": -10.0,
                "quantity": 1
            }
        ]
    }

    response = client.post("/orders", json=invalid_order, headers=auth_headers)
    assert response.status_code == 422


def test_order_not_found(client, auth_headers):
    response = client.get("/orders/NON_EXISTENT_ORDER", headers=auth_headers)
    assert response.status_code == 404


def test_invalid_status_update(client, auth_headers):
    # Créer une commande
    order_id = test_create_order(client, auth_headers)

    # Essayer avec un statut invalide
    invalid_status = {
        "status": "invalid_status"
    }

    response = client.put(f"/orders/{order_id}/status", json=invalid_status, headers=auth_headers)
    assert response.status_code == 422


def test_workflow_complete(client, auth_headers):
    """Test d'un workflow complet de commande"""
    # 1. Créer la commande
    order_id = test_create_order(client, auth_headers)

    # 2. Confirmer la commande
    response = client.put(f"/orders/{order_id}/status",
                          json={"status": "confirmed"}, headers=auth_headers)
    assert response.status_code == 200

    # 3. Traiter la commande
    response = client.put(f"/orders/{order_id}/status",
                          json={"status": "processing"}, headers=auth_headers)
    assert response.status_code == 200

    # 4. Expédier la commande
    response = client.put(f"/orders/{order_id}/status",
                          json={"status": "shipped"}, headers=auth_headers)
    assert response.status_code == 200

    # 5. Livrer la commande
    response = client.put(f"/orders/{order_id}/status",
                          json={"status": "delivered"}, headers=auth_headers)
    assert response.status_code == 200

    # 6. Vérifier l'état final
    response = client.get(f"/orders/{order_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "delivered"
    assert data["delivered_at"] is not None