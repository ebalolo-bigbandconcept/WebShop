from flask import Blueprint, request, jsonify, session
from flask_bcrypt import Bcrypt
from models import db, User, UserSchema, Parameters, TauxTVA, Articles, DevisArticles
from functools import wraps
import logging
from utils import validate_user_fields, _coerce_float, _coerce_int

# Create a Blueprint for admin-related routes
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/api/admin')

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
    prenom = request.json["prenom"]
    nom = request.json["nom"]
    mdp = request.json["mdp"]
    role = request.json["role"]
    
    # Vérification si le nom d'utilisateur existe déjà.
    user_already_exists = User.query.filter_by(email=email).first() is not None

    if user_already_exists:
        return jsonify({"error": "Cette addresse email est déjà utilisée."}), 409
    
    error = validate_user_fields(email, prenom, nom, mdp, role)
    if error:
        return jsonify({"error": error}), 400
    
    # Création du nouvel utilisateur du mot de passe.
    hashed_password = bcrypt.generate_password_hash(mdp).decode('utf-8')
    new_user = User(email=email,prenom=prenom,nom=nom,mdp=hashed_password,role=role)
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
    new_first_name = request.json["prenom"]
    new_last_name = request.json["nom"]
    new_password = request.json.get("mdp")
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
    user.prenom = new_first_name
    user.nom = new_last_name
    user.role = new_role
    
    if new_password:
        new_hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.mdp = new_hashed_password
    
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
        "prenom": user.prenom,
        "nom": user.nom,
        "email": user.email,
        "role": user.role
    })


@admin_bp.route("/parameters", methods=["GET"])
@admin_required
def get_parameters():
    params = Parameters.query.first()
    if not params:
        params = Parameters()
        db.session.add(params)
        db.session.commit()

    return jsonify({
        "marginRate": params.margin_rate,
        "marginRateLocation": params.margin_rate_location,
        "locationTime": params.location_time,
        "locationSubscriptionCost": params.location_subscription_cost,
        "locationInterestsCost": params.location_interests_cost,
        "locationMaintenanceCost": params.location_interests_cost,
        "generalConditionsSales": params.general_conditions_sales,
        "companyName": params.company_name,
        "companyAddressLine1": params.company_address_line1,
        "companyAddressLine2": params.company_address_line2,
        "companyZip": params.company_zip,
        "companyCity": params.company_city,
        "companyPhone": params.company_phone,
        "companyEmail": params.company_email,
        "companyIban": params.company_iban,
        "companyTva": params.company_tva,
        "companySiret": params.company_siret,
        "companyAprm": params.company_aprm,
    })


@admin_bp.route("/parameters", methods=["POST"])
@admin_required
def update_parameters():
    body = request.get_json(force=True) if request.data else {}

    try:
        margin_rate = _coerce_float(body.get("marginRate"))
        margin_rate_location = _coerce_float(body.get("marginRateLocation"))
        location_time = _coerce_int(body.get("locationTime"))
        location_subscription_cost = _coerce_float(body.get("locationSubscriptionCost"))
        location_maintenance_cost = _coerce_float(body.get("locationInterestsCost") or body.get("locationMaintenanceCost"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    general_conditions_sales = body.get("generalConditionsSales", "") or ""
    company_name = body.get("companyName", "") or ""
    company_address_line1 = body.get("companyAddressLine1", "") or ""
    company_address_line2 = body.get("companyAddressLine2", "") or ""
    company_zip = body.get("companyZip", "") or ""
    company_city = body.get("companyCity", "") or ""
    company_phone = body.get("companyPhone", "") or ""
    company_email = body.get("companyEmail", "") or ""
    company_iban = body.get("companyIban", "") or ""
    company_tva = body.get("companyTva", "") or ""
    company_siret = body.get("companySiret", "") or ""
    company_aprm = body.get("companyAprm", "") or ""

    params = Parameters.query.first()
    if not params:
        params = Parameters()
        db.session.add(params)

    params.margin_rate = margin_rate
    params.margin_rate_location = margin_rate_location
    params.location_time = location_time
    params.location_subscription_cost = location_subscription_cost
    params.location_interests_cost = location_maintenance_cost
    params.general_conditions_sales = general_conditions_sales
    params.company_name = company_name
    params.company_address_line1 = company_address_line1
    params.company_address_line2 = company_address_line2
    params.company_zip = company_zip
    params.company_city = company_city
    params.company_phone = company_phone
    params.company_email = company_email
    params.company_iban = company_iban
    params.company_tva = company_tva
    params.company_siret = company_siret
    params.company_aprm = company_aprm

    db.session.commit()
    logging.info(f"Admin {session.get('user_id')} a mis a jour les parametres de l'application")

    return jsonify({"status": "ok"})


# TVA management
@admin_bp.route("/tva", methods=["GET"])
@admin_required
def list_tva():
    vats = TauxTVA.query.order_by(TauxTVA.id.asc()).all()
    return jsonify({"data": [{"id": v.id, "taux": v.taux} for v in vats]})


@admin_bp.route("/tva", methods=["POST"])
@admin_required
def add_tva():
    body = request.get_json(force=True) if request.data else {}
    try:
        taux = float(body.get("taux"))
    except (TypeError, ValueError):
        return jsonify({"error": "Taux invalide"}), 400

    # Avoid duplicates
    existing = TauxTVA.query.filter_by(taux=taux).first()
    if existing:
        return jsonify({"id": existing.id, "taux": existing.taux})

    new_vat = TauxTVA(taux=taux)
    db.session.add(new_vat)
    db.session.commit()
    logging.info(f"Admin {session.get('user_id')} a ajouté un taux TVA: {taux}")
    return jsonify({"id": new_vat.id, "taux": new_vat.taux})


@admin_bp.route("/tva/<int:tva_id>", methods=["DELETE"])
@admin_required
def delete_tva(tva_id: int):
    vat = TauxTVA.query.get(tva_id)
    if not vat:
        return jsonify({"error": "Taux TVA introuvable"}), 404

    art_refs = Articles.query.filter_by(taux_tva_id=tva_id).count()
    devis_refs = DevisArticles.query.filter_by(taux_tva_id=tva_id).count()
    if art_refs > 0 or devis_refs > 0:
        return (
            jsonify({
                "error": f"Impossible de supprimer: {art_refs} article(s) et {devis_refs} ligne(s) de devis utilisent ce taux."
            }),
            409,
        )

    db.session.delete(vat)
    db.session.commit()
    logging.info(f"Admin {session.get('user_id')} a supprimé le taux TVA id={tva_id}")
    return jsonify({"status": "deleted"})