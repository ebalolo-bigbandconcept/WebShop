# WebShop

Application WebShop contenant :

[![React](https://img.shields.io/badge/Frontend-React-blue?logo=react)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)](https://redis.io/)
[![DocuSign](https://img.shields.io/badge/DocuSign-eSign-orange?logo=docusign)](https://www.docusign.com/)

Application WebShop avec frontend React/Bootstrap, backend Flask, Redis pour cache, et intégration DocuSign.

---

## Developpement local

### 1. Mise à jour du VPS

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Installation de docker

#### Ajouter le repo Docker

```bash
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

#### Installer Docker

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo systemctl status docker  # Vérifier le statut
sudo systemctl start docker   # Démarrer si nécessaire
sudo docker run hello-world   # Test rapide
```

### 3. Initialisation de site

#### Générer une clé secrète

```bash
openssl rand -base64 32
```

Exemple de clé générée :

```bash
0rnd5wsmCJYz9wucw4OCl3uOP3FxbRC+nV6pptA07KE=
```

#### Créez le fichier `.env` à la racine du site

```bash
SECRET_KEY=your_key
ADMIN_MAIL=your_admin_mail
ADMIN_PASSWORD=your_admin_password

REACT_APP_BACKEND_URL=http://localhost:5000

DOCUSIGN_ACCOUNT_ID=your_docusign_account_id
DOCUSIGN_USER_ID=your_docusign_user_id
DOCUSIGN_INTEGRATION_KEY=your_docusign_integration_id
DOCUSIGN_SERVER_IP=123.456.789.10
```

> Remplacer tous les `your_...` par vos identifiants.

#### Build et lancement avec Docker

```bash
sudo docker compose build
sudo docker compose up
```

### 4. Accès à l'application

- Frontend : [http://localhost:3000](http://localhost:3000)
- Backend : [http://localhost:5000](http://localhost:5000)

### 5. Gestion des Migrations de Base de Données

Cette application utilise Flask-Migrate (Alembic) pour gérer les modifications du schéma de base de données.

#### Initialisation des migrations (première fois uniquement)

```bash
# Entrer dans le conteneur backend
sudo docker compose -f docker-compose.prod.yml exec backend bash

# Initialiser les migrations (crée le dossier migrations/)
flask db init

# Créer la première migration
flask db migrate -m "Initial migration"

# Appliquer la migration
flask db upgrade

exit
```

#### Créer une nouvelle migration après modification des modèles

```bash
# Entrer dans le conteneur backend
sudo docker compose -f docker-compose.prod.yml exec backend bash

# Créer une migration automatique
flask db migrate -m "Description de vos changements"

# Vérifier la migration générée dans migrations/versions/
# Puis appliquer la migration
flask db upgrade

exit
```

#### Commandes utiles

```bash
# Voir l'historique des migrations
flask db history

# Voir la version actuelle de la base de données
flask db current

# Revenir à une version précédente
flask db downgrade

# Revenir à la version initiale
flask db downgrade base

# Appliquer toutes les migrations en attente
flask db upgrade
```

#### Exemple : Ajouter un champ à un modèle existant

**Étape 1** : Modifier le modèle dans `backend/models.py`

```python
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    mdp = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")
    # Nouveau champ ajouté
    telephone = db.Column(db.String(20), nullable=True)  # nullable=True pour les utilisateurs existants
```

**Étape 2** : Créer et appliquer la migration

```bash
# Entrer dans le conteneur
sudo docker compose exec backend bash

# Créer la migration
flask db migrate -m "Add telephone field to User model"

# Vérifier le fichier de migration généré dans migrations/versions/
# Le fichier contiendra quelque chose comme :
# op.add_column('users', sa.Column('telephone', sa.String(length=20), nullable=True))

# Appliquer la migration
flask db upgrade

exit
```

**Étape 3** : Utiliser le nouveau champ dans votre code

```python
# Dans routes/auth.py ou routes/admin.py
new_user = User(
    email=email,
    prenom=prenom,
    nom=nom,
    mdp=hashed_password,
    telephone=telephone  # Nouveau champ
)
```

#### Exemple : Supprimer un champ d'un modèle

**Étape 1** : Supprimer le champ dans `backend/models.py`

```python
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    mdp = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")
    # telephone supprimé
```

**Étape 2** : Créer et appliquer la migration

```bash
sudo docker compose exec backend bash
flask db migrate -m "Remove telephone field from User model"
flask db upgrade
exit
```

#### Notes importantes

- **Toujours créer une migration** avant de modifier directement la base de données
- **Vérifiez les fichiers de migration générés** dans `migrations/versions/` avant d'appliquer
- **En production**, testez d'abord les migrations en développement
- **Sauvegardez votre base de données** avant d'appliquer des migrations en production
- Les migrations sont **versionnées** et peuvent être annulées avec `flask db downgrade`

---

## Production

### Installation de Docker sur Ubuntu/Debian

#### 1. Mettre à Jour le Système

```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Installer Docker

```bash
# Installer les dépendances
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings

# Ajouter la clé GPG officielle Docker
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Ajouter le repository Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Mettre à jour et installer Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

#### 3. Vérifier l'Installation

```bash
# Vérifier le statut de Docker
sudo systemctl status docker

# Démarrer Docker si nécessaire
sudo systemctl start docker

# Tester Docker
sudo docker run hello-world
```

### Configuration de Production

#### 1. Générer une Clé Secrète Forte

```bash
openssl rand -base64 32
```

#### 2. Configurer Docker Secrets

Créez un dossier `.env_prod_secrets` à la racine du projet :

```bash
mkdir .env_prod_secrets
cd .env_prod_secrets
```

Créez des fichiers séparés pour chaque secret :

```bash
# Clé secrète (remplacez par votre clé générée)
echo "votre_cle_secrete_generee" > SECRET_KEY

# Email admin
echo "admin@votredomaine.com" > ADMIN_MAIL

# Mot de passe admin (8+ caractères, maj/min/chiffre/spécial)
echo "VotreMotDePasseSecure123!" > ADMIN_PASSWORD

# DocuSign secrets
echo "votre_docusign_account_id" > DOCUSIGN_ACCOUNT_ID
echo "votre_docusign_user_id" > DOCUSIGN_USER_ID
echo "votre_docusign_integration_key" > DOCUSIGN_INTEGRATION_KEY
```

**Note**: Les secrets sont automatiquement lus par Docker depuis `/run/secrets/` dans les conteneurs.

**Important**: Sécurisez ces fichiers !

```bash
cd ../
chmod 600 .env_prod_secrets/*
```

#### 3. Configurer les Variables d'Environnement et nginx

Changez les variables d'environnement du backend dans `docker-compose.prod.yml` :

```yaml
backend:
  environment:
    - DATABASE_URL=postgresql://user:password@db:5432/users_db # À CHANGER
    - DOCUSIGN_SERVER_IP=http://195.110.34.168:5001/api # À CHANGER
    - FRONTEND_URL=http://votre_domaine_ou_ip # À CHANGER
```

Changez les variables d'environnement du frontend dans `docker-compose.prod.yml` :

```yaml
frontend:
  args:
    - REACT_APP_BACKEND_URL=http://votre_domaine_ou_ip:5000/api # À CHANGER
```

⚠️ **Important**: Changez les identifiants de base de données dans `docker-compose.prod.yml` :

```yaml
db:
  environment:
    POSTGRES_USER: user  # À CHANGER
    POSTGRES_PASSWORD: password  # À CHANGER
```

Et mettez à jour `DATABASE_URL` dans la section backend :

```yaml
backend:
  environment:
    DATABASE_URL: postgresql://votre_utilisateur_secure:votre_mot_de_passe_secure@db:5432/users_db
```

Dans `frontend/nginx.conf`, mettez à jour l'URL du backend et le server_name :

```nginx
server {
    listen 80;
    server_name http://votre_domaine_ou_ip;  # À CHANGER

    location /api/ {
        proxy_pass http://votre_domaine_ou_ip:5000;  # À CHANGER
    }
}
```

> `Optionnel`: Vous pouvez changer le port 80 si nécessaire, mais il faudra le faire aussi dans `docker-compose.prod.yml`.

#### 4. Configurer le Pare-feu

Configurez le pare-feu pour autoriser le trafic HTTP (port 80) et HTTPS (port 443 si utilisé) :

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp  # Si vous utilisez HTTPS
sudo ufw allow OpenSSH  # Pour garder l'accès SSH
sudo ufw enable
sudo ufw status
```

#### 5. Déployer en Production

```bash
# Build les images de production
sudo docker compose -f docker-compose.prod.yml build

# Lancer en production
sudo docker compose -f docker-compose.prod.yml up -d

# Vérifier que tout fonctionne
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs -f

### 5. Accès à l'Application

- Frontend : [http://votre_domaine_ou_ip](http://votre_domaine_ou_ip)
- Backend : [http://votre_domaine_ou_ip:5000](http://votre_domaine_ou_ip:5000)
