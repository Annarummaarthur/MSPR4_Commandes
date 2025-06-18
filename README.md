# API Commandes MSPR4

Une API REST pour la gestion des commandes et produits de commandes, développée avec FastAPI et connectée à une base de données Supabase.

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

### Commandes

- `GET /` - Health check
- `GET /stats` - Statistiques générales
- `GET /commandes` - Liste des commandes
- `POST /commandes` - Créer une commande
- `GET /commandes/{id}` - Commande par ID
- `GET /commandes/order/{order_id}` - Commande par order_id
- `GET /commandes/customer/{customer_id}` - Commandes d'un client
- `PUT /commandes/{id}` - Modifier une commande
- `DELETE /commandes/{id}` - Supprimer une commande

### Produits de commandes

- `POST /commandes/{order_id}/produits` - Ajouter un produit à une commande
- `GET /commandes/{order_id}/produits` - Produits d'une commande
- `GET /produits-commandes` - Tous les produits de commandes
- `GET /produits-commandes/{id}` - Produit par ID
- `PUT /produits-commandes/{id}` - Modifier un produit
- `DELETE /produits-commandes/{id}` - Supprimer un produit

## 🔐 Authentification

Tous les endpoints (sauf `/`) nécessitent un token Bearer :

```bash
curl -H "Authorization: Bearer mspr4_commandes_api_token_secure_2024" \
     http://localhost:8001/commandes
```

## 📁 Structure du projet

```
MSPR4_Commandes/
├── main.py                    # API FastAPI principale
├── db.py                      # Configuration base de données
├── start.py                   # Script de démarrage
├── requirements.txt           # Dépendances Python
├── .env                       # Variables d'environnement
├── test_api.py               # Tests automatisés
├── test_db.py                # Test de connexion DB
├── test_api_curl.sh          # Tests cURL complets
├── commandes_transfert.py    # Import des données mockées
└── README.md                 # Ce fichier
```

## 🗄️ Base de données

L'API utilise une base de données PostgreSQL hébergée sur **Supabase** avec deux tables :

### Table `commandes`

- `id` (SERIAL PRIMARY KEY)
- `order_id` (VARCHAR(50) UNIQUE)
- `customer_id` (VARCHAR(50))
- `created_at` (TIMESTAMP)
- `total_amount` (DECIMAL(10,2))

### Table `produits_commandes`

- `id` (SERIAL PRIMARY KEY)
- `order_id` (VARCHAR(50)) - Clé étrangère vers `commandes`
- `product_id` (VARCHAR(50))
- `product_name` (VARCHAR(255))
- `price` (DECIMAL(10,2))
- `description` (TEXT)
- `color` (VARCHAR(100))
- `stock` (INTEGER)
- `product_created_at` (TIMESTAMP)

## 💾 Import de données

Pour importer les données mockées dans la base :

```bash
python commandes_transfert.py
```
