from sqlalchemy import text
from db import SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("✅ Connexion à la base de données MSPR4_Commandes (Supabase) OK")
        
        # Test des informations de connexion
        print(f"🔗 Database URL: {os.getenv('DATABASE_URL', 'Non définie')}")
        print(f"🔑 API Token configuré: {'Oui' if os.getenv('API_TOKEN') else 'Non'}")
        
        # Test des tables existantes
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"📊 Tables disponibles: {tables}")
        
        if 'commandes' in tables:
            result = db.execute(text("SELECT COUNT(*) FROM commandes"))
            count = result.fetchone()[0]
            print(f"📦 Nombre de commandes: {count}")
            
            if count > 0:
                # Afficher quelques exemples
                result = db.execute(text("SELECT order_id, customer_id, total_amount FROM commandes LIMIT 3"))
                examples = result.fetchall()
                print("📄 Exemples de commandes:")
                for example in examples:
                    print(f"   • Order ID: {example[0]}, Customer: {example[1]}, Montant: {example[2]}€")
        
        if 'produits_commandes' in tables:
            result = db.execute(text("SELECT COUNT(*) FROM produits_commandes"))
            count = result.fetchone()[0]
            print(f"🛍️ Nombre de produits de commandes: {count}")
            
            if count > 0:
                # Afficher quelques exemples
                result = db.execute(text("SELECT product_name, price, color FROM produits_commandes LIMIT 3"))
                examples = result.fetchall()
                print("🎁 Exemples de produits:")
                for example in examples:
                    print(f"   • Produit: {example[0]}, Prix: {example[1]}€, Couleur: {example[2]}")
        
        # Test de la structure des tables
        print("\n🏗️ Structure de la table commandes:")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'commandes' 
            ORDER BY ordinal_position
        """))
        for col in result.fetchall():
            print(f"   • {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
        print("\n🏗️ Structure de la table produits_commandes:")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'produits_commandes' 
            ORDER BY ordinal_position
        """))
        for col in result.fetchall():
            print(f"   • {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
    except Exception as e:
        print("❌ Erreur de connexion :", e)
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_connection() 