#!/usr/bin/env python3
"""
Script de monitoring pour l'API Commandes MSPR4
"""
import requests
import json
import time
import os
from datetime import datetime


def check_api_health():
    """Vérifie la santé de l'API"""
    api_url = os.getenv("API_URL", "http://localhost:8001")
    token = os.getenv("API_TOKEN")

    try:
        # Health check
        response = requests.get(f"{api_url}/", timeout=10)
        if response.status_code == 200:
            print(f"✅ [{datetime.now()}] API Health OK")
            return True
        else:
            print(
                f"❌ [{datetime.now()}] API Health FAILED - Status: {response.status_code}"
            )
            return False

    except requests.RequestException as e:
        print(f"❌ [{datetime.now()}] API UNREACHABLE - Error: {e}")
        return False


if __name__ == "__main__":
    check_api_health()
