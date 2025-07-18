import pytest
import httpx
import asyncio
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
API_TOKEN = os.getenv("API_TOKEN", "test_token")

@pytest.mark.asyncio
class TestIntegrationAPI:
    
    async def test_health_endpoint(self):
        """Test du health check"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/")
            assert response.status_code == 200
            
    async def test_commandes_workflow(self):
        """Test du workflow complet des commandes"""
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        
        async with httpx.AsyncClient() as client:
            # Test création commande
            commande_data = {
                "order_id": "TEST_CMD_001",
                "customer_id": "TEST_CLIENT_001",
                "total_amount": 99.99,
                "status": "pending"
            }
            
            response = await client.post(
                f"{API_BASE_URL}/commandes",
                json=commande_data,
                headers=headers
            )
            assert response.status_code == 201
            commande_id = response.json()["id"]
            
            # Test récupération commande
            response = await client.get(
                f"{API_BASE_URL}/commandes/{commande_id}",
                headers=headers
            )
            assert response.status_code == 200
            assert response.json()["order_id"] == "TEST_CMD_001"
            
    async def test_performance_basic(self):
        """Test de performance basique"""
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        
        async with httpx.AsyncClient() as client:
            # Test de 10 appels simultanés
            tasks = []
            for i in range(10):
                task = client.get(f"{API_BASE_URL}/commandes", headers=headers)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # Tous les appels doivent réussir
            for response in responses:
                assert response.status_code == 200 