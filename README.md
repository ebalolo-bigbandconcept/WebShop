# WebShop

Application WebShop avec frontend React/Bootstrap, backend Flask, Redis pour le cache et intégration DocuSign.

[![CI Tests](https://github.com/ebalolo-bigbandconcept/WebShop/actions/workflows/ci.yml/badge.svg)](https://github.com/ebalolo-bigbandconcept/WebShop/actions/workflows/ci.yml)
[![React](https://img.shields.io/badge/Frontend-React-blue?logo=react)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)](https://redis.io/)
[![DocuSign](https://img.shields.io/badge/DocuSign-eSign-orange?logo=docusign)](https://www.docusign.com/)

Ce README sert de guide opératoire principal pour travailler sur le projet, le déployer et le maintenir. Il propose trois parcours de lecture : développement, production et maintenance.

## Table des matières

1. [Développement](#développement)
   - [Installation locale](#1-installation-locale)
   - [Configuration locale](#2-configuration-locale)
   - [Démarrage local](#3-démarrage-local)
   - [Accès à l'application](#4-accès-à-lapplication)
   - [Qualité de code Python](#5-qualité-de-code-python)
   - [Migrations de base de données](#6-migrations-de-base-de-données)

2. [Production](#production)
   - [Préparation du serveur](#1-préparation-du-serveur)
   - [Secrets de production](#2-secrets-de-production)
   - [Configuration applicative](#3-configuration-applicative)
   - [Déployer l'application](#5-déployer-lapplication)
   - [Déploiement Traefik séparé](#4-déploiement-traefik-séparé-opttraefik--optwebshop)
   - [Sauvegarde et restauration](#6-sauvegarde-et-restauration)
   - [CI/CD et déploiement automatique](#7-cicd-et-déploiement-automatique-optionnel)

3. [Maintenance](#maintenance)
   - [Dépannage](#1-dépannage)
   - [Logs et monitoring](#2-logs-et-monitoring)

## Développement

Cette section couvre l'installation locale, le lancement de la stack Docker et les opérations de développement les plus fréquentes.

### 1. Installation locale

#### 1.1 Mettre à jour le système (production)

```bash
sudo apt update && sudo apt upgrade -y
```

#### 1.2 Ajouter le dépôt Docker

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

#### 1.3 Installer et vérifier Docker

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo systemctl start docker
sudo systemctl status docker
```

### 2. Configuration locale

#### 2.1 Générer une clé secrète

```bash
openssl rand -base64 32
```

Exemple de résultat :

```bash
0rnd5wsmCJYz9wucw4OCl3uOP3FxbRC+nV6pptA07KE=
```

#### 2.2 Créer le fichier `.env` à la racine

```bash
# Secrets et administration
SECRET_KEY=your_generated_key_here
ADMIN_MAIL=admin@example.com
ADMIN_PASSWORD=SecurePassword123!

# Configuration via proxy nginx (dev)
REACT_APP_BACKEND_URL=/api
FRONTEND_URL=https://localhost
BACKEND_URL=https://localhost

# Intégration DocuSign
DOCUSIGN_ACCOUNT_ID=your_account_id
DOCUSIGN_USER_ID=your_user_id
DOCUSIGN_INTEGRATION_KEY=your_integration_key
DOCUSIGN_SERVER_IP=123.456.789.10
```

> **Important** : remplacez toutes les valeurs `your_...` par vos identifiants réels.

### 3. Démarrage local

Ces commandes construisent les images, démarrent les conteneurs et initialisent la base lors du premier lancement.

```bash
# Construire les images Docker
sudo docker compose build

# Démarrer les conteneurs
sudo docker compose up -d

# Initialiser la base de données une seule fois
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

### 4. Accès à l'application

- Application (frontend + API via proxy) : [https://localhost](https://localhost)

> Au premier démarrage en développement, le conteneur `proxy` génère automatiquement un certificat auto-signé pour `localhost`.

### 5. Qualité de code Python

Le projet utilise `black` et `isort` pour garder un formatage cohérent. Le pipeline CI vérifie aussi ces outils.

#### 5.1 Installer les outils dans le conteneur backend

```bash
sudo docker compose exec backend pip install black isort
```

#### 5.2 Formater le code

```bash
sudo docker compose exec backend black .
sudo docker compose exec backend isort .
```

#### 5.3 Vérifier le formatage sans modifier les fichiers

```bash
sudo docker compose exec backend black --check .
sudo docker compose exec backend isort --check-only .
```

> **Note** : le CI échouera si le formatage attendu n'est pas respecté. Lancez les vérifications avant de pousser vos commits.

#### 5.4 Tests et couverture

Le backend dispose d'une suite de tests automatisés complète pour la gestion des devis.

Structure du dossier `tests/` :

```text
tests/
├── README.md
├── __init__.py
├── conftest.py
├── fixtures/
├── unit/
├── integration/
└── e2e/
```

Exécuter tous les tests :

```bash
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest'
```

Exécuter des suites spécifiques :

```bash
# Tests unitaires
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest tests/unit/'

# Tests d'intégration
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest tests/integration/'

# Fichier de test spécifique
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest tests/unit/test_devis_calculations.py'

# Classe de test spécifique
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest tests/unit/test_devis_calculations.py::TestArticleLineCalculations'

# Fonction de test spécifique
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest tests/unit/test_devis_calculations.py::TestArticleLineCalculations::test_montant_ht_calculation_basic'
```

Exécuter avec couverture :

```bash
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest --cov=. --cov-report=term-missing'
```

Exécuter avec une sortie détaillée :

```bash
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest -v'
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest -s'
sudo docker compose exec backend sh -lc 'cd /app && PYTHONPATH=/app pytest -vv'
```

> **Pourquoi cette forme ?** Dans ce projet, les imports Flask/pytest sont résolus de façon fiable en exécutant les tests depuis `/app` avec `PYTHONPATH=/app`.

Ressources utiles :

- [Documentation pytest](https://docs.pytest.org/)
- [Documentation pytest-flask](https://pytest-flask.readthedocs.io/)
- [Documentation Coverage.py](https://coverage.readthedocs.io/)

### 6. Migrations de base de données

Le projet utilise Flask-Migrate avec Alembic pour gérer le schéma de base de données.

#### 6.1 Initialiser les migrations

Cette séquence est utile uniquement lors de la toute première initialisation du projet :

```bash
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

#### 6.2 Ajouter un champ à un modèle existant

1. Modifiez le modèle concerné dans [backend/models.py](backend/models.py).
2. Générez puis appliquez la migration.
3. Utilisez le nouveau champ dans les routes ou services concernés.

Exemple de modification de modèle :

```python
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(50), nullable=False)
    prénom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    mdp = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")
    # Nouveau champ, nullable pour ne pas casser les enregistrements existants
    téléphone = db.Column(db.String(20), nullable=True)
```

Commandes associées :

```bash
# En développement
sudo docker compose exec backend flask db migrate -m "Ajouter le champ téléphone au modèle User"
sudo docker compose exec backend flask db upgrade

# En production
sudo docker compose -f docker-compose.prod.yml exec backend flask db migrate -m "Ajouter le champ telephone au modele User"
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
```

Exemple d'utilisation du champ dans le code applicatif :

```python
new_user = User(
    email=email,
    prénom=prénom,
    nom=nom,
    mdp=hashed_password,
    téléphone=téléphone,
)
```

#### 6.3 Supprimer un champ d'un modèle

1. Supprimez le champ du modèle dans [backend/models.py](backend/models.py).
2. Générez puis appliquez une migration.

Exemple de modèle après suppression :

```python
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    mdp = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")
```

Commandes associées :

```bash
sudo docker compose exec backend flask db migrate -m "Supprimer le champ téléphone du modèle User"
sudo docker compose exec backend flask db upgrade
```

#### 6.4 Commandes utiles

```bash
# Historique des migrations
sudo docker compose exec backend flask db history

# Version actuellement appliquée
sudo docker compose exec backend flask db current

# Revenir d'une migration
sudo docker compose exec backend flask db downgrade

# Revenir à l'état initial
sudo docker compose exec backend flask db downgrade base

# Appliquer toutes les migrations en attente
sudo docker compose exec backend flask db upgrade

# Créer une migration vide à compléter à la main
sudo docker compose exec backend flask db revision -m "Migration manuelle"
```

#### 6.5 Bonnes pratiques

- Créez toujours une migration avant de modifier la base manuellement.
- Vérifiez le contenu du fichier généré dans `backend/migrations/versions/` avant de l'appliquer.
- Testez d'abord les migrations en développement.
- Sauvegardez la base avant toute migration en production.
- Conservez des messages de migration explicites et courts.

## Production

Cette section couvre la préparation d'un serveur Linux, la configuration des secrets, le déploiement Docker et l'automatisation CI/CD.

### 1. Préparation du serveur

#### 1.1 Mettre à jour le système

```bash
sudo apt update && sudo apt upgrade -y
```

#### 1.2 Installer Docker

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
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

#### 1.3 Vérifier Docker

```bash
sudo systemctl start docker
sudo systemctl status docker
```

### 2. Secrets de production

#### 2.1 Créer le dossier `.env_prod_secrets`

Ce dossier contient les secrets utilisés par la stack de production.

```bash
mkdir -p .env_prod_secrets
cd .env_prod_secrets

echo "$(openssl rand -base64 32)" > SECRET_KEY.txt
echo "admin@example.com" > ADMIN_MAIL.txt
echo "SecurePassword123!" > ADMIN_PASSWORD.txt
echo "your_docusign_account_id" > DOCUSIGN_ACCOUNT_ID.txt
echo "your_docusign_user_id" > DOCUSIGN_USER_ID.txt
echo "your_docusign_integration_key" > DOCUSIGN_INTEGRATION_KEY.txt
echo "postgresql://user:password@db:5432/users_db" > DATABASE_URL.txt
echo "user" > DB_USER.txt
echo "password" > DB_PASSWORD.txt
echo "your-domain.tld" > TRAEFIK_DOMAIN.txt
echo "proxy" > TRAEFIK_NETWORK.txt
# Copiez aussi votre clé privée DocuSign private.pem dans ce dossier

cd ..
chmod 600 .env_prod_secrets/*
```

> **Important** : remplacez toutes les valeurs d'exemple par vos vrais identifiants et ne versionnez jamais ces fichiers.

### 3. Configuration applicative

#### 3.1 Configurer le pare-feu

```bash
# Politique par défaut
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH d'administration
sudo ufw allow from YOUR_ADMIN_IP to any port 22 proto tcp

# HTTP et HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Limiter les tentatives SSH
sudo ufw limit 22/tcp

# Si vous filtrez aussi les sorties, autorisez explicitement les flux nécessaires
# sudo ufw default deny outgoing
# sudo ufw allow out 53
# sudo ufw allow out 80/tcp
# sudo ufw allow out 443/tcp
# sudo ufw allow out to BACKUP_SERVER_IP port 22 proto tcp

sudo ufw enable
sudo ufw status verbose
```

> **Note** : remplacez `YOUR_ADMIN_IP` et `BACKUP_SERVER_IP` par les adresses réelles.

### 4. Déploiement Traefik séparé (/opt/traefik + /opt/WebShop)

Cette stratégie sépare l'infrastructure d'entrée (Traefik) de la stack applicative. Traefik tourne dans son propre dossier (`/opt/traefik`) et l'application dans `/opt/WebShop`.

- Traefik expose `80/443`.
- L'application n'expose pas de ports publics.
- Le routage est géré via labels Traefik sur `frontend` et `backend`.

#### 4.1 Préparer les dossiers traefik

```bash
sudo mkdir -p /opt/traefik
sudo chown -R $USER:$USER /opt/traefik
```

#### 4.2 Copier les fichiers nécessaires

Depuis la racine du projet :

```bash
cp -r traefik/* /opt/traefik/
cp traefik/.env.example /opt/traefik/.env
```

#### 4.3 Créer le réseau Docker partagé

```bash
docker network create proxy || true
```

#### 4.4 Configurer Traefik

```bash
cd /opt/traefik
cp .env.example .env

# Éditer .env et définir au minimum ACME_EMAIL
touch letsencrypt/acme.json
chmod 600 letsencrypt/acme.json
```

#### 4.5 Démarrer Traefik puis l'application

```bash
# 1) Démarrer Traefik (infra)
cd /opt/traefik
docker compose up -d

# 2) Démarrer l'application (app)
cd /opt/WebShop
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend flask db upgrade
docker compose -f docker-compose.prod.yml exec backend python init_db.py
```

### 5. Déployer l'application

#### 5.1 Construire, lancer et migrer

```bash
sudo docker compose -f docker-compose.prod.yml build
sudo docker compose -f docker-compose.prod.yml up -d
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
sudo docker compose -f docker-compose.prod.yml exec backend python init_db.py
```

#### 5.2 Vérifier l'état de la stack

```bash
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs -f
```

#### 5.3 Accès attendus

- Frontend : [http://your-domain.tld](http://your-domain.tld)
- API backend : [http://your-domain.tld/api](http://your-domain.tld/api)

### 6. Sauvegarde et restauration

#### 6.1 Configurer le dépôt de sauvegarde Restic avec Rclone et pCloud

Cette section couvre la configuration de Restic avec Rclone pour sauvegarder les données de votre application WebShop sur pCloud.

##### Créer le fichier secret et obtenir le token pCloud

Docker requiert que tous les fichiers secrets existent avant de démarrer n'importe quel conteneur. Créez d'abord le fichier placeholder :

```bash
touch .env_prod_secrets/RCLONE_CONFIG_PCLOUD_AUTH.txt
chmod 600 .env_prod_secrets/RCLONE_CONFIG_PCLOUD_AUTH.txt
```

Installez rclone sur la machine qui dispose d'un navigateur (votre poste local ou le serveur si vous avez accès à un navigateur) :

```bash
curl https://rclone.org/install.sh | sudo bash
```

Puis lancez l'autorisation :

```bash
rclone authorize "pcloud"
```

Rclone va tenter d'ouvrir un navigateur automatiquement. Si ce n'est pas possible, il affiche une URL du type `http://127.0.0.1:53682/auth?state=...` : ouvrez-la manuellement dans votre navigateur, connectez-vous à pCloud et autorisez l'accès.

Si votre serveur est en CLI Linux (sans navigateur), vous pouvez faire l'autorisation via un tunnel SSH :

1. Repérez le port dans l'URL affichée (exemple : `53682`).

2. Depuis votre machine locale, ouvrez un second terminal et créez le tunnel SSH vers ce port :

```bash
ssh -N -L 53682:127.0.0.1:53682 user@votre-serveur
ssh -N -L 53682:127.0.0.1:53682 -i "~/.ssh/votre_cle_privee" user@votre-serveur # si vous utilisez une clé privée
```

1. Sur votre machine locale, ouvrez dans le navigateur l'URL fournie par rclone (ou `http://127.0.0.1:53682/auth?...`), connectez-vous à pCloud et validez.

2. Revenez au terminal serveur : rclone y affiche le token JSON à copier dans `.env_prod_secrets/RCLONE_CONFIG_PCLOUD_AUTH.txt`.

Rclone affiche ensuite le token dans le terminal :

```json
Paste the following into your remote machine --->
{"access_token":"your_token_here","token_type":"bearer","expiry":"..."}
<---End paste
```

Copiez le JSON affiché entre les marqueurs et enregistrez-le dans le fichier secret :

```bash
echo '{"access_token":"your_token_here","token_type":"bearer","expiry":"..."}' \
  > .env_prod_secrets/RCLONE_CONFIG_PCLOUD_AUTH.txt
```

> **VPS sans navigateur** : exécutez `rclone authorize "pcloud"` depuis votre **machine locale**, récupérez le token affiché dans le terminal, puis copiez-le sur le serveur dans `.env_prod_secrets/RCLONE_CONFIG_PCLOUD_AUTH.txt`.

**Important** : Ne versionnez jamais ce token. Stockez-le uniquement dans `.env_prod_secrets/`.

##### Configurer les secrets Docker

Ajoutez les fichiers de secrets Rclone dans `.env_prod_secrets/` :

```bash
# Configuration Restic pointant vers le remote Rclone (ne modifiez pas)
echo "rclone:pcloud:/Backups/WebShop" > .env_prod_secrets/RESTIC_REPOSITORY.txt

# Générez une clé de chiffrement sécurisée pour Restic
echo "your_secure_password" > .env_prod_secrets/RESTIC_PASSWORD.txt

# Restreignez les permissions
chmod 600 .env_prod_secrets/*
```

##### Initialiser le dépôt Restic

Avant la première sauvegarde, initialisez le dépôt Restic sur pCloud :

```bash
sudo docker compose -f docker-compose.prod.yml --profile backup run --rm backup restic init
```

##### Tester une première sauvegarde manuelle

Lancez une première sauvegarde pour vérifier que tout fonctionne :

```bash
sudo docker compose -f docker-compose.prod.yml --profile backup run --rm backup
```

Observez les logs pour vérifier :

- Dumping database : la base de données est exportée
- Running restic backup : les données sont chiffrées et uploadées vers pCloud
- Applying retention policy : les anciennes sauvegardes sont nettoyées
- Backup finished : succès

##### Vérifier les snapshots dans Restic

Listez les snapshots de sauvegarde créés :

```bash
sudo docker compose -f docker-compose.prod.yml --profile backup run --rm backup restic snapshots
```

Exemple de sortie :

```bash
ID        Time                 Host         Tags  Paths
--------  -------------------  -----------  ----  ----
abc12345  2026-03-17 00:00:00  backup-host        /tmp/db_20260317_000000.sql.gz
...
```

##### Supprimer une sauvegarde

Si vous souhaitez supprimer une sauvegarde spécifique, utilisez son ID :

```bash
sudo docker compose -f docker-compose.prod.yml --profile backup run --rm backup restic forget SNAPSHOT_ID --prune
```

##### Supprimer le dépôt sur pCloud et tous les snapshots (attention, opération irréversible)

```bash
sudo docker compose -f docker-compose.prod.yml --profile backup run --rm backup rclone purge pcloud:Backups/WebShop
```

#### 6.2 Automatiser les sauvegardes

1. Ouvrez la crontab de l'utilisateur qui exécute Docker :

```bash
crontab -e
```

1. Ajoutez la tâche quotidienne :

> **Note** : changer le `/path/to/webshop` par le chemin réel de votre projet.

```bash
0 0 * * * PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /bin/bash -lc 'cd /path/to/webshop && echo "[$(date -Iseconds)] Début du backup..." >> /var/log/webshop-backup.log 2>&1 && docker compose -f docker-compose.prod.yml --profile backup run --rm backup >> /var/log/webshop-backup.log 2>&1 && echo "[$(date -Iseconds)] Backup terminé." >> /var/log/webshop-backup.log 2>&1'
```

1. Vérifiez la crontab active :

```bash
crontab -l
```

#### 6.3 Restaurer depuis une sauvegarde

```bash
sudo docker compose -f docker-compose.prod.yml --profile backup run --rm backup restore-db latest users_db
```

Cette commande restaure le snapshot Restic, recrée la base `users_db`, puis importe automatiquement le dump SQL.

> **Attention** : cette opération écrase la base cible. Arrêtez le backend avant restauration pour éviter les connexions actives.

### 7. CI/CD et déploiement automatique (optionnel)

Cette section couvre l'automatisation GitHub Actions pour tester puis déployer sur les environnements de développement et de production.

#### 7.1 Créer un utilisateur de déploiement dédié

```bash
ssh root@your-vps

useradd -m -s /bin/bash deploy
usermod -aG docker deploy
usermod -p 'StrongPassword' deploy

chown -R deploy:deploy /opt/WebShop
chown -R root:root /opt/WebShop/.env_prod_secrets
chmod 755 /opt/WebShop/.env_prod_secrets

cat >> /etc/sudoers.d/deploy << 'EOF'
deploy ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose
EOF
chmod 440 /etc/sudoers.d/deploy

su - deploy
docker ps
exit
exit
```

#### 7.2 Générer des clés SSH

```bash
# Clé de production
ssh-keygen -t ed25519 -C "ci-deploy-prod" -f ~/.ssh/webshop_deploy -N ""

# Clé de développement, si serveur distinct
ssh-keygen -t ed25519 -C "ci-deploy-dev" -f ~/.ssh/webshop_deploy_dev -N ""
```

#### 7.3 Installer les clés publiques sur le serveur

```bash
cat ~/.ssh/webshop_deploy.pub

mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh

cat >> /home/deploy/.ssh/authorized_keys << 'EOF'
ssh-ed25519 AAAA... ci-deploy-prod
EOF

chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

cp -r /root/WebShop/* /opt/WebShop/
chown -R deploy:deploy /opt/WebShop
```

#### 7.4 Ajouter les secrets GitHub

Dans le dépôt GitHub, ouvrez `Settings` > `Secrets and variables` > `Actions`, puis ajoutez :

Secrets de production :

- `SSH_HOST` : nom d'hôte ou IP du VPS
- `SSH_USER` : `deploy`
- `SSH_KEY` : contenu complet de `~/.ssh/webshop_deploy`
- `WORK_DIR` : `/opt/webshop`
- `DEPLOY_GIT_TOKEN` : optionnel, pour dépôt privé

Secrets de développement, si serveur distinct :

- `SSH_HOST_DEV` : hôte du serveur de développement
- `SSH_USER_DEV` : utilisateur de déploiement
- `SSH_KEY_DEV` : contenu complet de `~/.ssh/webshop_deploy_dev`
- `WORK_DIR_DEV` : chemin du projet sur le serveur de développement

#### 7.5 Comprendre les workflows

Le dépôt contient trois workflows GitHub Actions dans `.github/workflows/`.

Exemple de comportement pour le workflow principal CI :

- Déclenchement sur `push` et `pull_request` vers `dev` et `main`
- Tests backend avec `pytest` et couverture
- Build frontend
- Déploiement automatique vers le staging depuis `dev`
- Déploiement automatique vers la production depuis `main`

Exemple de séquence de déploiement :

```bash
# 1. Travailler en local
git checkout dev
git commit -m "Add new feature"
git push origin dev

# 2. GitHub Actions lance les tests et déploie le staging

# 3. Vérifier le staging
ssh deploy@dev-server "cd /opt/webshop && docker compose ps"

# 4. Fusionner vers main après validation
git checkout main
git pull
git merge dev
git push origin main
```

#### 7.6 Superviser les déploiements

```bash
# Suivre les logs en temps réel sur le serveur
ssh deploy@your-vps "cd /opt/webshop && docker compose logs -f backend"

# Vérifier l'état des services
ssh deploy@your-vps "cd /opt/webshop && docker compose ps"
```

#### 7.7 Renforcer l'accès SSH

Durcissez la configuration SSH sur le serveur :

```bash
ssh root@your-vps
nano /etc/ssh/ssh_config
```

Ajoutez ou adaptez :

```text
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
```

Redémarrez ensuite le service SSH :

```bash
sudo systemctl restart ssh
```

Si vous devez conserver un accès root par clé :

```bash
# Sur votre machine locale
ssh-keygen -t ed25519 -C "root-access" -f ~/.ssh/webshop_root
cat ~/.ssh/webshop_root.pub
```

Puis sur le VPS :

```bash
ssh root@your-vps
mkdir -p ~/.ssh
chmod 700 ~/.ssh

cat >> ~/.ssh/authorized_keys << 'EOF'
ssh-ed25519 AAAA...your-public-key-here... root-access
EOF

chmod 600 ~/.ssh/authorized_keys
cat ~/.ssh/authorized_keys
exit
```

#### 7.8 Dépannage CI/CD

Problème : accès refusé avec `Permission denied`

```bash
cat /home/deploy/.ssh/authorized_keys | head -1
ls -la /home/deploy/.ssh/
```

Problème : les services ne se relancent pas après déploiement

```bash
cd /opt/webshop && docker compose logs --tail=50
cd /opt/webshop && docker compose up -d
```

Problème : les migrations échouent

```bash
cd /opt/webshop && docker compose exec -T db pg_isready -U dev_user
cd /opt/webshop && docker compose exec -T backend flask db current
```

**Important** : conservez vos clés privées SSH dans un emplacement sûr. Si plusieurs administrateurs interviennent, attribuez une clé distincte à chacun.

## Maintenance

Cette section regroupe les procédures de dépannage et les commandes de suivi en exploitation.

### 1. Dépannage

Cette section regroupe les incidents les plus fréquents et une réponse rapide associée.

#### 1.1 Le backend redémarre en boucle

Cause probable : le schéma de la base de données ne correspond plus aux modèles.

```bash
sudo docker compose exec backend flask db upgrade
```

#### 1.2 La migration automatique échoue

Cause probable : Flask-Migrate ne détecte pas tous les changements complexes.

```bash
sudo docker compose exec backend flask db revision -m "Migration manuelle"
sudo docker compose exec backend flask db upgrade
```

#### 1.3 Les volumes Docker occupent trop d'espace

```bash
sudo docker volume ls
sudo docker volume prune
sudo du -sh /var/lib/docker/volumes/*/
```

#### 1.4 Réinitialiser complètement l'application

> **Attention** : cette opération supprime les données de la base et les volumes associés. Vérifiez d'abord que vous disposez d'une sauvegarde exploitable.

```bash
sudo docker compose down -v
sudo docker compose build
sudo docker compose up -d
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

#### 1.5 Sauvegardes Restic/pCloud: incidents fréquents

**Problème** : `Error: repository does not exist`

**Solution** : Exécutez `restic init` pour créer le dépôt avant la première sauvegarde.

**Problème** : `Error: couldn't find Rclone`

**Solution** : Vérifiez que le conteneur de backup peut accéder à Internet pour installer Rclone automatiquement.

**Problème** : `Error: authentication failed` ou `404 Not Found`

**Solution** : Vérifiez le contenu de `.env_prod_secrets/RCLONE_CONFIG_PCLOUD_AUTH.txt` et regénérez le token pCloud si nécessaire.

**Problème** : upload lent ou échec des sauvegardes

**Solution** : Contrôlez la connectivité réseau et relancez un backup manuel pour valider le flux.

### 2. Logs et monitoring

Ces commandes permettent de vérifier rapidement l'état de la plateforme et d'analyser les événements de sécurité.

#### 2.1 Consulter les logs applicatifs

```bash
# Logs en développement
sudo docker compose logs -f frontend
sudo docker compose logs -f backend

# Logs en production
sudo docker compose -f docker-compose.prod.yml logs -f backend
```

#### 2.2 Suivre le journal de sécurité

```bash
# Lire le journal de sécurité dans le conteneur backend
sudo docker compose -f docker-compose.prod.yml exec backend tail -f security.log

# Affichage brut des logs backend
sudo docker compose -f docker-compose.prod.yml logs -f backend

# Filtrer certaines actions avec jq
sudo docker compose -f docker-compose.prod.yml exec backend cat security.log | jq 'select(.action=="LOGIN_FAILED")'
sudo docker compose -f docker-compose.prod.yml exec backend cat security.log | jq 'select(.action=="USER_DELETED")'

# Rechercher les erreurs d'autorisation
sudo docker compose -f docker-compose.prod.yml exec backend grep "UNAUTHORIZED\|FORBIDDEN\|FAILED" security.log | jq '.'

# Copier le journal sur l'hôte
sudo docker compose -f docker-compose.prod.yml cp backend:/app/security.log ./security.log
```

Événements journalisés les plus courants :

- Authentification : `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `REGISTER`
- Gestion des utilisateurs : `USER_CREATED`, `USER_UPDATED`, `USER_DELETED`
- Contrôle d'accès : `UNAUTHORIZED_ACCESS`, `FORBIDDEN_ACCESS`
- Configuration : `PARAMETERS_UPDATED`, `VAT_CREATED`, `VAT_DELETED`

Chaque entrée contient typiquement un horodatage, un `user_id`, un `user_email`, une adresse IP, une action, une ressource et un statut.
