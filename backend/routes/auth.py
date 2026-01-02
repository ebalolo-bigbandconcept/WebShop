from flask import Blueprint, request, jsonify, session
from flask_bcrypt import Bcrypt
from models import db, User, UserSchema
from utils import validate_user_fields
import logging

# Create a Blueprint for authentication-related routes
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/user')

bcrypt = Bcrypt()

# Get current user info
@auth_bp.route("/me", methods=['GET'])
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
@auth_bp.route("/register", methods=["POST"])
def register():
    email = request.json["email"]
    prenom = request.json["prenom"]
    nom = request.json["nom"]
    mdp = request.json["mdp"]
    
    # Vérification si le nom d'utilisateur existe déjà.
    user_already_exists = User.query.filter_by(email=email).first() is not None

    if user_already_exists:
        return jsonify({"error": "User already exists"}), 409
    
    error = validate_user_fields(email, prenom, nom, mdp, role=None)
    if error:
        return jsonify({"error": error}), 400
    
    # Création du nouvel utilisateur du mot de passe.
    hashed_password = bcrypt.generate_password_hash(mdp).decode('utf-8')
    new_user = User(
        email=email,
        prenom=prenom,
        nom=nom,
        mdp=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()
    logging.info(f"Nouvel utilisateur enregistré: {new_user.email} (id: {new_user.id})")
    
    # Connexion automatique après l'inscription
    session["user_id"] = new_user.id
    
    user_schema = UserSchema()
    return user_schema.jsonify(new_user)

# Login route
@auth_bp.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    mdp = request.json["mdp"]
    
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Email invalide"}), 401
    
    if not bcrypt.check_password_hash(user.mdp, mdp):
        return jsonify({"error": "Mot de passe invalide"}), 401
    
    session["user_id"] = user.id
    
    user_schema = UserSchema()
    return user_schema.jsonify(user)

# Logout route
@auth_bp.route("/logout", methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Successfully logged out."}), 200