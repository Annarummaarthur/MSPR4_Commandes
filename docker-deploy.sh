#!/bin/bash

echo "🐳 Déploiement Docker du Microservice Commandes MSPR4"
echo "=================================================="

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé ou non accessible"
    exit 1
fi

# Vérifier que Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé ou non accessible"
    exit 1
fi

# Vérifier la présence du fichier .env
if [ ! -f .env ]; then
    echo "❌ Fichier .env manquant!"
    echo "Copie .env.example vers .env et configure tes variables"
    cp .env.example .env
    echo "✅ Fichier .env.example copié vers .env"
    echo "⚠️  Configure tes variables d'environnement avant de relancer"
    exit 1
fi

# Arrêter et supprimer les anciens conteneurs
echo "🛑 Arrêt des anciens conteneurs..."
docker-compose down

# Construire l'image
echo "🔨 Construction de l'image Docker..."
docker-compose build --no-cache

# Lancer le service
echo "🚀 Lancement du microservice..."
docker-compose up -d

# Afficher le statut
echo "📊 Statut des conteneurs:"
docker-compose ps

# Afficher les logs
echo "📝 Logs du service:"
docker-compose logs --tail=20 commandes-api

echo ""
echo "✅ Microservice Commandes déployé avec succès!"
echo "📍 API disponible sur: http://localhost:8001"
echo "📖 Documentation: http://localhost:8001/docs"
echo "🔍 Logs en temps réel: docker-compose logs -f commandes-api" 