#!/bin/bash

# Script de test complet pour l'API Commandes MSPR4 - Architecture Microservices Pure
# Ce script teste uniquement les fonctionnalités de gestion des commandes

BASE_URL="http://localhost:8001"
API_TOKEN="mspr4_commandes_api_token_secure_2025"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour tester les endpoints
test_curl() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    echo -e "${BLUE}🧪 Test: $test_name${NC}"
    echo "   📡 $method $endpoint"
    
    if [ "$method" = "GET" ] || [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $API_TOKEN" -X "$method" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $API_TOKEN" -H "Content-Type: application/json" -X "$method" -d "$data" "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [[ "$http_code" =~ ^(200|201)$ ]]; then
        echo -e "   ${GREEN}✅ Success ($http_code)${NC}"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo -e "   ${RED}❌ Failed ($http_code)${NC}"
        echo "$body"
    fi
    
    echo "$body"
    echo
}

echo -e "${YELLOW}🚀 DÉMARRAGE DES TESTS DE L'API COMMANDES MSPR4${NC}"
echo -e "${YELLOW}🏗️ Architecture Microservices Pure - Commandes Uniquement${NC}"
echo "=================================================="
echo

# 1. HEALTH CHECK
test_curl "Health check" "GET" "/" ""

# 2. STATISTIQUES GÉNÉRALES
test_curl "Statistiques générales" "GET" "/stats" ""

# 3. LISTER LES COMMANDES
test_curl "Lister toutes les commandes" "GET" "/commandes" ""

# 4. LISTER COMMANDES AVEC PAGINATION
test_curl "Lister commandes avec pagination" "GET" "/commandes?limit=5&offset=0" ""

# 5. LISTER COMMANDES AVEC TRI
test_curl "Lister commandes triées par montant DESC" "GET" "/commandes?order_by=total_amount&order_direction=desc&limit=3" ""

# 6. CRÉER UNE NOUVELLE COMMANDE
ORDER_ID="curl_test_$(date +%Y%m%d_%H%M%S)"
COMMANDE_DATA='{
  "order_id": "'$ORDER_ID'",
  "customer_id": "customer_curl_123",
  "total_amount": 299.99,
  "status": "pending"
}'

CREATE_RESPONSE=$(test_curl "Créer une nouvelle commande" "POST" "/commandes" "$COMMANDE_DATA")
CREATED_COMMANDE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id' 2>/dev/null)
echo "🆔 ID de la commande créée: $CREATED_COMMANDE_ID"
echo

# 7. RÉCUPÉRER UNE COMMANDE PAR ID
if [ "$CREATED_COMMANDE_ID" != "null" ] && [ "$CREATED_COMMANDE_ID" != "" ]; then
    test_curl "Récupérer commande par ID" "GET" "/commandes/$CREATED_COMMANDE_ID" ""
fi

# 8. RÉCUPÉRER UNE COMMANDE PAR ORDER_ID
if [ "$ORDER_ID" != "" ]; then
    test_curl "Récupérer commande par order_id" "GET" "/commandes/order/$ORDER_ID" ""
fi

# 9. RÉCUPÉRER LES COMMANDES D'UN CUSTOMER
test_curl "Récupérer commandes par customer_id" "GET" "/commandes/customer/customer_curl_123" ""

# 10. METTRE À JOUR LE STATUT D'UNE COMMANDE
if [ "$CREATED_COMMANDE_ID" != "null" ] && [ "$CREATED_COMMANDE_ID" != "" ]; then
    STATUS_UPDATE='{"status": "processing"}'
    test_curl "Mettre à jour le statut de la commande" "PUT" "/commandes/$CREATED_COMMANDE_ID/status" "$STATUS_UPDATE"
fi

# 11. MODIFIER UNE COMMANDE
if [ "$CREATED_COMMANDE_ID" != "null" ] && [ "$CREATED_COMMANDE_ID" != "" ]; then
    UPDATE_DATA='{
      "customer_id": "customer_curl_updated_456",
      "total_amount": 399.99,
      "status": "completed"
    }'
    test_curl "Modifier une commande complète" "PUT" "/commandes/$CREATED_COMMANDE_ID" "$UPDATE_DATA"
fi

# 12. RECHERCHE AVANCÉE PAR MONTANT
test_curl "Recherche par montant (1000€ - 1500€)" "GET" "/commandes/search?min_amount=1000&max_amount=1500&limit=3" ""

# 13. RECHERCHE TEXTUELLE
test_curl "Recherche textuelle (CLIENT)" "GET" "/commandes/search?q=CLIENT&limit=5" ""

# 14. RÉCUPÉRER COMMANDES PAR STATUT
test_curl "Récupérer commandes par statut (completed)" "GET" "/commandes/status/completed?limit=5" ""

# 15. RÉCUPÉRER COMMANDES PAR STATUT
test_curl "Récupérer commandes par statut (pending)" "GET" "/commandes/status/pending?limit=5" ""

# 16. TEST D'ERREUR - COMMANDE INEXISTANTE
test_curl "Test erreur - commande inexistante" "GET" "/commandes/999999" ""

# 17. TEST D'ERREUR - STATUT INVALIDE
test_curl "Test erreur - statut invalide" "GET" "/commandes/status/invalid_status" ""

# 18. TEST D'ERREUR - CRÉATION AVEC ORDER_ID EXISTANT
if [ "$ORDER_ID" != "" ]; then
    DUPLICATE_DATA='{
      "order_id": "'$ORDER_ID'",
      "customer_id": "customer_duplicate",
      "total_amount": 100.00,
      "status": "pending"
    }'
    test_curl "Test erreur - order_id existant" "POST" "/commandes" "$DUPLICATE_DATA"
fi

# 19. SUPPRIMER UNE COMMANDE (à la fin pour ne pas affecter les autres tests)
if [ "$CREATED_COMMANDE_ID" != "null" ] && [ "$CREATED_COMMANDE_ID" != "" ]; then
    test_curl "Supprimer une commande" "DELETE" "/commandes/$CREATED_COMMANDE_ID" ""
fi

echo "=================================================="
echo -e "${GREEN}✅ TESTS TERMINÉS${NC}"
echo -e "${YELLOW}📊 Tous les endpoints du microservice Commandes ont été testés${NC}"
echo -e "${BLUE}🏗️ Architecture Microservices Pure respectée${NC}"
echo 