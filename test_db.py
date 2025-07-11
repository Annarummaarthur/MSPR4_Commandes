from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        # Récupération de l'URL depuis .env
        DATABASE_URL = os.getenv("DATABASE_URL")
        API_TOKEN = os.getenv("API_TOKEN")
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL non trouvée dans le fichier .env")
            return
            
        print(f"✅ Connexion à la base de données MSPR4_Commandes (Supabase) OK")
        print(f"🔗 Database URL: {DATABASE_URL[:50]}...")
        print(f"🔑 API Token configuré: {'Oui' if API_TOKEN else 'Non'}")
        
        # Créer la connexion
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as db:
            # Vérifier les tables disponibles
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📊 Tables disponibles: {tables}")
            
            # Tester la table commandes
            if 'commandes' in tables:
                result = db.execute(text("SELECT COUNT(*) FROM commandes"))
                count = result.fetchone()[0]
                print(f"📦 Nombre de commandes: {count}")
                
                if count > 0:
                    # Afficher quelques exemples
                    result = db.execute(text("""
                        SELECT order_id, customer_id, total_amount, status 
                        FROM commandes 
                        ORDER BY created_at DESC 
                        LIMIT 3
                    """))
                    examples = result.fetchall()
                    print("📋 Exemples de commandes:")
                    for example in examples:
                        print(f"   • Order ID: {example[0]}, Client: {example[1]}, Montant: {example[2]}€, Statut: {example[3]}")
                
                # Statistiques par statut
                result = db.execute(text("""
                    SELECT status, COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                    FROM commandes 
                    GROUP BY status 
                    ORDER BY count DESC
                """))
                stats = result.fetchall()
                print("\n📊 Répartition par statut:")
                for stat in stats:
                    print(f"   • {stat[0]}: {stat[1]} commande(s) - {float(stat[2]):.2f}€")
            else:
                print("⚠️  Table 'commandes' non trouvée")
            
            # Test de la structure de la table commandes
            print("\n🏗️ Structure de la table commandes:")
            result = db.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'commandes' 
                ORDER BY ordinal_position
            """))
            for col in result.fetchall():
                nullable = 'NULL' if col[2] == 'YES' else 'NOT NULL'
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"   • {col[0]}: {col[1]} ({nullable}){default}")
            
            # Vérifier les index
            print("\n🚀 Index disponibles:")
            result = db.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'commandes'
                ORDER BY indexname
            """))
            indexes = result.fetchall()
            for idx in indexes:
                print(f"   • {idx[0]}")
            
            # Test de performance simple
            print("\n⚡ Test de performance:")
            import time
            start_time = time.time()
            result = db.execute(text("SELECT COUNT(*) FROM commandes WHERE status = 'completed'"))
            end_time = time.time()
            completed_count = result.fetchone()[0]
            print(f"   • Requête sur statut 'completed': {completed_count} résultats en {(end_time - start_time)*1000:.2f}ms")
            
    except SQLAlchemyError as e:
        print("❌ Erreur de connexion :", e)
    except Exception as e:
        print("❌ Erreur générale :", e)

if __name__ == "__main__":
    print("🔍 Test de connexion à la base de données - Microservice Commandes MSPR4")
    print("=" * 75)
    test_connection()
    print("=" * 75)
    print("✅ Test terminé") 