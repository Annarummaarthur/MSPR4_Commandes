# Microservice Commandes MSPR4

Un microservice REST dédié **uniquement** à la gestion des commandes dans une architecture microservices pure, développé avec FastAPI et connecté à une base de données Supabase.

## 🏗️ Architecture Microservices Pure

Cette API fait partie d'une architecture microservices avec séparation stricte des responsabilités :

- **🛒 Microservice Commandes** (cette API) - Gestion UNIQUEMENT des commandes
- **📦 Microservice Produits** - Gestion UNIQUEMENT du catalogue produits (à développer)
- **👥 Microservice Clients** - Gestion UNIQUEMENT des informations clients (à développer)

## 🚀 Installation et Lancement

### 1. Prérequis

- Python 3.8+
- pip

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancement de l'API

```bash
# Méthode recommandée (installe automatiquement les dépendances)
python start.py

# Ou directement avec uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

L'API sera disponible sur : **http://localhost:8001**

## 📚 Documentation

- **Documentation interactive** : http://localhost:8001/docs
- **ReDoc** : http://localhost:8001/redoc

## 🔧 Tests

### Tests automatisés

```bash
# Tests Python avec pytest
python -m pytest test_api.py -v

# Test de connexion à la base
python test_db.py
```

### Tests avec cURL

```bash
# Tests complets de tous les endpoints
./test_api_curl.sh
```

## 📊 Endpoints disponibles

### Commandes (uniquement)

- `GET /` - Health check et informations sur le microservice
- `GET /stats` - Statistiques des commandes avec répartition par statut
- `GET /commandes` - Liste des commandes (avec filtres optionnels)
- `POST /commandes` - Créer une commande
- `GET /commandes/{id}` - Commande par ID
- `GET /commandes/order/{order_id}` - Commande par order_id
- `GET /commandes/customer/{customer_id}` - Commandes d'un client
- `PUT /commandes/{id}` - Modifier une commande
- `DELETE /commandes/{id}` - Supprimer une commande

### Gestion des statuts

- `PUT /commandes/{id}/status` - Mettre à jour le statut d'une commande
- `GET /commandes/status/{status}` - Commandes par statut

## 🔐 Authentification

Tous les endpoints (sauf `/`) nécessitent un token Bearer :

```bash
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8001/commandes
```

## 📁 Structure du projet

```
MSPR4_Commandes/
├── main.py                    # Microservice Commandes uniquement
├── db.py                      # Configuration base de données
├── start.py                   # Script de démarrage
├── requirements.txt           # Dépendances Python
├── .env                       # Variables d'environnement
├── test_api.py               # Tests automatisés
├── test_db.py                # Test de connexion DB
├── test_api_curl.sh          # Tests cURL complets
├── commandes_transfert.py    # Import des données (microservice pur)
└── README.md                 # Ce fichier
```

## 🗄️ Base de données

Le microservice utilise une base de données PostgreSQL hébergée sur **Supabase** avec **UNE SEULE** table :

### Table `commandes`

Structure optimisée pour un microservice pur :

- `id` (SERIAL PRIMARY KEY)
- `order_id` (VARCHAR(50) UNIQUE NOT NULL)
- `customer_id` (VARCHAR(50) NOT NULL) - **Référence** vers microservice Clients
- `created_at` (TIMESTAMP)
- `status` (VARCHAR(50)) - Statut de la commande
- `total_amount` (DECIMAL(10,2)) - Montant total calculé
- `updated_at` (TIMESTAMP)

## 🔄 Architecture Microservices Pure

### Principe de séparation stricte

- **Commandes** : Stocke uniquement les informations de commande + `customer_id` en référence
- **Détails produits** : **AUCUN** stockage dans ce service, tout via le microservice Produits
- **Informations clients** : **AUCUN** stockage dans ce service, tout via le microservice Clients

### Communication entre microservices

Pour obtenir les détails complets d'une commande, il faudra :

1. **Récupérer la commande** depuis ce microservice
2. **Appeler le microservice Clients** avec le `customer_id` pour les infos client
3. **Appeler le microservice Produits** pour les détails des produits commandés
4. **Assembler les données** côté frontend ou via un API Gateway

### Technologies de communication prévues

1. **API Gateway** - Point d'entrée unique
2. **Communication HTTP** synchrone entre microservices
3. **Message Broker** (RabbitMQ/Kafka) pour les événements asynchrones
4. **Cache Redis** pour optimiser les performances
5. **Event Sourcing** pour la cohérence des données

## 💾 Import de données

Pour importer les données mockées dans la structure microservice pure :

```bash
python commandes_transfert.py
```

Cette commande crée uniquement la table `commandes` et importe les données avec séparation totale des responsabilités.

## 🚀 Roadmap Architecture Complète

### Phase 1 - Microservices de base

1. ✅ **Microservice Commandes** (ce projet)
2. 🔄 **Microservice Produits** (à développer)
3. 🔄 **Microservice Clients** (à développer)

### Phase 2 - Infrastructure

4. 🔄 **API Gateway** (agrégation des services)
5. 🔄 **Service Discovery** (consul/etcd)
6. 🔄 **Load Balancer** (nginx/envoy)

### Phase 3 - Communication

7. 🔄 **Message Broker** (RabbitMQ/Apache Kafka)
8. 🔄 **Event Bus** pour la synchronisation
9. 🔄 **Cache distribué** (Redis)

### Phase 4 - Monitoring & Déploiement

10. 🔄 **Logging centralisé** (ELK Stack)
11. 🔄 **Monitoring** (Prometheus/Grafana)
12. 🔄 **CI/CD Pipeline** avec Docker
13. 🔄 **Orchestration** (Kubernetes/Docker Swarm)

## 📋 Statuts des commandes

- `pending` - En attente de traitement
- `processing` - En cours de traitement
- `completed` - Commande terminée
- `cancelled` - Commande annulée

## 🎯 Exemple d'utilisation

```bash
# Créer une commande (référence client uniquement)
curl -X POST "http://localhost:8001/commandes" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "CMD001",
    "customer_id": "CLIENT123",
    "total_amount": 150.50,
    "status": "pending"
  }'

# Modifier le statut
curl -X PUT "http://localhost:8001/commandes/1/status" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '"processing"'
```

## 🏷️ Version

**v3.0.0** - Microservice Pur (Commandes uniquement)
# Test workflow - Ven 18 jul 2025 23:54:31 CEST
