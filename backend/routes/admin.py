from flask import Blueprint, request, jsonify, session
from flask_bcrypt import Bcrypt
from models import db, User, UserSchema
from functools import wraps
import logging
from utils import validate_user_fields

# Create a Blueprint for admin-related routes
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

bcrypt = Bcrypt()

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
@admin_bp.route("/all-user", methods=['GET'])
@admin_required
def get_all_users():
    users = User.query.all()
    user_schema = UserSchema(many=True)
    user_data = user_schema.dump(users)
    return jsonify(data=user_data)

# Add new user route
@admin_bp.route("/create-user", methods=["POST"])
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
@admin_bp.route("/update-user/<user_id>", methods=['POST'])
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
@admin_bp.route("/delete-user/<user_id>", methods=['POST'])
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
@admin_bp.route('/info-user/<user_id>', methods=['POST'])
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