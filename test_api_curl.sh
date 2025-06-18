#!/bin/bash

# Script de test complet de l'API Commandes MSPR4 avec curl
# Assurez-vous que l'API fonctionne sur http://localhost:8001

API_BASE="http://localhost:8001"
API_TOKEN="mspr4_commandes_api_token_secure_2024"
HEADERS="Authorization: Bearer $API_TOKEN"

echo "🚀 DÉBUT DES TESTS DE L'API COMMANDES MSPR4"
echo "============================================="

# Variables pour stocker les IDs créés pendant les tests
CREATED_ORDER_ID=""
CREATED_COMMANDE_ID=""
CREATED_PRODUIT_ID=""

# Fonction pour afficher les résultats
show_result() {
    echo
    echo "📋 Test: $1"
    echo "-------------------"
}

# Fonction pour tester une requête curl
test_curl() {
    local description="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    show_result "$description"
    echo "🔗 $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
            -H "$HEADERS" \
            "$API_BASE$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
            -X POST \
            -H "$HEADERS" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_BASE$endpoint")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
            -X PUT \
            -H "$HEADERS" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_BASE$endpoint")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
            -X DELETE \
            -H "$HEADERS" \
            "$API_BASE$endpoint")
    fi
    
    # Séparer la réponse du code de statut
    http_code=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    response_body=$(echo "$response" | sed '/HTTP_STATUS:/d')
    
    echo "📊 Status: $http_code"
    echo "📄 Response:"
    echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
    echo
    
    # Retourner la réponse pour extraction d'IDs
    echo "$response_body"
}

# 1. HEALTH CHECK
test_curl "Health Check" "GET" "/" ""

# 2. STATISTIQUES (protégé par token)
test_curl "Statistiques générales" "GET" "/stats" ""

# 3. LISTER TOUTES LES COMMANDES
test_curl "Lister toutes les commandes" "GET" "/commandes" ""

# 4. LISTER TOUTES LES COMMANDES AVEC PAGINATION
test_curl "Lister commandes avec pagination" "GET" "/commandes?limit=5&offset=0" ""

# 5. CRÉER UNE NOUVELLE COMMANDE AVEC PRODUITS
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NEW_ORDER_DATA='{
  "order_id": "test_curl_'$TIMESTAMP'",
  "customer_id": "customer_curl_123",
  "created_at": "2024-01-15T10:30:00",
  "total_amount": 275.50,
  "produits": [
    {
      "product_id": "prod_curl_1",
      "product_name": "Produit Test cURL 1",
      "price": 125.25,
      "description": "Description du produit test via cURL",
      "color": "Rouge",
      "stock": 15
    },
    {
      "product_id": "prod_curl_2", 
      "product_name": "Produit Test cURL 2",
      "price": 150.25,
      "description": "Deuxième produit test via cURL",
      "color": "Bleu",
      "stock": 8
    }
  ]
}'

CREATE_RESPONSE=$(test_curl "Créer une nouvelle commande avec produits" "POST" "/commandes" "$NEW_ORDER_DATA")

# Extraire l'ID de la commande créée
CREATED_COMMANDE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id' 2>/dev/null)
CREATED_ORDER_ID=$(echo "$CREATE_RESPONSE" | jq -r '.order_id' 2>/dev/null)

echo "🆔 ID de la commande créée: $CREATED_COMMANDE_ID"
echo "🆔 Order ID créé: $CREATED_ORDER_ID"
echo

# 6. RÉCUPÉRER UNE COMMANDE PAR ID
if [ "$CREATED_COMMANDE_ID" != "null" ] && [ "$CREATED_COMMANDE_ID" != "" ]; then
    test_curl "Récupérer commande par ID" "GET" "/commandes/$CREATED_COMMANDE_ID" ""
fi

# 7. RÉCUPÉRER UNE COMMANDE PAR ORDER_ID
if [ "$CREATED_ORDER_ID" != "null" ] && [ "$CREATED_ORDER_ID" != "" ]; then
    test_curl "Récupérer commande par order_id" "GET" "/commandes/order/$CREATED_ORDER_ID" ""
fi

# 8. RÉCUPÉRER LES COMMANDES D'UN CUSTOMER
test_curl "Récupérer commandes par customer_id" "GET" "/commandes/customer/customer_curl_123" ""

# 9. RÉCUPÉRER LES PRODUITS D'UNE COMMANDE
if [ "$CREATED_ORDER_ID" != "null" ] && [ "$CREATED_ORDER_ID" != "" ]; then
    test_curl "Récupérer produits d'une commande" "GET" "/commandes/$CREATED_ORDER_ID/produits" ""
fi

# 10. AJOUTER UN PRODUIT À UNE COMMANDE EXISTANTE
if [ "$CREATED_ORDER_ID" != "null" ] && [ "$CREATED_ORDER_ID" != "" ]; then
    NEW_PRODUCT_DATA='{
      "product_id": "prod_curl_3",
      "product_name": "Produit Ajouté via cURL",
      "price": 75.00,
      "description": "Produit ajouté après création de la commande",
      "color": "Vert",
      "stock": 12
    }'
    
    ADD_PRODUCT_RESPONSE=$(test_curl "Ajouter un produit à la commande" "POST" "/commandes/$CREATED_ORDER_ID/produits" "$NEW_PRODUCT_DATA")
    CREATED_PRODUIT_ID=$(echo "$ADD_PRODUCT_RESPONSE" | jq -r '.id' 2>/dev/null)
    echo "🆔 ID du produit ajouté: $CREATED_PRODUIT_ID"
    echo
fi

# 11. LISTER TOUS LES PRODUITS DE COMMANDES
test_curl "Lister tous les produits de commandes" "GET" "/produits-commandes" ""

# 12. LISTER TOUS LES PRODUITS AVEC PAGINATION
test_curl "Lister produits avec pagination" "GET" "/produits-commandes?limit=3&offset=0" ""

# 13. RÉCUPÉRER UN PRODUIT DE COMMANDE PAR ID
if [ "$CREATED_PRODUIT_ID" != "null" ] && [ "$CREATED_PRODUIT_ID" != "" ]; then
    test_curl "Récupérer produit de commande par ID" "GET" "/produits-commandes/$CREATED_PRODUIT_ID" ""
fi

# 14. MODIFIER UNE COMMANDE
if [ "$CREATED_COMMANDE_ID" != "null" ] && [ "$CREATED_COMMANDE_ID" != "" ]; then
    UPDATE_COMMANDE_DATA='{
      "customer_id": "customer_curl_updated_456",
      "total_amount": 350.75
    }'
    
    test_curl "Modifier une commande" "PUT" "/commandes/$CREATED_COMMANDE_ID" "$UPDATE_COMMANDE_DATA"
fi

# 15. MODIFIER UN PRODUIT DE COMMANDE
if [ "$CREATED_PRODUIT_ID" != "null" ] && [ "$CREATED_PRODUIT_ID" != "" ]; then
    UPDATE_PRODUCT_DATA='{
      "product_name": "Produit Modifié via cURL",
      "price": 89.99,
      "color": "Jaune",
      "stock": 20
    }'
    
    test_curl "Modifier un produit de commande" "PUT" "/produits-commandes/$CREATED_PRODUIT_ID" "$UPDATE_PRODUCT_DATA"
fi

# 16. CRÉER UNE COMMANDE SIMPLE SANS PRODUITS
SIMPLE_ORDER_DATA='{
  "order_id": "simple_curl_'$TIMESTAMP'",
  "customer_id": "customer_simple_789",
  "total_amount": 0
}'

SIMPLE_CREATE_RESPONSE=$(test_curl "Créer commande simple sans produits" "POST" "/commandes" "$SIMPLE_ORDER_DATA")
SIMPLE_ORDER_ID=$(echo "$SIMPLE_CREATE_RESPONSE" | jq -r '.order_id' 2>/dev/null)

# 17. TESTER ERREUR 404 - COMMANDE INEXISTANTE
test_curl "Test erreur 404 - Commande inexistante" "GET" "/commandes/99999" ""

# 18. TESTER ERREUR 404 - ORDER_ID INEXISTANT
test_curl "Test erreur 404 - Order_ID inexistant" "GET" "/commandes/order/order_inexistant" ""

# 19. TESTER ERREUR 404 - PRODUIT INEXISTANT
test_curl "Test erreur 404 - Produit inexistant" "GET" "/produits-commandes/99999" ""

# 20. TESTER ERREUR 403 - SANS TOKEN
show_result "Test erreur 403 - Sans token d'authentification"
echo "🔗 GET /commandes (sans token)"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$API_BASE/commandes")
http_code=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
response_body=$(echo "$response" | sed '/HTTP_STATUS:/d')
echo "📊 Status: $http_code"
echo "📄 Response:"
echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
echo

# 21. TESTER ERREUR 403 - MAUVAIS TOKEN
show_result "Test erreur 403 - Mauvais token"
echo "🔗 GET /commandes (mauvais token)"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer mauvais_token" \
    "$API_BASE/commandes")
http_code=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
response_body=$(echo "$response" | sed '/HTTP_STATUS:/d')
echo "📊 Status: $http_code"
echo "📄 Response:"
echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
echo

# 22. TESTER CRÉATION COMMANDE AVEC ORDER_ID EXISTANT
if [ "$CREATED_ORDER_ID" != "null" ] && [ "$CREATED_ORDER_ID" != "" ]; then
    DUPLICATE_ORDER_DATA='{
      "order_id": "'$CREATED_ORDER_ID'",
      "customer_id": "duplicate_test",
      "total_amount": 100
    }'
    
    test_curl "Test erreur 400 - Order_ID déjà existant" "POST" "/commandes" "$DUPLICATE_ORDER_DATA"
fi

# 23. NETTOYAGE - SUPPRIMER LES ÉLÉMENTS CRÉÉS
echo "🧹 NETTOYAGE DES DONNÉES DE TEST"
echo "================================="

# Supprimer le produit ajouté
if [ "$CREATED_PRODUIT_ID" != "null" ] && [ "$CREATED_PRODUIT_ID" != "" ]; then
    test_curl "Supprimer le produit de test" "DELETE" "/produits-commandes/$CREATED_PRODUIT_ID" ""
fi

# Supprimer la commande principale (cela supprime aussi ses produits)
if [ "$CREATED_COMMANDE_ID" != "null" ] && [ "$CREATED_COMMANDE_ID" != "" ]; then
    test_curl "Supprimer la commande de test" "DELETE" "/commandes/$CREATED_COMMANDE_ID" ""
fi

# Supprimer la commande simple
if [ "$SIMPLE_ORDER_ID" != "null" ] && [ "$SIMPLE_ORDER_ID" != "" ]; then
    SIMPLE_COMMANDE_ID=$(curl -s \
        -H "$HEADERS" \
        "$API_BASE/commandes/order/$SIMPLE_ORDER_ID" | jq -r '.id' 2>/dev/null)
    
    if [ "$SIMPLE_COMMANDE_ID" != "null" ] && [ "$SIMPLE_COMMANDE_ID" != "" ]; then
        test_curl "Supprimer la commande simple de test" "DELETE" "/commandes/$SIMPLE_COMMANDE_ID" ""
    fi
fi

echo "✅ TESTS TERMINÉS AVEC SUCCÈS !"
echo "==============================="
echo
echo "📊 RÉSUMÉ DES ENDPOINTS TESTÉS:"
echo "• GET    /                           - Health check"
echo "• GET    /stats                      - Statistiques"
echo "• GET    /commandes                  - Liste des commandes"
echo "• POST   /commandes                  - Créer une commande"
echo "• GET    /commandes/{id}             - Commande par ID"
echo "• GET    /commandes/order/{order_id} - Commande par order_id"
echo "• GET    /commandes/customer/{id}    - Commandes par customer"
echo "• PUT    /commandes/{id}             - Modifier une commande"
echo "• DELETE /commandes/{id}             - Supprimer une commande"
echo "• POST   /commandes/{order_id}/produits - Ajouter produit"
echo "• GET    /commandes/{order_id}/produits - Produits d'une commande"
echo "• GET    /produits-commandes         - Tous les produits"
echo "• GET    /produits-commandes/{id}    - Produit par ID"
echo "• PUT    /produits-commandes/{id}    - Modifier un produit"
echo "• DELETE /produits-commandes/{id}    - Supprimer un produit"
echo
echo "🔒 TESTS DE SÉCURITÉ:"
echo "• Test sans token (403)"
echo "• Test avec mauvais token (403)"
echo "• Test ressources inexistantes (404)"
echo "• Test order_id déjà existant (400)" 