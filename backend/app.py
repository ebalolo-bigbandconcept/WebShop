from flask import Flask, request, jsonify, session, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
from flask_marshmallow import Marshmallow
from config import ApplicationConfig
from models import db, ma, User, UserSchema
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
    table_empty = User.query.filter_by(email=ADMIN_MAIL).first() is None

    if table_empty:
        hashed_admin_password = bcrypt.generate_password_hash(ADMIN_PASSWORD)
        admin_user = User(first_name='Admin',last_name='Admin',email=ADMIN_MAIL,password=hashed_admin_password,role='Administrateur')
        db.session.add(admin_user)
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
    
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    logging.info(f"Admin {session.get('user_id')} a supprimé l'utilisateur: {user.email} (id: {user.id})")
    
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)