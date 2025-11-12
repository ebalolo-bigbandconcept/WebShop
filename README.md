# PythonWebApp

Application web basic fullstack

- Frontend : Flask
- Backend : Nodejs

## 1. Setup

Tout d'abord mettez a jour votre VPS :
``sudo apt update && apt upgrade -y``

## 2. Installation de docker

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

### 3. Initialisation de DocuSign eSign

Créer une application intégrée dans DocuSign (Integrator Key)

- Connectez-vous sur [DocuSign Developer](https://developers.docusign.com/).  
- Allez dans **My Apps & Keys** > **Add App and Integration Key**.  
- Nommez votre application
- Dans **Integration Type** cocher **Private custom integration**
- Dans **Authentication** cocher **Yes**
- Dans **Service Integration** générer une paire de clée RSA
  - Copier la clée publique dans un fichier public.pem
  - Copier la clée privée dans un fichier private.pem
- Dans **Additional settings** Ajoutez une **Redirect URI** : ``http://localhost:3000/consent-complete``
- Dans **Allowed HTTP Methods** cocher **POST**
- Enregistrer

### 4. Initialisation de site

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
REACT_APP_BACKEND_URL=http://localhost:5000

# Variables pour DocuSign trouvable sur docusign dans l'onglet Apps & Keys
DOCUSIGN_ACCOUNT_ID=your_docusign_account_id
DOCUSIGN_USER_ID=your_docusign_user_id
DOCUSIGN_INTEGRATION_KEY=your_docusign_integration_id
DOCUSIGN_BASE_PATH=https://demo.docusign.net/restapi
DOCUSIGN_AUTH_SERVER=https://account-d.docusign.com
DOCUSIGN_PRIVATE_KEY_PATH=/app/private.pem
```

Penser à bien remplacer les **'your_...'** par vos identifiants.

### 5. Démarrage du site web

Enfin on peut lancer le site web
``sudo docker compose up --build``
