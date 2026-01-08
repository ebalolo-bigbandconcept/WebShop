# WebShop

Application WebShop avec frontend React/Bootstrap, backend Flask, Redis pour le cache, et intégration DocuSign.

[![React](https://img.shields.io/badge/Frontend-React-blue?logo=react)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)](https://redis.io/)
[![DocuSign](https://img.shields.io/badge/DocuSign-eSign-orange?logo=docusign)](https://www.docusign.com/)

---

## Table des matières

1. [Démarrage rapide en développement](#démarrage-rapide-en-développement)
2. [Gestion des migrations de base de données](#gestion-des-migrations-de-base-de-données)
3. [Déploiement en production](#déploiement-en-production)
4. [Support HTTPS avec Let's Encrypt](#support-https-avec-lets-encrypt)
5. [Sauvegarde et restauration](#sauvegarde-et-restauration)
6. [Dépannage](#dépannage)

---

## Démarrage rapide en développement

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
sudo docker run hello-world  # Test quick
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
sudo docker compose up -d

# Initialiser la base de données (première fois seulement)
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

### 5. Accès à l'application

- **Frontend** : [http://localhost:3000](http://localhost:3000)
- **Backend API** : [http://localhost:5000](http://localhost:5000)

---

## Gestion des migrations de base de données

Cette application utilise **Flask-Migrate** (Alembic) pour gérer les modifications du schéma de base de données.

> **Important** : Avec Flask-Migrate, `db.create_all()` n'est plus utilisé. Cela évite les redémarrages infinis du backend quand le schéma change.

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
# Install dependencies
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings

# Add Docker's official GPG key
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
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
sudo docker run hello-world  # Quick test
```

### 2. Configurer les secrets

Créez un dossier de secrets sécurisés :

```bash
mkdir -p .env_prod_secrets
cd .env_prod_secrets

# Generate and store secrets
echo "$(openssl rand -base64 32)" > SECRET_KEY.txt
echo "admin@example.com" > ADMIN_MAIL.txt
echo "SecurePassword123!" > ADMIN_PASSWORD.txt
echo "your_docusign_account_id" > DOCUSIGN_ACCOUNT_ID.txt
echo "your_docusign_user_id" > DOCUSIGN_USER_ID.txt
echo "your_docusign_integration_key" > DOCUSIGN_INTEGRATION_KEY.txt

# Secure permissions
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
    - DATABASE_URL=postgresql://secure_user:secure_password@db:5432/users_db
    - DOCUSIGN_SERVER_IP=http://your-docusign-ip:5001/api
    - FRONTEND_URL=https://your-domain.tld
```

#### 3.2 Variables du frontend

```yaml
frontend:
  build:
    args:
      - REACT_APP_BACKEND_URL=https://your-domain.tld/api
```

#### 3.3 Identifiants de base de données

```yaml
db:
  environment:
    POSTGRES_USER: secure_user
    POSTGRES_PASSWORD: secure_password
```

Dans le backend, mettez à jour `DATABASE_URL` :

```yaml
backend:
  environment:
    DATABASE_URL: postgresql://secure_user:secure_password@db:5432/users_db
```

#### 3.4 Configuration Nginx

Mettez à jour [frontend/nginx.conf](frontend/nginx.conf) :

```nginx
server {
    listen 80;
    server_name your-domain.tld;  # Change this
    
    # ... rest of configuration
}
```

### 4. Configurer le pare-feu

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow OpenSSH  # Keep SSH access
sudo ufw enable
sudo ufw status  # Verify
```

### 5. Déployer l'application

```bash
# Build production images
sudo docker compose -f docker-compose.prod.yml build

# Start services
sudo docker compose -f docker-compose.prod.yml up -d

# Initialize database with migrations
sudo docker compose -f docker-compose.prod.yml exec backend flask db init
sudo docker compose -f docker-compose.prod.yml exec backend flask db migrate -m "Initial migration"
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
sudo docker compose -f docker-compose.prod.yml exec backend python init_db.py

# Verify services are running
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs -f
```

### 6. Accéder à l'application

- **Frontend** : [http://your-domain.tld](http://your-domain.tld)
- **Backend API** : [http://your-domain.tld/api](http://your-domain.tld/api)

---

## Support HTTPS avec Let's Encrypt

### 1. Préparer la configuration

- Mettez à jour [proxy/nginx.conf](proxy/nginx.conf) avec votre domaine réel :

```nginx
server_name your-domain.tld;
ssl_certificate /etc/letsencrypt/live/your-domain.tld/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.tld/privkey.pem;
```

- Ouvrez les ports 80/443 sur le serveur (pare-feu) pour éviter les erreurs "connection refused" pendant l'ACME challenge.

### 2. Bootstrap (éviter le crash Nginx avant le vrai certificat)

Nginx ne doit pas tomber en échec si le certificat n'existe pas encore. Générez un certificat autosigné éphémère partagé via le volume `letsencrypt` :

```bash
sudo docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
  sh -c "apk add --no-cache openssl >/dev/null && \
         mkdir -p /etc/letsencrypt/live/your-domain.tld && \
         openssl req -x509 -nodes -newkey rsa:2048 -days 2 \
           -subj '/CN=your-domain.tld' \
           -keyout /etc/letsencrypt/live/your-domain.tld/privkey.pem \
           -out /etc/letsencrypt/live/your-domain.tld/fullchain.pem"
```

### 3. Démarrer les services (proxy doit écouter sur 80)

```bash
sudo docker compose -f docker-compose.prod.yml up -d --force-recreate proxy
sudo docker compose -f docker-compose.prod.yml up -d --build
```

Vérifiez que le port 80 écoute :

```bash
sudo ss -ltnp | grep ':80'
```

### 4. Obtenir le vrai certificat (webroot)

Si vous avez déjà un dossier `live/your-domain.tld` (ancien autosigné), supprimez-le avant de lancer certbot pour éviter l'erreur "live directory exists" :

```bash
sudo docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
  sh -c "rm -rf /etc/letsencrypt/live/your-domain.tld \
               /etc/letsencrypt/archive/your-domain.tld \
               /etc/letsencrypt/renewal/your-domain.tld.conf"
```

Puis lancez certbot :

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

Tâche cron recommandée :

```bash
# Run at 3 AM daily
0 3 * * * cd /path/to/WebShop && \
  docker compose -f docker-compose.prod.yml run --rm certbot renew --webroot -w /var/www/certbot && \
  docker compose -f docker-compose.prod.yml exec -T proxy nginx -s reload
```

### 7. Vérifications

- ✅ Accès HTTPS et certificat valide
- ✅ Pas de mixed-content
- ✅ Cookies avec flag `Secure`
- ✅ Logs Nginx : `sudo docker compose -f docker-compose.prod.yml logs -f proxy`

---

## Sauvegarde et restauration

### Sauvegarde de la base de données

```bash
# Create timestamped backup
sudo docker compose -f docker-compose.prod.yml exec db pg_dump -U secure_user users_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restauration de la base de données

```bash
# Restore from backup
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
# Edit backend/migrations/versions/xxx_manual_migration.py
sudo docker compose exec backend flask db upgrade
```

### Les volumes Docker occupent trop d'espace

```bash
# List all volumes
sudo docker volume ls

# Remove unused volumes (caution!)
sudo docker volume prune

# See volume size
sudo du -sh /var/lib/docker/volumes/*/
```

### Voir les logs en temps réel

```bash
# Development
sudo docker compose logs -f

# Production
sudo docker compose -f docker-compose.prod.yml logs -f

# Specific service
sudo docker compose logs -f backend  # or 'frontend', 'db', etc.
```

### Réinitialiser complètement l'application

```bash
# CAUTION: This will delete ALL data!
sudo docker compose down -v
sudo docker compose build
sudo docker compose up -d
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

---

## Support DocuSign

### Configuration de l'intégration

1. Créez une application sur [DocuSign Developer](https://developer.docusign.com/)
2. Choisissez **Private custom integration**
3. Générez les clés RSA : `private.pem` et `public.pem`
4. Ajoutez la Redirect URI : `https://www.google.com`
5. Autorisez les requêtes HTTP POST

### Obtenir le consentement OAuth

Pour chaque utilisateur DocuSign, accédez à cette URL une fois :

``` bash
https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature%20impersonation&client_id=YOUR_INTEGRATION_ID&redirect_uri=https://www.google.com
```

> Remplacez `YOUR_INTEGRATION_ID` par votre clé d'intégration.

---

## Informations utiles

| Service | Port | URL |
| --------- | ------ | ----- |
| Frontend | 3000 | <http://localhost:3000> |
| Backend API | 5000 | <http://localhost:5000> |
| Database | 5432 | postgresql://localhost:5432 |
| Redis | 6379 | redis://localhost:6379 |

## Aide et support

Pour toute question ou problème :

1. Consultez les logs : `sudo docker compose logs -f`
2. Vérifiez les fichiers de configuration
3. Assurez-vous que tous les services sont en cours d'exécution : `sudo docker compose ps`
4. Consultez la documentation officielle de [Flask](https://flask.palletsprojects.com/), [React](https://reactjs.org/), ou [Docker](https://docs.docker.com/)

Quand vous modifiez `models.py` (ajout/suppression de colonnes, tables, etc.), créez une migration :

```bash
# En développement
sudo docker compose exec backend flask db migrate -m "Description des changements"
sudo docker compose exec backend flask db upgrade

# En production
sudo docker compose -f docker-compose.prod.yml exec backend flask db migrate -m "Description des changements"
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
```

### Revenir en arrière (downgrade)

```bash
# Revenir d'une migration
sudo docker compose exec backend flask db downgrade

# Voir l'historique des migrations
sudo docker compose exec backend flask db history
```

### Problèmes courants

**Backend redémarre en boucle** : Cela arrive quand le schéma DB ne correspond pas aux modèles. Appliquez les migrations :

```bash
sudo docker compose exec backend flask db upgrade
```

**Migration automatique échoue** : Parfois Flask-Migrate ne détecte pas tous les changements. Créez une migration vide et éditez-la manuellement :

```bash
sudo docker compose exec backend flask db revision -m "Manual migration"
# Éditez ensuite le fichier dans backend/migrations/versions/
```
