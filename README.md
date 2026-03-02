# WebShop

Application WebShop avec frontend React/Bootstrap, backend Flask, Redis pour le cache, et intégration DocuSign.

[![CI Tests](https://github.com/ebalolo-bigbandconcept/WebShop/actions/workflows/ci.yml/badge.svg)](https://github.com/ebalolo-bigbandconcept/WebShop/actions/workflows/ci.yml)
[![React](https://img.shields.io/badge/Frontend-React-blue?logo=react)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)](https://redis.io/)
[![DocuSign](https://img.shields.io/badge/DocuSign-eSign-orange?logo=docusign)](https://www.docusign.com/)

---

## Table des matières

### 📚 Documentation

1. [Démarrage rapide - Développement](#démarrage-rapide--développement)
2. [Gestion des migrations de base de données](#gestion-des-migrations-de-base-de-données)

### 🚀 Déploiement & Production

1. [Déploiement en production](#déploiement-en-production)
2. [Configuration CI/CD et déploiement automatique](#configuration-cicd-et-déploiement-automatique)
3. [Support HTTPS avec Let's Encrypt](#support-https-avec-lets-encrypt)

### 💾 Exploitation & Maintenance

1. [Sauvegarde et restauration](#sauvegarde-et-restauration)
2. [Logs et monitoring](#logs-et-monitoring)
3. [Dépannage](#dépannage)
4. [Aide et support](#aide-et-support)

---

## Démarrage rapide — Développement

### 1. Mettre à jour le système

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Installer Docker

#### 2.1 Ajouter le repository Docker

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

#### 2.2 Installer Docker

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo systemctl start docker
sudo systemctl status docker
```

### 3. Configurer les variables d'environnement

#### 3.1 Générer une clé secrète

```bash
openssl rand -base64 32
```

Exemple de résultat :

``` bash
0rnd5wsmCJYz9wucw4OCl3uOP3FxbRC+nV6pptA07KE=
```

#### 3.2 Créer le fichier `.env` à la racine

```bash
# Secret & Administration
SECRET_KEY=your_generated_key_here
ADMIN_MAIL=admin@example.com
ADMIN_PASSWORD=SecurePassword123!

# Frontend configuration
REACT_APP_BACKEND_URL=http://localhost:5000

# DocuSign integration
DOCUSIGN_ACCOUNT_ID=your_account_id
DOCUSIGN_USER_ID=your_user_id
DOCUSIGN_INTEGRATION_KEY=your_integration_key
DOCUSIGN_SERVER_IP=123.456.789.10
```

> **Note** : Remplacez tous les `your_...` par vos identifiants réels.

### 4. Lancer l'application

```bash
# Build des images Docker
sudo docker compose build

# Démarrer les conteneurs
sudo docker compose --profile proxy-only up -d

# Initialiser la base de données (première fois seulement)
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

### 5. Accès à l'application

- **Frontend** : [http://localhost:3000](http://localhost:3000)
- **Backend API** : [http://localhost:5000](http://localhost:5000)

### 6. Formatage du code Python

Cette application utilise **Black** et **isort** pour assurer un formatage cohérent du code Python. Ces outils sont également utilisés dans le CI/CD pour vérifier le formatage.

#### Installer les outils de formatage dans le conteneur

```bash
# Installer black et isort dans le conteneur backend
sudo docker compose exec backend pip install black isort
```

#### Formater le code

```bash
# Formater tous les fichiers Python avec black
sudo docker compose exec backend black .

# Organiser les imports avec isort
sudo docker compose exec backend isort .
```

#### Vérifier le formatage (sans modifier les fichiers)

```bash
# Vérifier avec black (comme dans le CI)
sudo docker compose exec backend black --check .

# Vérifier avec isort (comme dans le CI)
sudo docker compose exec backend isort --check-only .
```

> **Note** : Le CI/CD échouera si le code n'est pas correctement formaté. Exécutez toujours `black .` et `isort .` avant de pousser vos commits.

#### Configuration

- **Black** : Utilise les paramètres par défaut (ligne de 88 caractères)
- **isort** : Compatible avec Black (profil automatique)

---

## Gestion des migrations de base de données

Cette application utilise **Flask-Migrate** (Alembic) pour gérer les modifications du schéma de base de données.

### Initialisation (première fois uniquement)

```bash
# Create migrations folder and apply initial migration
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

### Ajouter un champ à un modèle existant

**Étape 1** : Modifier le modèle dans [backend/models.py](backend/models.py)

```python
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    mdp = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")
    # New field added - use nullable=True for existing records
    telephone = db.Column(db.String(20), nullable=True)
```

**Étape 2** : Créer et appliquer la migration

```bash
# Development
sudo docker compose exec backend flask db migrate -m "Add telephone field to User model"
sudo docker compose exec backend flask db upgrade

# Production
sudo docker compose -f docker-compose.prod.yml exec backend flask db migrate -m "Add telephone field to User model"
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
```

Vérifiez le fichier généré dans `backend/migrations/versions/`

**Étape 3** : Utiliser le nouveau champ

```python
# In routes/auth.py or routes/admin.py
new_user = User(
    email=email,
    prenom=prenom,
    nom=nom,
    mdp=hashed_password,
    telephone=telephone  # New field
)
```

### Supprimer un champ d'un modèle

**Étape 1** : Supprimer le champ dans [backend/models.py](backend/models.py)

```python
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    mdp = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")
    # telephone field removed
```

**Étape 2** : Créer et appliquer la migration

```bash
sudo docker compose exec backend flask db migrate -m "Remove telephone field from User model"
sudo docker compose exec backend flask db upgrade
```

### Commandes utiles

```bash
# See migration history
sudo docker compose exec backend flask db history

# See current database version
sudo docker compose exec backend flask db current

# Rollback one migration
sudo docker compose exec backend flask db downgrade

# Rollback to initial version
sudo docker compose exec backend flask db downgrade base

# Apply all pending migrations
sudo docker compose exec backend flask db upgrade

# Create empty migration (manual editing required)
sudo docker compose exec backend flask db revision -m "Manual migration"
```

### Bonnes pratiques

- ✅ **Toujours créer une migration** avant de modifier directement la base de données
- ✅ **Vérifiez les fichiers** générés dans `backend/migrations/versions/` avant d'appliquer
- ✅ **En production** : Testez d'abord les migrations en développement
- ✅ **Sauvegardez la BD** avant d'appliquer des migrations en production
- ✅ Les migrations sont **versionnées** et réversibles

---

## Déploiement en production

### Prérequis

Vous avez besoin de :

- Une machine Linux (Ubuntu/Debian recommandé)
- Accès SSH et droits sudo
- Un domaine (optionnel, pour HTTPS)
- Les identifiants DocuSign (si intégration utilisée)

### 1. Installation de Docker

#### 1.1 Mettre à jour le système

```bash
sudo apt update && sudo apt upgrade -y
```

#### 1.2 Installer Docker

```bash
# Installer les dépendances
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings

# Ajouter la clé GPG de Docker
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Ajouter le repository Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

#### 1.3 Vérifier l'installation

```bash
sudo systemctl start docker
sudo systemctl status docker
```

### 2. Configurer les secrets

Créez un dossier de secrets sécurisés :

```bash
mkdir -p .env_prod_secrets
cd .env_prod_secrets

# Générer les fichiers de secrets
echo "$(openssl rand -base64 32)" > SECRET_KEY.txt
echo "admin@example.com" > ADMIN_MAIL.txt
echo "SecurePassword123!" > ADMIN_PASSWORD.txt
echo "your_docusign_account_id" > DOCUSIGN_ACCOUNT_ID.txt
echo "your_docusign_user_id" > DOCUSIGN_USER_ID.txt
echo "your_docusign_integration_key" > DOCUSIGN_INTEGRATION_KEY.txt
echo "postgresql://user:password@db:5432/users_db" > DATABASE_URL.txt # Change user/password
echo "user" > DB_USER.txt
echo "password" > DB_PASSWORD.txt
# Copiez aussi votre clé privée DocuSign (private.pem) dans ce dossier

# Permissions sécurisées
cd ..
chmod 600 .env_prod_secrets/*
```

> **Important** : Remplacez les valeurs par vos identifiants réels.

### 3. Configurer l'application

Mettez à jour [docker-compose.prod.yml](docker-compose.prod.yml) avec :

#### 3.1 Variables du backend

```yaml
backend:
  environment:
    - DOCUSIGN_SERVER_IP=http://your-docusign-ip
    - FRONTEND_URL=https://your-domain.tld
    - REACT_APP_BACKEND_URL=https://your-domain.tld/api
```

#### 3.2 Configuration Nginx

Mettez à jour [frontend/nginx.conf](frontend/nginx.conf) et [proxy/nginx.conf](proxy/nginx.conf) avec votre domaine réel :

```nginx
  server_name your-domain.tld;  # Changer toutes les occurrences de 'server_name'
```

### 4. Configurer le pare-feu

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow OpenSSH  # Garder l'accès SSH (optionnel mais recommandé)
sudo ufw enable
sudo ufw status
```

### 5. Déployer l'application

```bash
# Build images Docker
sudo docker compose -f docker-compose.prod.yml build

# Démarrer les conteneurs en arrière-plan
sudo docker compose -f docker-compose.prod.yml up -d

# Initialiser la base de données
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
sudo docker compose -f docker-compose.prod.yml exec backend python init_db.py

# Vérifier que tout fonctionne
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs -f
```

### 6. Configurer le certificat SSL

Voir la section [Support HTTPS avec Let's Encrypt](#support-https-avec-lets-encrypt) ci-dessous.

### 7. Configurer le CI/CD et déploiement automatique

Voir la section [Configuration CI/CD et déploiement automatique](#configuration-cicd-et-déploiement-automatique) ci-dessous.

### 8. Accéder à l'application

- **Frontend** : [http://your-domain.tld](http://your-domain.tld)
- **Backend API** : [http://your-domain.tld/api](http://your-domain.tld/api)

---

## Configuration CI/CD et Déploiement Automatique

> **Note** : Cette section couvre la configuration de GitHub Actions pour tester automatiquement et déployer vers les serveurs de production et développement.

### 1. Créer un Utilisateur Déploiement (Recommandé)

Sur votre serveur, créez un utilisateur dédié avec accès Docker (au lieu d'utiliser root) :

```bash
ssh root@your-vps

# Créer utilisateur
useradd -m -s /bin/bash deploy
usermod -aG docker deploy
usermod -p 'StrongPassword' deploy  # Changez le mot de passe

# Donner ownership à deploy sauf .env_prod_secrets
chown -R deploy:deploy /opt/WebShop
chown -R root:root /opt/WebShop/.env_prod_secrets
chmod 755 /opt/WebShop/.env_prod_secrets  # Lisible par deploy mais modifiable que par root

# Configuration sudo pour docker (optionnel)
cat >> /etc/sudoers.d/deploy << 'EOF'
deploy ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose
EOF
chmod 440 /etc/sudoers.d/deploy

# Vérifier
su - deploy
docker ps  # Devrait fonctionner sans sudo
exit
exit
```

### 2. Générer des Clés SSH

Sur votre machine locale :

```bash
# Clé pour production
ssh-keygen -t ed25519 -C "ci-deploy-prod" -f ~/.ssh/webshop_deploy -N ""

# Clé pour développement (optionnel, si dev server différent)
ssh-keygen -t ed25519 -C "ci-deploy-dev" -f ~/.ssh/webshop_deploy_dev -N ""
```

### 3. Installer Clés Publiques sur le Serveur

```bash
# Copier la clé publique
cat ~/.ssh/webshop_deploy.pub

# Installer pour utilisateur 'deploy'
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh

# Ajouter la clé (coller le contenu de webshop_deploy.pub)
cat >> /home/deploy/.ssh/authorized_keys << 'EOF'
ssh-ed25519 AAAA... ci-deploy-prod
EOF

chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

# Copier l'application
cp -r /root/WebShop/* /opt/WebShop/
chown -R deploy:deploy /opt/WebShop
exit
```

### 4. Ajouter les Secrets GitHub

Dans votre dépôt GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** :

#### Secrets Production

- **SSH_HOST** : votre VPS hostname ou IP (ex: `example.com` ou `123.45.67.89`)
- **SSH_USER** : `deploy`
- **SSH_KEY** : Contenu complet de `~/.ssh/webshop_deploy` (y compris `-----BEGIN OPENSSH PRIVATE KEY-----` et `-----END OPENSSH PRIVATE KEY-----`)
- **WORK_DIR** : `/opt/webshop`
- **DEPLOY_GIT_TOKEN** (optionnel) : GitHub PAT si repo privé

#### Secrets Développement (si dev server différent)

- **SSH_HOST_DEV** : hostname dev
- **SSH_USER_DEV** : `deploy` (ou autre utilisateur)
- **SSH_KEY_DEV** : Contenu de `~/.ssh/webshop_deploy_dev`
- **WORK_DIR_DEV** : `/opt/webshop-dev` (ou votre chemin dev)

### 5. Comment Fonctionne CI/CD

#### Workflows Disponibles

Trois workflows GitHub Actions sont disponibles dans `.github/workflows/` :

**1. CI Tests & Build** (`.github/workflows/ci.yml`)

- Déclenché sur : `push` et `pull_request` vers `dev` et `main`
- Teste : Backend (pytest + coverage), Frontend (build)
- Déploie automatiquement :
  - `dev` branch → **Staging server** (deploy-staging)
  - `main` branch → **Production server** (deploy-production)

**2. Docker Publish** (`.github/workflows/docker-publish.yml`)

- Déclenché sur : `push` vers `dev` et `main`
- Pousse vers : GitHub Container Registry (GHCR)
  - `dev` → `ghcr.io/owner/webshop-backend:dev`
  - `main` → `ghcr.io/owner/webshop-backend:latest`

**3. Nightly** (`.github/workflows/nightly.yml`)

- Déclenché : Tous les jours à 02:00 UTC
- Exécute : Full test suite, security scan (Trivy), dependency audit
- Pousse : Images avec tag `nightly`

#### Exemple de Déploiement

```bash
# 1. Faire des modifications localement
git checkout dev
git commit -m "Add new feature"
git push origin dev

# 2. GitHub Actions déclenche automatiquement :
#    - Exécute les tests backend & frontend
#    - Si tests réussissent, déploie sur staging server
#    - Logs visibles dans Actions tab

# 3. Vérifier le déploiement sur staging
ssh deploy@dev-server "cd /opt/webshop && docker compose ps"

# 4. Une fois validé, merger vers main
git checkout main
git pull
git merge dev
git push origin main

# 5. Production se déploie automatiquement !
```

### 6. Monitorer les Déploiements

```bash
# Voir tous les déploiements
# GitHub repo → Actions tab

# Logs en temps réel sur le serveur
ssh deploy@your-vps "cd /opt/webshop && docker compose logs -f backend"

# Vérifier santé des services
ssh deploy@your-vps "cd /opt/webshop && docker compose ps"
```

### 7. Sécurité SSH (Recommandé)

Durcir SSH sur le serveur :

```bash
ssh root@your-vps

nano /etc/ssh/ssh_config

# Ajouter/modifier :
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
```

### 7.1 Configurer une clé SSH pour l'accès root

Si vous avez besoin d'accès SSH root pour certaines opérations, vous pouvez configurer une authentification par clé au lieu d'utiliser le mot de passe.

#### Sur votre machine locale (générer la clé)

```bash
# Générer une nouvelle clé SSH pour l'accès root
ssh-keygen -t ed25519 -C "root-access" -f ~/.ssh/webshop_root
cat ~/.ssh/webshop_root.pub

# Laissez la passphrase vide (ou définissez-en une pour plus de sécurité)
# Passphrase vide : connexion sans prompt (recommandé pour les scripts)
# Avec passphrase : connexion sécurisée mais nécessite d'entrer le mot de passe
```

#### Sur le VPS (ajouter la clé publique)

```bash
ssh root@your-vps

# Créer le dossier .ssh s'il n'existe pas
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Ajouter votre clé publique à authorized_keys
cat >> ~/.ssh/authorized_keys << 'EOF'
ssh-ed25519 AAAA...your-public-key-here... root-access
EOF

# Définir les permissions correctes
chmod 600 ~/.ssh/authorized_keys

# Vérifier que la clé est bien ajoutée
cat ~/.ssh/authorized_keys

exit
```

#### Sauvegarde de la clé

```bash
# Sur votre machine locale, sauvegardez la clé privée dans un endroit sûr
cat ~/.ssh/webshop_root
```

Redémarrez le service SSH pour appliquer les changements :

```bash
sudo systemctl restart ssh
```

### 8. Dépannage CI/CD

#### Conserver l'accès SSH pour la maintenance

**Important** : Gardez précieusement votre clé privée SSH (`~/.ssh/webshop_deploy`) sur votre machine locale. C'est cette clé qui vous permet de vous connecter au serveur pour les opérations de maintenance manuelle.

```bash
# Sauvegardez votre clé dans un endroit sûr
cat ~/.ssh/webshop_deploy 
```

> **Conseil** : Si vous travaillez en équipe, chaque administrateur devrait avoir sa propre clé SSH ajoutée au fichier `~/.ssh/authorized_keys` du serveur.

#### Déploiement échoue avec "Permission denied"

```bash
# Vérifier permissions de clé publique sur serveur
cat /home/deploy/.ssh/authorized_keys | head -1

# Vérifier permissions du répertoire
ls -la /home/deploy/.ssh/
# Doit être : drwx------ (700)
```

#### Services ne se relancent pas après déploiement

```bash
# Vérifier les logs
cd /opt/webshop && docker compose logs --tail=50

# Redémarrer manuellement
cd /opt/webshop && docker compose up -d
```

#### Migrations échouent

```bash
# Vérifier la base de données
cd /opt/webshop && docker compose exec -T db pg_isready -U dev_user

# Voir les migrations appliquées
cd /opt/webshop && docker compose exec -T backend flask db current
```

---

## Support HTTPS avec Let's Encrypt

> **Note importante** : Remplacez `your-domain.tld` par votre vrai domaine dans toutes les commandes ci-dessous.

### 1. Préparer la configuration

- Mettez à jour [proxy/nginx.conf](proxy/nginx.conf) avec votre domaine réel :

```nginx
server_name your-domain.tld;
ssl_certificate /etc/letsencrypt/live/your-domain.tld/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.tld/privkey.pem;
```

### 2. Bootstrap (éviter le crash Nginx avant le vrai certificat)

Générez un certificat autosigné éphémère partagé via le volume `letsencrypt` :

> Remplacez `your-domain.tld` par votre domaine réel.

```bash
sudo docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
  sh -c "apk add --no-cache openssl >/dev/null && \
         mkdir -p /etc/letsencrypt/live/your-domain.tld && \
         openssl req -x509 -nodes -newkey rsa:2048 -days 2 \
           -subj '/CN=your-domain.tld' \
           -keyout /etc/letsencrypt/live/your-domain.tld/privkey.pem \
           -out /etc/letsencrypt/live/your-domain.tld/fullchain.pem"
```

### 3. Démarrer les services

```bash
sudo docker compose -f docker-compose.prod.yml up -d --force-recreate proxy
sudo docker compose -f docker-compose.prod.yml up -d --build
```

Vérifiez que le port 80 écoute :

```bash
sudo ss -ltnp | grep ':80'
```

### 4. Obtenir le vrai certificat (webroot)

Supprimer l'ancien certificat autosigné avant de lancer certbot :

> Remplacez `your-domain.tld` par votre domaine réel.

```bash
sudo docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
  sh -c "rm -rf /etc/letsencrypt/live/your-domain.tld \
               /etc/letsencrypt/archive/your-domain.tld \
               /etc/letsencrypt/renewal/your-domain.tld.conf"
```

Puis lancez certbot :

> Remplacez `your-domain.tld` par votre domaine réel.
> Remplacez `admin@example.com` par votre adresse email.

```bash
sudo docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d your-domain.tld \
  --email admin@example.com \
  --agree-tos --no-eff-email
```

### 5. Recharger Nginx pour utiliser le certificat Let’s Encrypt

```bash
sudo docker compose -f docker-compose.prod.yml exec -T proxy nginx -s reload
```

### 6. Renouvellement automatique

Les certificats Let's Encrypt expirent après 90 jours. Configurez une tâche cron pour les renouveler automatiquement.

#### 6.1 Ouvrir l'éditeur crontab

```bash
crontab -e
```

#### 6.2 Ajouter la tâche de renouvellement

Ajoutez cette ligne à la fin du fichier crontab :

> **Note importante** : Remplacez `/path/to/WebShop` par le chemin absolu de votre projet.

```bash
# Renouvellement Let's Encrypt à 3h du matin tous les jours
0 3 * * * cd /path/to/WebShop && docker compose -f docker-compose.prod.yml run --rm certbot renew --webroot -w /var/www/certbot && docker compose -f docker-compose.prod.yml exec -T proxy nginx -s reload >> /var/log/certbot-renew.log 2>&1
```

#### 6.4 Vérifier la tâche cron

```bash
crontab -l
```

#### 6.5 Tester le renouvellement manuellement

```bash
sudo docker compose -f docker-compose.prod.yml run --rm certbot renew --webroot -w /var/www/certbot --dry-run
```

Le flag `--dry-run` teste le renouvellement sans modifier les certificats réels.

---

## Sauvegarde et restauration

### Sauvegarde de la base de données

```bash
# Créer une backup
sudo docker compose -f docker-compose.prod.yml exec db pg_dump -U secure_user users_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restauration de la base de données

```bash
# Restauration depuis une backup
sudo docker compose -f docker-compose.prod.yml exec -T db psql -U secure_user users_db < backup_20240127_120000.sql
```

---

## Dépannage

### Le backend redémarre en boucle

**Cause** : Le schéma de la base de données ne correspond pas aux modèles.

**Solution** :

```bash
sudo docker compose exec backend flask db upgrade
```

### La migration automatique échoue

**Cause** : Flask-Migrate ne détecte pas tous les changements complexes.

**Solution** : Créer une migration vide et la modifier manuellement

```bash
sudo docker compose exec backend flask db revision -m "Manual migration"
sudo docker compose exec backend flask db upgrade
```

### Les volumes Docker occupent trop d'espace

```bash
# Lister tous les volumes
sudo docker volume ls

# Retirer les volumes inutilisés
sudo docker volume prune

# Vérifier la taille des volumes
sudo du -sh /var/lib/docker/volumes/*/
```

### Réinitialiser complètement l'application

```bash
# ATTENTION : Cela supprimera toutes les données !
sudo docker compose down -v
sudo docker compose build
sudo docker compose up -d
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

---

## Logs et monitoring

### Consulter les logs

```bash
# Logs applicatifs (développement)
sudo docker compose logs -f frontend
sudo docker compose logs -f backend

# Logs applicatifs (production)
sudo docker compose -f docker-compose.prod.yml logs -f backend

# Journaux de sécurité (format JSON)
# Application logs (production)
sudo docker compose -f docker-compose.prod.yml exec backend tail -f security.log

# Affichage JSON lisible (nécessite jq)
sudo docker compose -f docker-compose.prod.yml logs -f backend

# Filtrer par type d'action
sudo docker compose -f docker-compose.prod.yml exec backend cat security.log | jq 'select(.action=="LOGIN_FAILED")'
sudo docker compose -f docker-compose.prod.yml exec backend cat security.log | jq 'select(.action=="USER_DELETED")'

# Rechercher les accès non autorisés / erreurs
sudo docker compose -f docker-compose.prod.yml exec backend grep "UNAUTHORIZED\|FORBIDDEN\|FAILED" security.log | jq '.'

# Copier le journal de sécurité sur l'hôte
sudo docker compose -f docker-compose.prod.yml cp backend:/app/security.log ./security.log
```

### Événements de sécurité journalisés

- Authentification : `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `REGISTER`
- Gestion des utilisateurs : `USER_CREATED`, `USER_UPDATED`, `USER_DELETED`
- Contrôle d'accès : `UNAUTHORIZED_ACCESS`, `FORBIDDEN_ACCESS`
- Configuration : `PARAMETERS_UPDATED`, `VAT_CREATED`, `VAT_DELETED`

Chaque entrée contient : horodatage, user_id, user_email, adresse IP, action, ressource, statut.