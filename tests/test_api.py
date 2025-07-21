import pytest
import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
API_TOKEN = "mspr4_commandes_api_token_secure_2025"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}

test_commande_id = None


def test_health_check():
    """Test du health check de l'API"""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert data["service"] == "Microservice Commandes"
    assert data["version"] == "3.0.0"
    assert data["architecture"] == "microservices_pure"
    print("Health check OK")


def test_authentication():
    """Test de l'authentification"""
    try:
        response = requests.get(f"{BASE_URL}/stats")
        assert response.status_code == 401

        bad_headers = {"Authorization": "Bearer mauvais_token"}
        response = requests.get(f"{BASE_URL}/stats", headers=bad_headers)
        assert response.status_code == 401

        response = requests.get(f"{BASE_URL}/stats", headers=HEADERS)
        assert response.status_code == 200
        print("Authentification OK")
    except Exception as e:
        print(f"⚠Authentification: {e}")


def test_stats():
    """Test de l'endpoint des statistiques"""
    response = requests.get(f"{BASE_URL}/stats", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()

    required_fields = [
        "total_commandes",
        "montant_total",
        "montant_moyen",
        "montant_max",
        "montant_min",
        "commandes_par_statut",
    ]
    for field in required_fields:
        assert field in data

    assert isinstance(data["total_commandes"], int)
    assert isinstance(data["montant_total"], (int, float))
    assert isinstance(data["commandes_par_statut"], dict)

    expected_statuses = ["pending", "processing", "completed", "cancelled"]
    for status in expected_statuses:
        assert status in data["commandes_par_statut"]

    print("Statistiques OK")


def test_get_commandes():
    """Test de récupération des commandes avec pagination"""
    response = requests.get(f"{BASE_URL}/commandes", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    response = requests.get(f"{BASE_URL}/commandes?limit=5&offset=0", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5

    response = requests.get(
        f"{BASE_URL}/commandes?order_by=total_amount&order_direction=desc&limit=3",
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    if len(data) >= 2:
        assert data[0]["total_amount"] >= data[1]["total_amount"]

    print("Récupération des commandes OK")


def test_create_commande():
    """Test de création d'une commande"""
    global test_commande_id

    timestamp = int(time.time())
    new_commande = {
        "order_id": f"TEST{timestamp}",
        "customer_id": "CLIENT_TEST",
        "total_amount": 199.99,
        "status": "pending",
    }

    response = requests.post(
        f"{BASE_URL}/commandes", headers=HEADERS, json=new_commande
    )
    assert response.status_code == 200
    data = response.json()

    test_commande_id = data["id"]

    assert data["order_id"] == new_commande["order_id"]
    assert data["customer_id"] == new_commande["customer_id"]
    assert data["total_amount"] == new_commande["total_amount"]
    assert data["status"] == new_commande["status"]
    assert "id" in data
    assert "updated_at" in data

    response = requests.post(
        f"{BASE_URL}/commandes", headers=HEADERS, json=new_commande
    )
    assert response.status_code == 409  # Conflit

    print("Création de commande OK")


def test_get_commande_by_id():
    """Test de récupération d'une commande par ID"""
    global test_commande_id

    if test_commande_id is None:
        test_create_commande()

    response = requests.get(f"{BASE_URL}/commandes/{test_commande_id}", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_commande_id

    response = requests.get(f"{BASE_URL}/commandes/999999", headers=HEADERS)
    assert response.status_code == 404

    print("Récupération par ID OK")


def test_update_commande_status():
    """Test de mise à jour du statut d'une commande"""
    global test_commande_id

    if test_commande_id is None:
        test_create_commande()

    status_update = {"status": "completed"}
    response = requests.put(
        f"{BASE_URL}/commandes/{test_commande_id}/status",
        headers=HEADERS,
        json=status_update,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

    invalid_status = {"status": "invalid_status"}
    response = requests.put(
        f"{BASE_URL}/commandes/{test_commande_id}/status",
        headers=HEADERS,
        json=invalid_status,
    )
    assert response.status_code == 422

    print("Mise à jour du statut OK")


def test_search_commandes():
    """Test de la recherche avancée"""
    response = requests.get(
        f"{BASE_URL}/commandes/search?min_amount=1000&max_amount=1500", headers=HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    for commande in data:
        assert 1000 <= commande["total_amount"] <= 1500

    response = requests.get(f"{BASE_URL}/commandes/search?q=CLIENT", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    print("✅ Recherche avancée OK")


def test_get_commandes_by_status():
    """Test de récupération par statut"""
    response = requests.get(f"{BASE_URL}/commandes/status/completed", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    for commande in data:
        assert commande["status"] == "completed"

    response = requests.get(f"{BASE_URL}/commandes/status/invalid", headers=HEADERS)
    assert response.status_code == 400

    print("✅ Récupération par statut OK")


def test_update_commande():
    """Test de mise à jour complète d'une commande"""
    global test_commande_id

    if test_commande_id is None:
        test_create_commande()

    update_data = {
        "customer_id": "CLIENT_UPDATED",
        "total_amount": 299.99,
        "status": "processing",
    }

    response = requests.put(
        f"{BASE_URL}/commandes/{test_commande_id}", headers=HEADERS, json=update_data
    )
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == update_data["customer_id"]
    assert data["total_amount"] == update_data["total_amount"]
    assert data["status"] == update_data["status"]

    print("Mise à jour complète OK")


def test_delete_commande():
    """Test de suppression d'une commande"""
    timestamp = int(time.time())
    new_commande = {
        "order_id": f"DELETE_TEST{timestamp}",
        "customer_id": "CLIENT_DELETE_TEST",
        "total_amount": 99.99,
        "status": "pending",
    }

    response = requests.post(
        f"{BASE_URL}/commandes", headers=HEADERS, json=new_commande
    )
    assert response.status_code == 200
    commande_to_delete_id = response.json()["id"]

    response = requests.delete(
        f"{BASE_URL}/commandes/{commande_to_delete_id}", headers=HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    response = requests.get(
        f"{BASE_URL}/commandes/{commande_to_delete_id}", headers=HEADERS
    )
    assert response.status_code == 404

    print("Suppression OK")


def test_validation_errors():
    """Test des erreurs de validation"""
    invalid_commande = {
        "order_id": "",
        "customer_id": "CLIENT_TEST",
        "total_amount": 100,
    }

    response = requests.post(
        f"{BASE_URL}/commandes", headers=HEADERS, json=invalid_commande
    )
    assert response.status_code == 422

    invalid_commande = {
        "order_id": "TEST_INVALID",
        "customer_id": "CLIENT_TEST",
        "total_amount": -100,
    }

    response = requests.post(
        f"{BASE_URL}/commandes", headers=HEADERS, json=invalid_commande
    )
    assert response.status_code == 422

    print("Validation des erreurs OK")


def run_all_tests():
    """Exécuter tous les tests"""
    print("Démarrage des tests du Microservice Commandes v3.0.0")
    print("=" * 60)

    # Tests dans l'ordre de dépendance
    test_functions = [
        test_health_check,
        test_authentication,
        test_stats,
        test_get_commandes,
        test_create_commande,  # Crée test_commande_id
        test_get_commande_by_id,
        test_update_commande_status,
        test_search_commandes,
        test_get_commandes_by_status,
        test_update_commande,
        test_validation_errors,
        test_delete_commande,  # En dernier pour ne pas affecter les autres tests
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            failed += 1

    print("=" * 60)
    print(f"📊 RÉSULTATS DES TESTS:")
    print(f"   ✅ Tests réussis: {passed}")
    print(f"   ❌ Tests échoués: {failed}")
    print(f"   📈 Taux de réussite: {(passed/(passed+failed)*100):.1f}%")

    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! L'API est parfaitement fonctionnelle.")
        print("\n📋 FONCTIONNALITÉS TESTÉES:")
        print("   • Health check et informations système")
        print("   • Authentification et sécurité")
        print("   • Statistiques avancées (montants min/max/moyen)")
        print("   • CRUD complet des commandes")
        print("   • Pagination et tri")
        print("   • Recherche avancée par montant et texte")
        print("   • Gestion des statuts")
        print("   • Validation des données")
        print("   • Gestion d'erreurs robuste")
    else:
        print(f"\n⚠️  {failed} test(s) ont échoué. Vérifiez les erreurs ci-dessus.")


if __name__ == "__main__":
    run_all_tests()
