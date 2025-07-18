## 1. **Dockerfile** - Image optimisée pour FastAPI

```dockerfile:MSPR4_Commandes/Dockerfile
# Utiliser une image Python slim pour optimiser la taille
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Installer les dépendances système nécessaires pour psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements.txt en premier pour optimiser le cache Docker
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier tout le code source
COPY . .

# Créer un utilisateur non-root pour la sécurité
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Exposer le port sur lequel l'application va tourner
EXPOSE 8001

# Vérifier la santé du conteneur
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Commande par défaut pour lancer l'application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

## 2. **docker-compose.yml** - Orchestration du service

```yaml:MSPR4_Commandes/docker-compose.yml
version: '3.8'

services:
  commandes-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mspr4-commandes
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_TOKEN=${API_TOKEN}
    env_file:
      - .env
    volumes:
      # Volume pour les logs (optionnel)
      - ./logs:/app/logs
      # Volume pour le développement (optionnel - à commenter en production)
      - .:/app
    restart: unless-stopped
    networks:
      - mspr4-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

# Réseau pour la communication entre microservices
networks:
  mspr4-network:
    driver: bridge
    external: false

# Volume pour persister les logs
volumes:
  logs:
    driver: local
```

## 3. **.dockerignore** - Optimisation du build

```dockerignore:MSPR4_Commandes/.dockerignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
env/
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Logs
logs/
*.log

# Cache
.pytest_cache/
.coverage

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# Documentation
README.md
*.pdf
```

## 4. **Mise à jour du fichier .env** (exemple)

```env:MSPR4_Commandes/.env.example
# Base de données Supabase
DATABASE_URL=

# Token API pour sécuriser les endpoints
API_TOKEN=

# Environnement
ENVIRONMENT=development

# Port d'écoute (optionnel - défaut 8001)
PORT=8001
```

## 5. **Script de déploiement** - `docker-deploy.sh`

```bash:MSPR4_Commandes/docker-deploy.sh
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
```

## 6. **Commandes Docker utiles**

````bash:MSPR4_Commandes/docker-commands.md
# Commandes Docker utiles pour le microservice

## Build et déploiement
```bash
# Construction de l'image
docker build -t mspr4-commandes .

# Lancement avec docker-compose
docker-compose up -d

# Lancement avec rebuild
docker-compose up --build -d

# Arrêt du service
docker-compose down

## Monitoring et debugging
```bash
# Voir les logs en temps réel
docker-compose logs -f commandes-api

# Exécuter des commandes dans le conteneur
docker-compose exec commandes-api bash

# Inspecter le conteneur
docker-compose ps
docker-compose top

# Voir l'utilisation des ressources
docker stats

## Maintenance
```bash
# Nettoyer les images non utilisées
docker system prune

# Supprimer l'image spécifique
docker rmi mspr4-commandes

# Redémarrer le service
docker-compose restart commandes-api
````

## 🚀 **Instructions de déploiement**

1. **Rendre le script exécutable** :

```bash
chmod +x docker-deploy.sh
```

2. **Configurer l'environnement** :

```bash
cp .env.example .env
# Éditer .env avec tes vraies valeurs
```

3. **Déployer** :

```bash
./docker-deploy.sh
```

4. **Tester l'API** :

```bash
curl http://localhost:8001/
curl -H "Authorization: Bearer ton_token" http://localhost:8001/commandes
```

## 🔧 **Optimisations Docker**

- **Multi-stage build** (optionnel pour optimiser encore plus la taille)
- **Image scratch** ou **distroless** pour la production
- **Secrets Docker** pour les credentials sensibles
- **Health checks** configurés pour le monitoring
- **Restart policies** pour la haute disponibilité
