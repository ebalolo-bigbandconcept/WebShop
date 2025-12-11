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

#### 3. Configurer les Variables d'Environnement

Changez les variables d'environnement du backend dans `docker-compose.prod.yml` :

```yaml
backend:
  environment:
    - DATABASE_URL=postgresql://user:password@db:5432/users_db # À CHANGER
    - DOCUSIGN_SERVER_IP=http://195.110.34.168:5001/api # À CHANGER
    - DOCUSIGN_BASE_PATH=https://demo.docusign.net/restapi # À CHANGER
```

⚠️ **Important**: Changez les identifiants de base de données dans `docker-compose.prod.yml` :

```yaml
db:
  environment:
    POSTGRES_USER: votre_utilisateur_secure  # À CHANGER
    POSTGRES_PASSWORD: votre_mot_de_passe_secure  # À CHANGER
```

Et mettez à jour `DATABASE_URL` dans la section backend :

```yaml
backend:
  environment:
    DATABASE_URL: postgresql://votre_utilisateur_secure:votre_mot_de_passe_secure@db:5432/users_db
```

#### 4. Déployer en Production

```bash
# Build les images de production
sudo docker compose -f docker-compose.prod.yml build

# Lancer en production
sudo docker compose -f docker-compose.prod.yml up -d

# Vérifier que tout fonctionne
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs -f

# Initialiser la base de données (première fois uniquement)
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
```

### 5. Accès à l'Application

- Frontend : [http://votre_domaine_ou_ip](http://votre_domaine_ou_ip)
- Backend : [http://votre_domaine_ou_ip:5000](http://votre_domaine_ou_ip:5000)
