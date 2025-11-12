# WebShop

Application WebShop contenant :

[![React](https://img.shields.io/badge/Frontend-React-blue?logo=react)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)](https://redis.io/)
[![DocuSign](https://img.shields.io/badge/DocuSign-eSign-orange?logo=docusign)](https://www.docusign.com/)

Application WebShop avec frontend React/Bootstrap, backend Flask, Redis pour cache, et intégration DocuSign.

---

## 1. Mise à jour de VPS

```bash
sudo apt update && sudo apt upgrade -y
```

## 2. Installation de docker

### Ajouter le repo Docker

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

### Installer Docker

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo systemctl status docker  # Vérifier le statut
sudo systemctl start docker   # Démarrer si nécessaire
sudo docker run hello-world   # Test rapide
```

## 3. Initialisation DocuSign eSign

1. Créez une application intégrée sur [DocuSign Developer](https://developers.docusign.com/).  
2. Allez dans **My Apps & Keys** -> **Add App and Integration Key**.  
3. Donnez un nom à votre application.
4. Choisissez **Private custom integration**.
5. Dans **Is your application able to securely store a client secret?** cocher **Yes**.
6. Dans **Service Integration**, générez une paire de clés RSA :
   - Copiez la clé publique dans `public.pem`
   - Copiez la clé privée dans `private.pem`
   - Ajoutez le fichier `private.pem` dans `backend/`
7. Dans **Additional settings**, ajoutez une **Redirect URI** :

   ``` bash
   http://localhost:3000/consent-complete
   ```

8. Autorisez la méthode HTTP **POST**.
9. Enregistrez votre application.

## 4. Initialisation de site

### Générer une clé secrète

```bash
openssl rand -base64 32
```

Exemple de clé générée :

```bash
0rnd5wsmCJYz9wucw4OCl3uOP3FxbRC+nV6pptA07KE=
```

### Créez le fichier `.env` à la racine du site

```bash
SECRET_KEY=your_key
ADMIN_MAIL=your_admin_mail
ADMIN_PASSWORD=your_admin_password
REACT_APP_BACKEND_URL=http://localhost:5000

# Variables pour DocuSign trouvable sur docusign dans l'onglet Apps & Keys
DOCUSIGN_ACCOUNT_ID=your_docusign_account_id
DOCUSIGN_USER_ID=your_docusign_user_id
DOCUSIGN_INTEGRATION_KEY=your_docusign_integration_id
DOCUSIGN_BASE_PATH=https://demo.docusign.net/restapi
DOCUSIGN_AUTH_SERVER=https://account-d.docusign.com
DOCUSIGN_PRIVATE_KEY_PATH=/app/private.pem
```

> Remplacer tous les `your_...` par vos identifiants.

### Build et lancement avec Docker

```bash
sudo docker compose build
sudo docker compose up
```

## 5. Consentement DocuSign

Pour finaliser l’intégration DocuSign, vous devez accepter le consentement OAuth :

1. Remplacez {your_integration_id} par l’ID d’intégration DocuSign que vous avez créé dans l'URl suivante.

   ``` bash
   https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature%20impersonation&client_id={your_integration_id}&redirect_uri=http://localhost:3000/consent-complete).
   ```

2. Ouvrez cette URL dans votre navigateur et suivez les instructions pour accepter le consentement.
   > Le consentement DocuSign n'est à faire **qu'une seule fois** pour initialiser l'accès via votre compte.

## 6. Accès à l'application

- Frontend : [http://localhost:3000](http://localhost:3000)
- Backend : [http://localhost:5000](http://localhost:5000)
