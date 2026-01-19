from flask import Blueprint, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, User, UserSchema
from utils import validate_user_fields, validated_json
import logging

# Get loggers
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')

# Create a Blueprint for authentication-related routes
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/user')

bcrypt = Bcrypt()

# Initialize rate limiter (storage configured in app.py)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

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
@limiter.limit("5/minute")
@validated_json("email", "prenom", "nom", "mdp")
def register():
    data = request.get_json()
    email = data.get("email", "").strip()
    prenom = data.get("prenom", "").strip()
    nom = data.get("nom", "").strip()
    mdp = data.get("mdp", "")
    
    ip_address = request.remote_addr
    
    # Vérification si le nom d'utilisateur existe déjà.
    user_already_exists = User.query.filter_by(email=email).first() is not None

    if user_already_exists:
        security_logger.warning(
            f"Registration attempt for existing email: {email}",
            extra={
                'action': 'REGISTRATION_FAILED',
                'user_email': email,
                'ip_address': ip_address,
                'status': 'DUPLICATE_EMAIL'
            }
        )
        return jsonify({"error": "User already exists"}), 409
    
    error = validate_user_fields(email, prenom, nom, mdp, role=None)
    if error:
        security_logger.warning(
            f"Registration validation failed: {error}",
            extra={
                'action': 'REGISTRATION_FAILED',
                'user_email': email,
                'ip_address': ip_address,
                'status': 'VALIDATION_ERROR'
            }
        )
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
    
    security_logger.info(
        f"New user registered: {new_user.email}",
        extra={
            'action': 'REGISTRATION_SUCCESS',
            'user_id': new_user.id,
            'user_email': new_user.email,
            'ip_address': ip_address,
            'status': 'SUCCESS'
        }
    )
    
    # Connexion automatique après l'inscription
    session["user_id"] = new_user.id
    
    user_schema = UserSchema()
    return user_schema.jsonify(new_user)

# Login route
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5/minute")
@validated_json("email", "mdp")
def login_user():
    data = request.get_json()
    email = data.get("email", "").strip()
    mdp = data.get("mdp", "")
    ip_address = request.remote_addr
    
    user = User.query.filter_by(email=email).first()

    if user is None:
        security_logger.warning(
            f"Login attempt with non-existent email: {email}",
            extra={
                'action': 'LOGIN_FAILED',
                'user_email': email,
                'ip_address': ip_address,
                'status': 'INVALID_EMAIL'
            }
        )
        return jsonify({"error": "Email invalide"}), 401
    
    if not bcrypt.check_password_hash(user.mdp, mdp):
        security_logger.warning(
            f"Failed login attempt for user: {email}",
            extra={
                'action': 'LOGIN_FAILED',
                'user_id': user.id,
                'user_email': email,
                'ip_address': ip_address,
                'status': 'INVALID_PASSWORD'
            }
        )
        return jsonify({"error": "Mot de passe invalide"}), 401
    
    session["user_id"] = user.id
    
    security_logger.info(
        f"User logged in successfully: {user.email}",
        extra={
            'action': 'LOGIN_SUCCESS',
            'user_id': user.id,
            'user_email': user.email,
            'ip_address': ip_address,
            'status': 'SUCCESS'
        }
    )
    
    user_schema = UserSchema()
    return user_schema.jsonify(user)

# Logout route
@auth_bp.route("/logout", methods=['POST'])
def logout():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            security_logger.info(
                f"User logged out: {user.email}",
                extra={
                    'action': 'LOGOUT',
                    'user_id': user.id,
                    'user_email': user.email,
                    'ip_address': request.remote_addr,
                    'status': 'SUCCESS'
                }
            )
    
    session.pop('user_id', None)
    return jsonify({"message": "Successfully logged out."}), 200