# WebShop

Application WebShop avec frontend React/Bootstrap, backend Flask, Redis pour le cache et integration DocuSign.

[![CI Tests](https://github.com/ebalolo-bigbandconcept/WebShop/actions/workflows/ci.yml/badge.svg)](https://github.com/ebalolo-bigbandconcept/WebShop/actions/workflows/ci.yml)
[![React](https://img.shields.io/badge/Frontend-React-blue?logo=react)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)](https://redis.io/)
[![DocuSign](https://img.shields.io/badge/DocuSign-eSign-orange?logo=docusign)](https://www.docusign.com/)

Ce README sert de guide operatoire principal pour travailler sur le projet, le deployer et le maintenir. Il conserve trois parcours de lecture : developpement, production et maintenance.

**Acces rapide**

- Demarrage local : [Demarrage local](#demarrage-local)
- Migrations de base de donnees : [Migrations de base de donnees](#migrations-de-base-de-donnees)
- Deploiement production : [Deployer lapplication](#deployer-lapplication)
- HTTPS avec Let's Encrypt : [HTTPS avec Let's Encrypt](#https-avec-lets-encrypt)
- Sauvegarde Restic : [Sauvegarde et restauration](#sauvegarde-et-restauration)
- Depannage courant : [Depannage](#depannage)

**Table des matieres**

1. [Developpement](#developpement)
2. [Production](#production)
3. [Maintenance](#maintenance)

Sous-sections principales :

- Developpement : prerequis, installation locale, configuration, demarrage, acces, qualite de code, migrations
- Production : prerequis, preparation serveur, secrets, configuration applicative, deploiement, HTTPS, CI/CD
- Maintenance : sauvegarde et restauration, depannage, logs et monitoring

## Developpement

Cette section couvre l'installation locale, le lancement de la stack Docker et les operations de developpement les plus frequentes.

### Prerequis

Avant de commencer, preparez :

- Une machine Linux, idealement Ubuntu ou Debian
- Un acces `sudo`
- Docker et Docker Compose
- Les identifiants DocuSign si vous utilisez l'integration

### Installation locale

#### Mettre a jour le systeme

```bash
sudo apt update && sudo apt upgrade -y
```

#### Ajouter le depot Docker

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

#### Installer et verifier Docker

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo systemctl start docker
sudo systemctl status docker
```

### Configuration locale

#### Generer une cle secrete

```bash
openssl rand -base64 32
```

Exemple de resultat :

```bash
0rnd5wsmCJYz9wucw4OCl3uOP3FxbRC+nV6pptA07KE=
```

#### Creer le fichier `.env` a la racine

```bash
# Secrets et administration
SECRET_KEY=your_generated_key_here
ADMIN_MAIL=admin@example.com
ADMIN_PASSWORD=SecurePassword123!

# Configuration frontend
REACT_APP_BACKEND_URL=http://localhost:5000

# Integration DocuSign
DOCUSIGN_ACCOUNT_ID=your_account_id
DOCUSIGN_USER_ID=your_user_id
DOCUSIGN_INTEGRATION_KEY=your_integration_key
DOCUSIGN_SERVER_IP=123.456.789.10
```

> **Important** : remplacez toutes les valeurs `your_...` par vos identifiants reels.

### Demarrage local

Ces commandes construisent les images, demarrent les conteneurs et initialisent la base lors du premier lancement.

```bash
# Construire les images Docker
sudo docker compose build

# Demarrer les conteneurs
sudo docker compose --profile proxy-only up -d

# Initialiser la base de donnees une seule fois
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

### Acces a l'application

- Frontend : [http://localhost:3000](http://localhost:3000)
- API backend : [http://localhost:5000](http://localhost:5000)

### Qualite de code Python

Le projet utilise `black` et `isort` pour garder un formatage coherent. Le pipeline CI verifie aussi ces outils.

#### Installer les outils dans le conteneur backend

```bash
sudo docker compose exec backend pip install black isort
```

#### Formater le code

```bash
sudo docker compose exec backend black .
sudo docker compose exec backend isort .
```

#### Verifier le formatage sans modifier les fichiers

```bash
sudo docker compose exec backend black --check .
sudo docker compose exec backend isort --check-only .
```

#### Tests et couverture

Pour les suites de tests detaillees, consultez [backend/tests/README.md](backend/tests/README.md).

Commande utile pour lancer la couverture backend dans le conteneur :

```bash
sudo docker compose exec backend pytest --cov=. --cov-report=term-missing
```

> **Note** : le CI echouera si le formatage attendu n'est pas respecte. Lancez les verifications avant de pousser vos commits.

### Migrations de base de donnees

Le projet utilise Flask-Migrate avec Alembic pour gerer le schema de base de donnees.

#### Initialiser les migrations

Cette sequence est utile uniquement lors de la toute premiere initialisation du projet :

```bash
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

#### Ajouter un champ a un modele existant

1. Modifiez le modele concerne dans [backend/models.py](backend/models.py).
2. Generez puis appliquez la migration.
3. Utilisez le nouveau champ dans les routes ou services concernes.

Exemple de modification de modele :

```python
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, autoincrement=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    mdp = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")
    # Nouveau champ, nullable pour ne pas casser les enregistrements existants
    telephone = db.Column(db.String(20), nullable=True)
```

Commandes associees :

```bash
# En developpement
sudo docker compose exec backend flask db migrate -m "Ajouter le champ telephone au modele User"
sudo docker compose exec backend flask db upgrade

# En production
sudo docker compose -f docker-compose.prod.yml exec backend flask db migrate -m "Ajouter le champ telephone au modele User"
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
```

Exemple d'utilisation du champ dans le code applicatif :

```python
new_user = User(
    email=email,
    prenom=prenom,
    nom=nom,
    mdp=hashed_password,
    telephone=telephone,
)
```

#### Supprimer un champ d'un modele

1. Supprimez le champ du modele dans [backend/models.py](backend/models.py).
2. Generez puis appliquez une migration.

Exemple de modele apres suppression :

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

Commandes associees :

```bash
sudo docker compose exec backend flask db migrate -m "Supprimer le champ telephone du modele User"
sudo docker compose exec backend flask db upgrade
```

#### Commandes utiles

```bash
# Historique des migrations
sudo docker compose exec backend flask db history

# Version actuellement appliquee
sudo docker compose exec backend flask db current

# Revenir d'une migration
sudo docker compose exec backend flask db downgrade

# Revenir a l'etat initial
sudo docker compose exec backend flask db downgrade base

# Appliquer toutes les migrations en attente
sudo docker compose exec backend flask db upgrade

# Creer une migration vide a completer a la main
sudo docker compose exec backend flask db revision -m "Migration manuelle"
```

#### Bonnes pratiques

- Creez toujours une migration avant de modifier la base manuellement.
- Verifiez le contenu du fichier genere dans `backend/migrations/versions/` avant de l'appliquer.
- Testez d'abord les migrations en developpement.
- Sauvegardez la base avant toute migration en production.
- Conservez des messages de migration explicites et courts.

## Production

Cette section couvre la preparation d'un serveur Linux, la configuration des secrets, le deploiement Docker et l'automatisation CI/CD.

### Prerequis de deploiement

Preparez les elements suivants :

- Une machine Linux, idealement Ubuntu ou Debian
- Un acces SSH avec droits `sudo`
- Un nom de domaine si vous activez HTTPS
- Les identifiants DocuSign si l'integration est utilisee

### Preparation du serveur

#### Mettre a jour le systeme

```bash
sudo apt update && sudo apt upgrade -y
```

#### Installer Docker

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

#### Verifier Docker

```bash
sudo systemctl start docker
sudo systemctl status docker
```

### Secrets de production

#### Creer le dossier `.env_prod_secrets`

Ce dossier contient les secrets utilises par la stack de production.

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
# Copiez aussi votre cle privee DocuSign private.pem dans ce dossier

cd ..
chmod 600 .env_prod_secrets/*
```

> **Important** : remplacez toutes les valeurs d'exemple par vos vrais identifiants et ne versionnez jamais ces fichiers.

### Configuration applicative

#### Variables du backend

Mettez a jour [docker-compose.prod.yml](docker-compose.prod.yml) avec les valeurs adaptees a votre environnement :

```yaml
backend:
  environment:
    - DOCUSIGN_SERVER_IP=http://your-docusign-ip
    - FRONTEND_URL=https://your-domain.tld
    - REACT_APP_BACKEND_URL=https://your-domain.tld/api
```

#### Configuration Nginx

Mettez a jour [frontend/nginx.conf](frontend/nginx.conf) et [proxy/nginx.conf](proxy/nginx.conf) avec votre domaine reel :

```nginx
server_name your-domain.tld;
```

#### Configurer le pare-feu

```bash
# Politique par defaut
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH d'administration
sudo ufw allow from YOUR_ADMIN_IP to any port 22 proto tcp

# HTTP et HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Limiter les tentatives SSH
sudo ufw limit 22/tcp

# Si vous filtrez aussi les sorties, autorisez explicitement les flux necessaires
# sudo ufw default deny outgoing
# sudo ufw allow out 53
# sudo ufw allow out 80/tcp
# sudo ufw allow out 443/tcp
# sudo ufw allow out to BACKUP_SERVER_IP port 22 proto tcp

sudo ufw enable
sudo ufw status verbose
```

> **Note** : remplacez `YOUR_ADMIN_IP` et `BACKUP_SERVER_IP` par les adresses reelles.

### Deployer l'application

#### Construire, lancer et migrer

```bash
sudo docker compose -f docker-compose.prod.yml build
sudo docker compose -f docker-compose.prod.yml up -d
sudo docker compose -f docker-compose.prod.yml exec backend flask db upgrade
sudo docker compose -f docker-compose.prod.yml exec backend python init_db.py
```

#### Verifier l'etat de la stack

```bash
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs -f
```

#### Acces attendus

- Frontend : [http://your-domain.tld](http://your-domain.tld)
- API backend : [http://your-domain.tld/api](http://your-domain.tld/api)

### HTTPS avec Let's Encrypt

Cette procedure evite le demarrage en echec de Nginx avant l'obtention du vrai certificat, puis installe le certificat Let's Encrypt definitif.

#### Preparer la configuration

Mettez a jour [proxy/nginx.conf](proxy/nginx.conf) avec votre domaine reel :

```nginx
server_name your-domain.tld;
ssl_certificate /etc/letsencrypt/live/your-domain.tld/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.tld/privkey.pem;
```

#### Creer un certificat autosigne temporaire

```bash
sudo docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
  sh -c "apk add --no-cache openssl >/dev/null && \
         mkdir -p /etc/letsencrypt/live/your-domain.tld && \
         openssl req -x509 -nodes -newkey rsa:2048 -days 2 \
           -subj '/CN=your-domain.tld' \
           -keyout /etc/letsencrypt/live/your-domain.tld/privkey.pem \
           -out /etc/letsencrypt/live/your-domain.tld/fullchain.pem"
```

#### Demarrer les services

```bash
sudo docker compose -f docker-compose.prod.yml up -d --force-recreate proxy
sudo docker compose -f docker-compose.prod.yml up -d --build
sudo ss -ltnp | grep ':80'
```

#### Obtenir le certificat reel

Supprimez d'abord le certificat temporaire :

```bash
sudo docker compose -f docker-compose.prod.yml run --rm --entrypoint "" certbot \
  sh -c "rm -rf /etc/letsencrypt/live/your-domain.tld \
               /etc/letsencrypt/archive/your-domain.tld \
               /etc/letsencrypt/renewal/your-domain.tld.conf"
```

Puis lancez la generation du certificat Let's Encrypt :

```bash
sudo docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d your-domain.tld \
  --email admin@example.com \
  --agree-tos --no-eff-email
```

#### Recharger Nginx

```bash
sudo docker compose -f docker-compose.prod.yml exec -T proxy nginx -s reload
```

#### Configurer le renouvellement automatique

1. Ouvrez la crontab :

```bash
crontab -e
```

2. Ajoutez la tache de renouvellement suivante :

```bash
0 3 * * * cd /path/to/WebShop && docker compose -f docker-compose.prod.yml run --rm certbot renew --webroot -w /var/www/certbot && docker compose -f docker-compose.prod.yml exec -T proxy nginx -s reload >> /var/log/certbot-renew.log 2>&1
```

3. Verifiez la tache active :

```bash
crontab -l
```

4. Testez le renouvellement sans modifier les certificats reels :

```bash
sudo docker compose -f docker-compose.prod.yml run --rm certbot renew --webroot -w /var/www/certbot --dry-run
```

### CI/CD et deploiement automatique

Cette section couvre l'automatisation GitHub Actions pour tester puis deployer sur les environnements de developpement et de production.

#### Creer un utilisateur de deploiement dedie

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

#### Generer des cles SSH

```bash
# Cle de production
ssh-keygen -t ed25519 -C "ci-deploy-prod" -f ~/.ssh/webshop_deploy -N ""

# Cle de developpement, si serveur distinct
ssh-keygen -t ed25519 -C "ci-deploy-dev" -f ~/.ssh/webshop_deploy_dev -N ""
```

#### Installer les cles publiques sur le serveur

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

#### Ajouter les secrets GitHub

Dans le depot GitHub, ouvrez `Settings` > `Secrets and variables` > `Actions`, puis ajoutez :

Secrets de production :

- `SSH_HOST` : nom d'hote ou IP du VPS
- `SSH_USER` : `deploy`
- `SSH_KEY` : contenu complet de `~/.ssh/webshop_deploy`
- `WORK_DIR` : `/opt/webshop`
- `DEPLOY_GIT_TOKEN` : optionnel, pour depot prive

Secrets de developpement, si serveur distinct :

- `SSH_HOST_DEV` : hote du serveur de developpement
- `SSH_USER_DEV` : utilisateur de deploiement
- `SSH_KEY_DEV` : contenu complet de `~/.ssh/webshop_deploy_dev`
- `WORK_DIR_DEV` : chemin du projet sur le serveur de developpement

#### Comprendre les workflows

Le depot contient trois workflows GitHub Actions dans `.github/workflows/`.

Exemple de comportement pour le workflow principal CI :

- Declenchement sur `push` et `pull_request` vers `dev` et `main`
- Tests backend avec `pytest` et couverture
- Build frontend
- Deploiement automatique vers le staging depuis `dev`
- Deploiement automatique vers la production depuis `main`

Exemple de sequence de deploiement :

```bash
# 1. Travailler en local
git checkout dev
git commit -m "Add new feature"
git push origin dev

# 2. GitHub Actions lance les tests et deploie le staging

# 3. Verifier le staging
ssh deploy@dev-server "cd /opt/webshop && docker compose ps"

# 4. Fusionner vers main apres validation
git checkout main
git pull
git merge dev
git push origin main
```

#### Superviser les deploiements

```bash
# Consulter les executions dans l'onglet Actions du depot GitHub

# Suivre les logs en temps reel sur le serveur
ssh deploy@your-vps "cd /opt/webshop && docker compose logs -f backend"

# Verifier l'etat des services
ssh deploy@your-vps "cd /opt/webshop && docker compose ps"
```

#### Renforcer l'acces SSH

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

Redemarrez ensuite le service SSH :

```bash
sudo systemctl restart ssh
```

Si vous devez conserver un acces root par cle :

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

#### Depannage CI/CD

Probleme : acces refuse avec `Permission denied`

```bash
cat /home/deploy/.ssh/authorized_keys | head -1
ls -la /home/deploy/.ssh/
```

Probleme : les services ne se relancent pas apres deploiement

```bash
cd /opt/webshop && docker compose logs --tail=50
cd /opt/webshop && docker compose up -d
```

Probleme : les migrations echouent

```bash
cd /opt/webshop && docker compose exec -T db pg_isready -U dev_user
cd /opt/webshop && docker compose exec -T backend flask db current
```

> **Important** : conservez vos cles privees SSH dans un emplacement sur. Si plusieurs administrateurs interviennent, attribuez une cle distincte a chacun.

## Maintenance

Cette section regroupe les operations de sauvegarde, les procedures de depannage et les commandes de suivi en exploitation.

### Sauvegarde et restauration

Le projet utilise un service Docker `backup` base sur l'image officielle `restic/restic`. Les sauvegardes sont chiffrees cote client puis envoyees vers un depot distant.

#### Preparer le serveur de sauvegarde (seulement pour SFTP)

1. Creez un utilisateur dedie sur le serveur de sauvegarde :

```bash
sudo adduser --disabled-login --gecos "Restic Backup User" backup_user
sudo chsh -s /usr/sbin/nologin backup_user
```

2. Creez le dossier de stockage :

```bash
sudo mkdir -p /path/to/backup/webshop
sudo chown backup_user:backup_user /path/to/backup/webshop
sudo chmod 700 /path/to/backup/webshop
```

3. Generez une paire de cles SSH depuis le serveur applicatif :

```bash
ssh-keygen -t ed25519 -f ~/.ssh/restic_backup -C "restic backup key"
ssh-copy-id -i ~/.ssh/restic_backup.pub backup_user@backup.example.com
ssh -i ~/.ssh/restic_backup backup_user@backup.example.com ls /srv/restic/webshop
```

4. Copiez la cle privee `~/.ssh/restic_backup` dans `.env_prod_secrets`.

> **Important** : ne mettez pas de mot de passe sur cette cle si elle est utilisee de facon automatisee.

#### Ajouter les secrets Restic

```bash
echo "votre_mot_de_passe_restic_tres_fort" > .env_prod_secrets/RESTIC_PASSWORD.txt
chmod 600 .env_prod_secrets/RESTIC_PASSWORD.txt

echo "sftp:backup_user@backup.example.com:/srv/restic/webshop" > .env_prod_secrets/RESTIC_REPOSITORY.txt
chmod 600 .env_prod_secrets/RESTIC_REPOSITORY.txt
```

> **Note** : Pour les services demandant un utilisateur et un mot de passe, changer `RESTIC_PASSWORD` par le mot de passe de ce service et `RESTIC_REPOSITORY` par l'URL de connexion correspondante (ex: `webdav://pcloud_user@ewebdav.pcloud.com` pour pCloud).

Autres exemples de depot :

```bash
# Exemple pCloud
echo "webdav://ewebdav.pcloud.com/restic/backup/" > .env_prod_secrets/RESTIC_REPOSITORY.txt
chmod 600 .env_prod_secrets/RESTIC_REPOSITORY.txt

# Exemple S3 compatible AWS ou MinIO
echo "s3:s3.amazonaws.com/my-restic-bucket/webshop" > .env_prod_secrets/RESTIC_REPOSITORY.txt
chmod 600 .env_prod_secrets/RESTIC_REPOSITORY.txt

# Exemple Backblaze B2
echo "b2:my-bucket:webshop" > .env_prod_secrets/RESTIC_REPOSITORY.txt
chmod 600 .env_prod_secrets/RESTIC_REPOSITORY.txt
```

#### Configurer Docker Compose pour le profil backup

Dans [docker-compose.prod.yml](docker-compose.prod.yml), le service `backup` doit au minimum ressembler a ceci :

```yaml
backup:
  image: restic/restic:latest
  depends_on:
    - db
  environment:
    - RESTIC_REPOSITORY=$(cat /run/secrets/RESTIC_REPOSITORY)
    - RESTIC_PASSWORD_FILE=/run/secrets/RESTIC_PASSWORD
    - RESTIC_HOSTNAME=webshop-prod # Pour SFTP, sinon peut etre ignore
    - POSTGRES_DB=users_db
    - POSTGRES_USER_FILE=/run/secrets/DB_USER
    - POSTGRES_PASSWORD_FILE=/run/secrets/DB_PASSWORD
  secrets:
    - RESTIC_PASSWORD
    - RESTIC_REPOSITORY
    - RESTIC_SSH_KEY # Si vous utilisez une cle SSH pour SFTP
    - DB_USER
    - DB_PASSWORD
  volumes:
    - postgres_data:/var/lib/postgresql/data:ro
    - ./backup:/backup
  entrypoint: ["/backup/backup.sh"]
  profiles:
    - backup
```

Et dans la section `secrets` :

```yaml
RESTIC_PASSWORD:
  file: ./.env_prod_secrets/RESTIC_PASSWORD.txt
RESTIC_REPOSITORY:
  file: ./.env_prod_secrets/RESTIC_REPOSITORY.txt
RESTIC_SSH_KEY:
  file: ./.env_prod_secrets/restic_backup # Seulement pour SFTP
```

#### Initialiser le depot Restic

```bash
docker compose -f docker-compose.prod.yml --profile backup run --rm backup restic init
```

#### Automatiser les sauvegardes

1. Ouvrez la crontab de l'utilisateur qui execute Docker :

```bash
crontab -e
```

2. Ajoutez la tache quotidienne :

```bash
0 0 * * * export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && \
cd /opt/webshop/project && \
echo "[$(date '+\%Y-\%m-\%d \%H:\%M:\%S')] Debut du backup..." >> /var/log/webshop-backup.log 2>&1 && \
docker compose -f docker-compose.prod.yml --profile backup run --rm backup >> /var/log/webshop-backup.log 2>&1 && \
echo "[$(date '+\%Y-\%m-\%d \%H:\%M:\%S')] Backup termine." >> /var/log/webshop-backup.log 2>&1
```

3. Verifiez la crontab active :

```bash
crontab -l
```

#### Securiser le serveur de sauvegarde (seulement pour SFTP)

Sur le serveur de sauvegarde distant, n'autorisez SSH que depuis l'IP du serveur applicatif :

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from WEBSHOP_SERVER_IP to any port 22 proto tcp
sudo ufw enable
sudo ufw status verbose
```

#### Executer un backup manuel

```bash
docker compose -f docker-compose.prod.yml --profile backup run --rm backup
```

#### Restaurer depuis une sauvegarde

1. Lister les snapshots :

```bash
docker compose -f docker-compose.prod.yml --profile backup run --rm backup restic snapshots
```

2. Restaurer le dernier snapshot vers un dossier temporaire :

```bash
docker compose -f docker-compose.prod.yml --profile backup run --rm backup restic restore latest --target /path/to/restore
```

Pour plus de contexte sur le service de sauvegarde, consultez aussi [backup/README.md](backup/README.md).

### Depannage

Cette section regroupe les incidents les plus frequents et une reponse rapide associee.

#### Le backend redemarre en boucle

Cause probable : le schema de la base de donnees ne correspond plus aux modeles.

```bash
sudo docker compose exec backend flask db upgrade
```

#### La migration automatique echoue

Cause probable : Flask-Migrate ne detecte pas tous les changements complexes.

```bash
sudo docker compose exec backend flask db revision -m "Migration manuelle"
sudo docker compose exec backend flask db upgrade
```

#### Les volumes Docker occupent trop d'espace

```bash
sudo docker volume ls
sudo docker volume prune
sudo du -sh /var/lib/docker/volumes/*/
```

#### Reinitialiser completement l'application

> **Attention** : cette operation supprime les donnees de la base et les volumes associes. Verifiez d'abord que vous disposez d'une sauvegarde exploitable.

```bash
sudo docker compose down -v
sudo docker compose build
sudo docker compose up -d
sudo docker compose exec backend flask db init
sudo docker compose exec backend flask db migrate -m "Initial migration"
sudo docker compose exec backend flask db upgrade
```

### Logs et monitoring

Ces commandes permettent de verifier rapidement l'etat de la plateforme et d'analyser les evenements de securite.

#### Consulter les logs applicatifs

```bash
# Logs en developpement
sudo docker compose logs -f frontend
sudo docker compose logs -f backend

# Logs en production
sudo docker compose -f docker-compose.prod.yml logs -f backend
```

#### Suivre le journal de securite

```bash
# Lire le journal de securite dans le conteneur backend
sudo docker compose -f docker-compose.prod.yml exec backend tail -f security.log

# Affichage brut des logs backend
sudo docker compose -f docker-compose.prod.yml logs -f backend

# Filtrer certaines actions avec jq
sudo docker compose -f docker-compose.prod.yml exec backend cat security.log | jq 'select(.action=="LOGIN_FAILED")'
sudo docker compose -f docker-compose.prod.yml exec backend cat security.log | jq 'select(.action=="USER_DELETED")'

# Rechercher les erreurs d'autorisation
sudo docker compose -f docker-compose.prod.yml exec backend grep "UNAUTHORIZED\|FORBIDDEN\|FAILED" security.log | jq '.'

# Copier le journal sur l'hote
sudo docker compose -f docker-compose.prod.yml cp backend:/app/security.log ./security.log
```

Evenements journalises les plus courants :

- Authentification : `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `REGISTER`
- Gestion des utilisateurs : `USER_CREATED`, `USER_UPDATED`, `USER_DELETED`
- Controle d'acces : `UNAUTHORIZED_ACCESS`, `FORBIDDEN_ACCESS`
- Configuration : `PARAMETERS_UPDATED`, `VAT_CREATED`, `VAT_DELETED`

Chaque entree contient typiquement un horodatage, un `user_id`, un `user_email`, une adresse IP, une action, une ressource et un statut.