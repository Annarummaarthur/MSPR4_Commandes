import os
import subprocess
import sys
import uvicorn


def install_requirements():
    print("📦 Installation des dépendances depuis requirements.txt...")
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt manquant !")
        sys.exit(1)
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )


def check_env_file():
    print("🔍 Vérification de la présence du fichier .env...")
    if not os.path.exists(".env"):
        print(
            "⚠️  Fichier .env manquant. Crée un fichier .env avec les variables DATABASE_URL et API_TOKEN."
        )
        print("Exemple de contenu pour .env :")
        print(
            "DATABASE_URL=postgresql://postgres:MSPR4_Commandes@db.kmchiernfkyehxovldwa.supabase.co:5432/postgres"
        )
        print("API_TOKEN=your_api_token_here")
        sys.exit(1)


def start_server():
    print("🚀 Démarrage de l'API Commandes avec Uvicorn sur le port 8001...")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)


if __name__ == "__main__":
    install_requirements()
    check_env_file()
    start_server()
