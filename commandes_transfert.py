import requests
import psycopg
import json
from datetime import datetime

# 1. Récupération des données mockées
MOCK_API_URL = "https://615f5fb4f7254d0017068109.mockapi.io/api/v1/orders"
response = requests.get(MOCK_API_URL)
orders = response.json()

# 2. Connexion à ta base Supabase (Commandes)
conn = psycopg.connect(
    host="db.kmchiernfkyehxovldwa.supabase.co",
    dbname="postgres",
    user="postgres",
    password="MSPR4_Commandes",
    port="5432"
)
cursor = conn.cursor()

# 3. Création des tables
cursor.execute("""
DROP TABLE IF EXISTS produits_commandes;
DROP TABLE IF EXISTS commandes;

CREATE TABLE commandes (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE,
    customer_id VARCHAR(50),
    created_at TIMESTAMP,
    total_amount DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE produits_commandes (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    product_id VARCHAR(50),
    product_name VARCHAR(255),
    price DECIMAL(10,2),
    description TEXT,
    color VARCHAR(100),
    stock INTEGER,
    product_created_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES commandes(order_id) ON DELETE CASCADE
);
""")

print("✅ Tables créées avec succès!")

# 4. Insertion des commandes et produits
for order in orders:
    try:
        # Calculer le montant total de la commande
        total_amount = 0
        if order.get("products"):
            for product in order["products"]:
                if product.get("details", {}).get("price"):
                    total_amount += float(product["details"]["price"])

        # Insertion de la commande
        cursor.execute("""
            INSERT INTO commandes (
                order_id, customer_id, created_at, total_amount
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (order_id) DO NOTHING;
        """, (
            order.get("id"),
            order.get("customerId") or order.get("customer_id"),
            order.get("createdAt"),
            total_amount
        ))

        # Insertion des produits de la commande
        if order.get("products"):
            for product in order["products"]:
                cursor.execute("""
                    INSERT INTO produits_commandes (
                        order_id, product_id, product_name, price,
                        description, color, stock, product_created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    order.get("id"),
                    product.get("id"),
                    product.get("name"),
                    float(product.get("details", {}).get("price", 0)) if product.get("details", {}).get("price") else None,
                    product.get("details", {}).get("description"),
                    product.get("details", {}).get("color"),
                    product.get("stock"),
                    product.get("createdAt")
                ))

        print(f"✅ Commande {order.get('id')} importée avec {len(order.get('products', []))} produits")

    except Exception as e:
        print(f"❌ Erreur pour commande {order.get('id')}: {e}")

# 5. Commit et fermeture
conn.commit()

# 6. Affichage des statistiques
cursor.execute("SELECT COUNT(*) FROM commandes;")
nb_commandes = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM produits_commandes;")
nb_produits = cursor.fetchone()[0]

cursor.execute("SELECT SUM(total_amount) FROM commandes;")
total_global = cursor.fetchone()[0]

cursor.close()
conn.close()

print("\n📊 STATISTIQUES D'IMPORTATION:")
print(f"   • Commandes importées: {nb_commandes}")
print(f"   • Produits importés: {nb_produits}")
print(f"   • Montant total des commandes: {total_global:.2f}€" if total_global else "   • Montant total: 0€")
print("\n✅ Importation terminée avec succès !") 