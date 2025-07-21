import requests
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

MOCK_API_URL = "https://615f5fb4f7254d0017068109.mockapi.io/api/v1/orders"
response = requests.get(MOCK_API_URL)
orders = response.json()

# 2. Connexion à ta base Supabase (Commandes) - avec les credentials du .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL non trouvée dans le fichier .env")

conn = psycopg.connect(DATABASE_URL)
cursor = conn.cursor()

print(f"🔗 Connexion à la base de données : {DATABASE_URL[:50]}...")

# 3. Création de la table commandes uniquement (microservice pur)
cursor.execute(
    """
DROP TABLE IF EXISTS commandes_produits;
DROP TABLE IF EXISTS produits_commandes;
DROP TABLE IF EXISTS commandes;

-- Table des commandes (microservice commandes uniquement)
CREATE TABLE commandes (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10,2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les performances
CREATE INDEX idx_commandes_order_id ON commandes(order_id);
CREATE INDEX idx_commandes_customer_id ON commandes(customer_id);
CREATE INDEX idx_commandes_status ON commandes(status);
CREATE INDEX idx_commandes_created_at ON commandes(created_at);
"""
)

print("✅ Table commandes créée selon l'architecture microservices pure!")
print("🚀 Index de performance créés pour optimiser les requêtes!")

# 4. Insertion des commandes uniquement (sans aucune référence produit)
commandes_importees = 0
erreurs = 0

for order in orders:
    try:
        # Calculer le montant total de la commande à partir des produits
        total_amount = 0
        if order.get("products"):
            for product in order["products"]:
                if product.get("details", {}).get("price"):
                    total_amount += float(product["details"]["price"])

        # Insertion de la commande pure (pas de gestion des produits)
        cursor.execute(
            """
            INSERT INTO commandes (
                order_id, customer_id, created_at, total_amount, status
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (order_id) DO NOTHING;
        """,
            (
                order.get("id"),
                order.get("customerId") or order.get("customer_id") or "unknown",
                order.get("createdAt"),
                total_amount,
                "completed",  # Statut par défaut pour les données mockées
            ),
        )

        if cursor.rowcount > 0:
            print(f"✅ Commande {order.get('id')} importée (montant: {total_amount}€)")
            commandes_importees += 1
        else:
            print(f"⚠️  Commande {order.get('id')} déjà existante")

    except Exception as e:
        print(f"❌ Erreur pour commande {order.get('id')}: {e}")
        erreurs += 1

# 5. Commit et fermeture
conn.commit()

# 6. Affichage des statistiques
cursor.execute("SELECT COUNT(*) FROM commandes;")
nb_commandes = cursor.fetchone()[0]

cursor.execute("SELECT SUM(total_amount) FROM commandes;")
total_global = cursor.fetchone()[0]

cursor.execute(
    "SELECT status, COUNT(*) FROM commandes GROUP BY status ORDER BY status;"
)
stats_status = cursor.fetchall()

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("📊 STATISTIQUES D'IMPORTATION (Microservice Commandes Pur)")
print("=" * 60)
print(f"   • Commandes importées cette session: {commandes_importees}")
print(f"   • Erreurs rencontrées: {erreurs}")
print(f"   • Total commandes en base: {nb_commandes}")
print(
    f"   • Montant total des commandes: {total_global:.2f}€"
    if total_global
    else "   • Montant total: 0€"
)

print(f"\n📋 Répartition par statut:")
for status, count in stats_status:
    print(f"   • {status}: {count} commande(s)")

print("\n✅ Importation terminée avec succès !")
print("\n🏗️  ARCHITECTURE MICROSERVICES PURE:")
print("   • 🛒 Microservice Commandes: gère UNIQUEMENT les commandes")
print("   • 📦 Microservice Produits: gère UNIQUEMENT le catalogue (à développer)")
print("   • 👥 Microservice Clients: gère UNIQUEMENT les clients (à développer)")
print("\n💡 Les liens entre services se feront via API calls ou message broker")
print(f"\n🔑 Token API configuré: {os.getenv('API_TOKEN', 'Non configuré')}")
