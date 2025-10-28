from flask import Flask, request, jsonify, session, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
from flask_marshmallow import Marshmallow
from config import ApplicationConfig
from models import db, ma, User, UserSchema, Clients, ClientsSchema, Devis, DevisSchema, Articles, ArticlesSchema, DevisArticles, DevisArticlesSchema, TauxTVA, TauxTVASchema
from dotenv import load_dotenv
from functools import wraps
import os, re, logging

# CONSTANTS
load_dotenv()
ADMIN_MAIL = os.getenv('ADMIN_MAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Config App
app = Flask(__name__)
app.config.from_object(ApplicationConfig)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
bcrypt = Bcrypt(app)
server_session = Session(app)

# Config logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler("app.log"),logging.StreamHandler()]
)

# Config BDD
db.init_app(app)
ma.init_app(app)

with app.app_context():
    db.create_all()
    # Créer le 1er admin si la table users est vide.
    table_empty_user = User.query.filter_by(email=ADMIN_MAIL).first() is None

    if table_empty_user:
        hashed_admin_password = bcrypt.generate_password_hash(ADMIN_PASSWORD)
        admin_user = User(first_name='Admin',last_name='Admin',email=ADMIN_MAIL,password=hashed_admin_password,role='Administrateur')
        db.session.add(admin_user)
        db.session.commit()
    
    table_empty_tva = TauxTVA.query.first() is None
    if table_empty_tva:
        taux20 = TauxTVA(taux=0.20)
        db.session.add(taux20)
        db.session.commit()

### USEFULL FUNCTIONS ###

# Validate user fields for database entry
VALID_ROLES = {"Utilisateur", "Administrateur"}

def validate_user_fields(email, first_name, last_name, password=None, role=None):
    if not is_valid_email(email) or len(email) > 345:
        return "Format d'email invalide ou trop long."
    if len(first_name) < 1 or len(first_name) > 50:
        return "Le prénom doit contenir entre 1 et 50 caractères."
    if len(last_name) < 1 or len(last_name) > 50:
        return "Le nom doit contenir entre 1 et 50 caractères."
    if role and role not in VALID_ROLES:
        return "Rôle invalide."
    if password is not None:
        if not is_strong_password(password):
            return "Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial."
    return None

def validate_client_fields(nom, prenom, rue, ville, code_postal, telephone, email):
    if not is_valid_email(email) or len(email) > 345:
        return "Format d'email invalide ou trop long."
    if len(nom) < 1 or len(nom) > 100:
        return "Le nom doit contenir entre 1 et 100 caractères."
    if len(prenom) < 1 or len(prenom) > 100:
        return "Le prénom doit contenir entre 1 et 100 caractères."
    if len(rue) < 1 or len(rue) > 200:
        return "La rue doit contenir entre 1 et 200 caractères."
    if len(ville) < 1 or len(ville) > 100:
        return "La ville doit contenir entre 1 et 100 caractères."
    if len(code_postal) < 1 or len(code_postal) > 20:
        return "Le code postal doit contenir entre 1 et 20 caractères."
    if len(telephone) < 1 or len(telephone) > 20:
        return "Le téléphone doit contenir entre 1 et 20 caractères."
    return None

def validate_article_fields(nom, description, prix_achat_HT, prix_vente_HT, taux_tva_id):
    if len(nom) < 1 or len(nom) > 200:
        return "Le nom de l'article doit contenir entre 1 et 200 caractères."
    if len(description) < 1:
        return "La description de l'article ne peut pas être vide."
    if float(prix_achat_HT) < 0:
        return "Le prix d'achat HT ne peut pas être négatif."
    if float(prix_vente_HT) < 0:
        return "Le prix de vente HT ne peut pas être négatif."
    taux_tva = TauxTVA.query.filter_by(id=taux_tva_id).first()
    if not taux_tva:
        return "Le taux de TVA spécifié n'existe pas."
    return None

# Email validation function
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

# Password strength validation function
def is_strong_password(password):
    # Au moins 8 caractères, une majuscule, une minuscule, un chiffre, un caractère spécial
    regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
    return re.match(regex, password)
        
### ADMIN ROUTES ###
# Admin role required decorator           
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        user = User.query.filter_by(id=user_id).first()
        if user.role != 'Administrateur':
            return jsonify({"error": "Forbidden"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Get all users info route
@app.route("/@all", methods=['GET'])
@admin_required
def get_all_users():
    users = User.query.all()
    user_schema = UserSchema(many=True)
    user_data = user_schema.dump(users)
    return jsonify(data=user_data)

# Add new user route
@app.route("/add-user", methods=["POST"])
@admin_required
def add_user():
    email = request.json["email"]
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    password = request.json["password"]
    role = request.json["role"]
    
    # Vérification si le nom d'utilisateur existe déjà.
    user_already_exists = User.query.filter_by(email=email).first() is not None

    if user_already_exists:
        return jsonify({"error": "Cette addresse email est déjà utilisée."}), 409
    
    error = validate_user_fields(email, first_name, last_name, password, role)
    if error:
        return jsonify({"error": error}), 400
    
    # Création du nouvel utilisateur du mot de passe.
    hashed_password = bcrypt.generate_password_hash(password)
    new_user = User(email=email,first_name=first_name,last_name=last_name,password=hashed_password,role=role)
    db.session.add(new_user)
    db.session.commit()
    logging.info(f"Admin {session.get('user_id')} a créé un nouvel utilisateur: {new_user.email} (id: {new_user.id}, rôle: {new_user.role})")
    
    return jsonify({
        "id": new_user.id
    })

# Modify user route
@app.route("/modify-user/<user_id>", methods=['POST'])
@admin_required
def modify_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    new_email = request.json["email"]
    new_first_name = request.json["first_name"]
    new_last_name = request.json["last_name"]
    new_password = request.json.get("password")
    new_role = request.json["role"]
    
    # Empêcher la modification du rôle du dernier admin
    if user.role == "Administrateur":
        admin_count = User.query.filter_by(role="Administrateur").count()
        if admin_count <= 1 and new_role != "Administrateur":
            return jsonify({"error": "Impossible de modifier le rôle du dernier compte administrateur."}), 403

    # Empêcher la modification de son propre rôle admin
    if user.role == "Administrateur":
        current_user_id = session.get("user_id")
        if user.id == current_user_id and new_role != "Administrateur":
            return jsonify({"error": "Impossible de modifier votre propre rôle administrateur."}), 403
    
    if new_email != user.email: 
        email_already_exists = User.query.filter_by(email=new_email).first() is not None
        if email_already_exists:
            return jsonify({"error": "Cette addresse email est déjà utilisée."}), 409
        
    error = validate_user_fields(new_email, new_first_name, new_last_name, new_password, new_role)
    if error:
        return jsonify({"error": error}), 400
    
    user.email = new_email
    user.first_name = new_first_name
    user.last_name = new_last_name
    user.role = new_role
    
    if new_password:
        new_hashed_password = bcrypt.generate_password_hash(new_password)
        user.password = new_hashed_password
    
    db.session.commit()
    logging.info(f"Admin {session.get('user_id')} a modifié l'utilisateur: {user.email} (id: {user.id}, rôle: {user.role})")
    
    return jsonify({
        "id": user.id
    })
    
# Delete user route
@app.route("/delete-user/<user_id>", methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Empêcher la suppression de son propre compte admin
    current_user_id = session.get("user_id")
    if user.id == current_user_id:
        return jsonify({"error": "Vous ne pouvez pas supprimer votre propre compte admin."}), 403

    # Empêcher la suppression du dernier admin
    if user.role == "Administrateur":
        admin_count = User.query.filter_by(role="Administrateur").count()
        if admin_count <= 1:
            return jsonify({"error": "Impossible de supprimer le dernier compte administrateur."}), 403
    user_email = user.email
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    logging.info(f"Admin {session.get('user_id')} a supprimé l'utilisateur: {user_email} (id: {user_id})")
    
    return jsonify({
        "200": "User successfully deleted."
    })

# Get user info route
@app.route('/user-info/<user_id>', methods=['POST'])
@admin_required
def get_user_info(user_id):
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role
    })

### User routes ###

# Get current user info
@app.route("/@me", methods=['GET'])
def get_current_user():
    user_id = session.get("user_id")
    
    if not user_id:
        return jsonify({"user": None}), 401
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"user": None}), 401
    
    user_schema = UserSchema()
    return user_schema.jsonify(user)

# Register route
@app.route("/register", methods=["POST"])
def register():
    email = request.json["email"]
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    password = request.json["password"]
    
    # Vérification si le nom d'utilisateur existe déjà.
    user_already_exists = User.query.filter_by(email=email).first() is not None

    if user_already_exists:
        return jsonify({"error": "User already exists"}), 409
    
    error = validate_user_fields(email, first_name, last_name, password, role=None)
    if error:
        return jsonify({"error": error}), 400
    
    # Création du nouvel utilisateur du mot de passe.
    hashed_password = bcrypt.generate_password_hash(password)
    new_user = User(email=email,first_name=first_name,last_name=last_name,password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    logging.info(f"Nouvel utilisateur enregistré: {new_user.email} (id: {new_user.id})")
    
    # Connexion automatique après l'inscription
    session["user_id"] = new_user.id
    
    user_schema = UserSchema()
    return user_schema.jsonify(new_user)

# Login route
@app.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]
    
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Email invalide"}), 401
    
    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Mot de passe invalide"}), 401
    
    session["user_id"] = user.id
    
    user_schema = UserSchema()
    return user_schema.jsonify(user)

# Logout route
@app.route("/logout", methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Successfully logged out."}), 200

### Clients routes ###

# Get all clients info route
@app.route("/@all-clients", methods=['GET'])
def get_all_clients():
    tableEmpty = Clients.query.first() is None
    if tableEmpty:
        return jsonify({"error": "Aucun clients trouvé"}), 404
    
    clients = Clients.query.all()
    clients_schema = ClientsSchema(many=True)
    clients_data = clients_schema.dump(clients)
    return jsonify(data=clients_data)

# Add new client route
@app.route("/add-client", methods=["POST"])
def add_client():
    nom = request.json["last_name"]
    prenom = request.json["first_name"]
    rue = request.json["street"]
    ville = request.json["city"]
    code_postal = request.json["postal_code"]
    telephone = request.json["phone"]
    email = request.json["email"]
    
    # Vérification si le client existe déjà.
    client_already_exists = Clients.query.filter_by(email=email).first() is not None

    if client_already_exists:
        return jsonify({"error": "Cette addresse email est déjà utilisée."}), 409
    
    error = validate_client_fields(nom, prenom, rue, ville, code_postal, telephone, email)
    if error:
        return jsonify({"error": error}), 400
    
    new_client = Clients(nom=nom,prenom=prenom,rue=rue,ville=ville,code_postal=code_postal,telephone=telephone,email=email)
    db.session.add(new_client)
    db.session.commit()
    logging.info(f"Nouvel client ajouté: {new_client.email} (id: {new_client.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": new_client.id
    })

# Get client info route
@app.route('/client-info/<client_id>', methods=['GET'])
def get_client_info(client_id):
    client = Clients.query.filter_by(id=client_id).first()
    return jsonify({
        "id": client.id,
        "first_name": client.prenom,
        "last_name": client.nom,
        "street": client.rue,
        "city": client.ville,
        "postal_code": client.code_postal,
        "phone": client.telephone,
        "email": client.email
    })

### Devis routes ###

# Get every devis of a client route
@app.route('/@client-devis/<client_id>', methods=['GET'])
def get_client_devis(client_id):
    tableEmpty = Devis.query.filter_by(client_id=client_id).first() is None
    if tableEmpty:
        return jsonify({"error": "Aucuns devis trouvé"}), 404
    
    devis = Devis.query.filter_by(client_id=client_id).all()
    devis_schema = DevisSchema(many=True)
    devis_data = devis_schema.dump(devis)
    return jsonify(data=devis_data)

# Get specific devis info route
@app.route('/devis-info/<devis_id>', methods=['GET'])
def get_devis_info(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404
    
    devis_schema = DevisSchema()
    return devis_schema.jsonify(devis)

# Get new devis id route
@app.route('/new-devis-id', methods=['GET'])
def get_new_devis_id():
    new_devis_id = Devis.query.order_by(Devis.id.desc()).first()
    if new_devis_id is None:
        return jsonify({
            "id": 1
        })
        
    return jsonify({
        "id": new_devis_id.id + 1
    })

# Create new devis route
@app.route('/create-devis', methods=['POST'])
def create_devis():
    client_id = request.json["client_id"]
    tauxTVA_id = request.json["tauxTVA_id"]
    titre = request.json["title"]
    description = request.json["description"]
    date = request.json["date"]
    montant_HT = request.json["montant_HT"]
    montant_TVA = request.json["montant_TVA"]
    montant_TTC = request.json["montant_TTC"]
    statut = request.json["statut"]
    
    new_devis = Devis(client_id=client_id,tauxTVA_id=tauxTVA_id,titre=titre,description=description,date=date,montant_HT=montant_HT,montant_TVA=montant_TVA,montant_TTC=montant_TTC,statut=statut)
    db.session.add(new_devis)
    db.session.commit()
    logging.info(f"Nouveau devis créé: {new_devis.titre} (id: {new_devis.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": new_devis.id
    })

# Update devis route
@app.route('/update-devis/<devis_id>', methods=['POST'])
def update_devis(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404
    
    devis.tauxTVA_id = request.json["tauxTVA_id"]
    devis.titre = request.json["title"]
    devis.description = request.json["description"]
    devis.date = request.json["date"]
    devis.montant_HT = request.json["montant_HT"]
    devis.montant_TVA = request.json["montant_TVA"]
    devis.montant_TTC = request.json["montant_TTC"]
    devis.statut = request.json["statut"]
    
    db.session.commit()
    logging.info(f"Devis modifié: {devis.titre} (id: {devis.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": devis.id
    })

### Articles routes ###
# Get all articles info route
@app.route("/@all-articles", methods=['GET'])
@admin_required
def get_all_articles():
    tableEmpty = Articles.query.first() is None
    if tableEmpty:
        return jsonify({"error": "Aucuns articles trouvé"}), 404
    
    articles = Articles.query.all()
    articles_schema = ArticlesSchema(many=True)
    articles_data = articles_schema.dump(articles)
    return jsonify(data=articles_data)

# Get specific article info route
@app.route('/article-info/<article_id>', methods=['GET'])
@admin_required
def get_article_info(article_id):
    article = Articles.query.filter_by(id=article_id).first()
    if not article:
        return jsonify({"error": "Article non trouvé"}), 404
    
    article_schema = ArticlesSchema()
    return article_schema.jsonify(article)

# Add new article route
@app.route("/add-article", methods=["POST"])
@admin_required
def add_article():
    nom = request.json["nom"]
    description = request.json["description"]
    prix_achat_HT = request.json["prix_achat_HT"]
    prix_vente_HT = request.json["prix_vente_HT"]
    taux_tva = request.json["taux_tva"]
    
    if not taux_tva:
        return jsonify({"error": "Le taux de TVA est requis."}), 400
        
    taux_tva_id = TauxTVA.query.filter_by(taux=taux_tva).first().id
    
    
    error = validate_article_fields(nom, description, prix_achat_HT, prix_vente_HT, taux_tva_id)
    if error:
        return jsonify({"error": error}), 400
    
    new_article = Articles(nom=nom,description=description,prix_achat_HT=prix_achat_HT,prix_vente_HT=prix_vente_HT,taux_tva_id=taux_tva_id)
    db.session.add(new_article)
    db.session.commit()
    logging.info(f"Nouvel article ajouté: {new_article.nom} (id: {new_article.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": new_article.id
    })

# Modify article route
@app.route("/modify-article/<article_id>", methods=['POST'])
@admin_required
def modify_article(article_id):
    article = Articles.query.filter_by(id=article_id).first()
    if not article:
        return jsonify({"error": "Article non trouvé"}), 404
    
    new_nom = request.json["nom"]
    new_description = request.json["description"]
    new_prix_achat_HT = request.json["prix_achat_HT"]
    new_prix_vente_HT = request.json["prix_vente_HT"]
    new_taux_tva = request.json["taux_tva"]
    
    if not new_taux_tva:
        return jsonify({"error": "Le taux de TVA est requis."}), 400
        
    new_taux_tva_id = TauxTVA.query.filter_by(taux=new_taux_tva).first().id
    
    error = validate_article_fields(new_nom, new_description, new_prix_achat_HT, new_prix_vente_HT, new_taux_tva_id)
    if error:
        return jsonify({"error": error}), 400
    
    article.nom = new_nom
    article.description = new_description
    article.prix_achat_HT = new_prix_achat_HT
    article.prix_vente_HT = new_prix_vente_HT
    article.taux_tva_id = new_taux_tva_id
    
    db.session.commit()
    logging.info(f"Article modifié: {article.nom} (id: {article.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": article.id
    })

# Delete article route
@app.route("/delete-article/<article_id>", methods=['POST'])
@admin_required
def delete_article(article_id):
    article = Articles.query.filter_by(id=article_id).first()
    if not article:
        return jsonify({"error": "Article non trouvé"}), 404
    
    article_name = article.nom
    Articles.query.filter_by(id=article_id).delete()
    db.session.commit()
    logging.info(f"Article supprimé: {article_name} (id: {article_id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "200": "Article successfully deleted."
    })

### Main ###

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)