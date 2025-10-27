# PythonWebApp

Application web basic fullstack

- Frontend : Flask
- Backend : Nodejs

## Setup

Tout d'abord mettez a jour votre VPS :
``sudo apt update && apt upgrade -y``

### Installation de docker

Tout d'abord il faut installer le repo apt de Docker

``` bash
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

Ensuite on peut l'installer
``sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y``

Une fois installer vérifions si docker fonctionne correctement
``sudo systemctl status docker``

Si ce n'est pas le cas faites
``sudo systemctl start docker``

Enfin pour voir si tout fonctionne bien faites
``sudo docker run hello-world``

### Initialisation de site

Tout d'abord allez à la racine du dossier du site.

Vous aurez besoin d'une clée secrète pour faire fonctionné l'application.
Pour la générer faite dans votre terminal linux :
``openssl rand -base64 32``

Copier ensuite cette la clée qui devrais resemblé à quelque chose comme ça :
``0rnd5wsmCJYz9wucw4OCl3uOP3FxbRC+nV6pptA07KE=``

Créer ensuite un fichier .env à la racine du dossier du site et créer les variable d'environement suivantes :

``` bash
SECRET_KEY=your_key
ADMIN_MAIL=your_admin_mail
ADMIN_PASSWORD=your_admin_password
REACT_APP_BACKEND_URL=http:127.0.0.1
```

Remplacer les 'your_...' par vos identifiant et votre clée secrète.

Ensuite il faut initialiser l'application
``sudo docker compose build``

Enfin on peut lance le site web
``sudo docker compose up``
