import pytest
from fastapi.testclient import TestClient
from main import app
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "API Commandes MSPR4" in data["status"]
    assert data["project"] == "MSPR4_Commandes"

def test_stats():
    response = client.get("/stats", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "nombre_commandes" in data
    assert "nombre_produits" in data
    assert "montant_total" in data

def test_list_existing_commandes():
    response = client.get("/commandes", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_commande():
    test_order_id = f"test_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    response = client.post(
        "/commandes",
        headers=HEADERS,
        json={
            "order_id": test_order_id,
            "customer_id": "customer_test_456",
            "created_at": "2024-01-01T10:00:00",
            "total_amount": 150.50,
            "produits": [
                {
                    "product_id": "prod_1",
                    "product_name": "Test Product",
                    "price": 75.25,
                    "description": "Description du produit test",
                    "color": "Rouge",
                    "stock": 10
                },
                {
                    "product_id": "prod_2",
                    "product_name": "Another Product",
                    "price": 75.25,
                    "description": "Autre produit test",
                    "color": "Bleu",
                    "stock": 5
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == test_order_id
    assert data["total_amount"] == 150.50
    assert len(data["produits"]) == 2
    global created_commande_id, created_order_id
    created_commande_id = data["id"]
    created_order_id = data["order_id"]

def test_get_commande():
    response = client.get(f"/commandes/{created_commande_id}", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_commande_id

def test_get_commande_by_order_id():
    response = client.get(f"/commandes/order/{created_order_id}", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == created_order_id

def test_list_commandes():
    response = client.get("/commandes", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_produits_commande():
    response = client.get(f"/commandes/{created_order_id}/produits", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

def test_add_produit_to_commande():
    response = client.post(
        f"/commandes/{created_order_id}/produits",
        headers=HEADERS,
        json={
            "product_id": "prod_3",
            "product_name": "New Product",
            "price": 25.00,
            "description": "Nouveau produit ajouté",
            "color": "Vert",
            "stock": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "New Product"
    assert data["order_id"] == created_order_id

def test_update_commande():
    response = client.put(
        f"/commandes/{created_commande_id}",
        headers=HEADERS,
        json={
            "total_amount": 200.00,
            "customer_id": "updated_customer_789"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == 200.00
    assert data["customer_id"] == "updated_customer_789"

def test_delete_commande():
    response = client.delete(f"/commandes/{created_commande_id}", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["message"] == "Commande supprimée avec succès"

def test_protected_route_without_token():
    response = client.get("/commandes")
    assert response.status_code == 403

def test_commande_not_found():
    response = client.get("/commandes/99999", headers=HEADERS)
    assert response.status_code == 404 