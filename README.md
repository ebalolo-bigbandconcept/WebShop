# WebShop

Application WebShop contenant :

[![React](https://img.shields.io/badge/Frontend-React-blue?logo=react)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)](https://redis.io/)
[![DocuSign](https://img.shields.io/badge/DocuSign-eSign-orange?logo=docusign)](https://www.docusign.com/)

Application WebShop avec frontend React/Bootstrap, backend Flask, Redis pour cache, et intégration DocuSign.

---

## 1. Mise à jour du VPS

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

## 3. Initialisation de site

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

DOCUSIGN_ACCOUNT_ID=your_docusign_account_id
DOCUSIGN_USER_ID=your_docusign_user_id
DOCUSIGN_INTEGRATION_KEY=your_docusign_integration_id
DOCUSIGN_SERVER_IP=123.456.789.10
```

> Remplacer tous les `your_...` par vos identifiants.

### Build et lancement avec Docker

```bash
sudo docker compose build
sudo docker compose up
```

## 4. Accès à l'application

- Frontend : [http://localhost:3000](http://localhost:3000)
- Backend : [http://localhost:5000](http://localhost:5000)
