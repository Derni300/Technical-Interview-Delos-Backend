# Chatbot Sportif Backend

## 📋 Description
Un backend FastAPI pour un chatbot sportif permettant aux utilisateurs de discuter de différents sports (rugby, football, tennis, volley, cyclisme). Le projet utilise PostgreSQL comme base de données et propose des fonctionnalités de gestion d'utilisateurs, de conversations et de messages.

## 🚀 Prérequis
- Python 3.9+
- Docker
- Docker Compose
- pip

## 🔧 Installation

### Clonage du Projet
```bash
git clone https://github.com/Derni300/Technical-Interview-Delos-Backend
cd Technical-Interview-Delos-Backend
```

### Configuration de l'Environnement
```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`

# Installer les dépendances
pip install -r requirements.txt
```

## 🐳 Docker et Base de Données

### Démarrage des Services
```bash
# Démarrer la base de données PostgreSQL
docker-compose up -d postgres
```

### Configuration de la Base de Données
- Utilisateur : `user`
- Mot de passe : `password`
- Base de données : `mydatabase`
- Port : `5432`

## 🚦 Démarrage de l'Application

### Mode Développement
```bash
# Démarrer le serveur de développement
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Mode Production
```bash
# Construction d'un conteneur (optionnel)
docker build -t chatbot-backend .
docker run -p 8000:8000 chatbot-backend
```

## 📡 Routes API Principales

### Utilisateurs
- `POST /users/` : Créer un utilisateur
- `GET /users/{user_id}` : Récupérer un utilisateur

### Conversations
- `POST /chat/` : Envoyer un message
- `POST /chat/stream` : Envoyer un message avec réponse streaming
- `GET /history/{user_id}` : Historique des conversations
- `GET /conversation/{conversation_id}` : Détails d'une conversation

### Administration
- `GET /admin/stats` : Statistiques de l'application
- `GET /ping` : Vérification de l'état du serveur

## 🧪 Tests
```bash
# Commande pour exécuter les tests (à définir)
pytest
```

## 🔒 Sécurité
- Authentification par UUID
- Validation des données avec Pydantic
- CORS configuré
- Base de données sécurisée

## 📦 Dépendances Principales
- FastAPI
- SQLAlchemy
- Uvicorn
- Psycopg2
- Python-dotenv

## 📝 Structure du Projet
```
.
├── main.py            # Point d'entrée principal
├── config.py          # Configuration de l'environnement
├── requirements.txt   # Dépendances Python
├── docker-compose.yml # Configuration Docker
└── README.md          # Documentation du projet
```

## 🌟 Fonctionnalités
- Chat sur 5 sports : Rugby, Football, Tennis, Volley, Cyclisme
- Génération de réponses aléatoires
- Historique des conversations
- Support du streaming de réponses
- Statistiques administratives

## 🤝 Contribution
1. Forker le projet
2. Créer une branche de fonctionnalité
3. Commiter vos modifications
4. Pousser la branche
5. Ouvrir une Pull Request

## 📄 Licence
[À définir - par exemple MIT]

## 📞 Contact
- Votre Nom
- Votre Email
- Lien du Projet GitHub
