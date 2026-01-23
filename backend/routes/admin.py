from flask import Blueprint, request, jsonify, session
from flask_bcrypt import Bcrypt
from models import db, User, UserSchema, Parameters, TauxTVA, Articles, DevisArticles
from functools import wraps
import logging
import bleach
from utils import validate_user_fields, _coerce_float, _coerce_int, validated_json, require_login

# Create a Blueprint for admin-related routes
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/api/admin')

bcrypt = Bcrypt()

# Get loggers
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')

# Admin role required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            security_logger.warning(
                "Unauthorized access attempt to admin endpoint",
                extra={
                    'action': 'UNAUTHORIZED_ACCESS',
                    'resource': request.path,
                    'ip_address': request.remote_addr,
                    'status': 'NO_SESSION'
                }
            )
            return jsonify({"error": "Unauthorized"}), 401
        
        user = User.query.filter_by(id=user_id).first()
        if user.role != 'Administrateur':
            security_logger.warning(
                f"Forbidden access attempt by non-admin user: {user.email}",
                extra={
                    'action': 'FORBIDDEN_ACCESS',
                    'user_id': user.id,
                    'user_email': user.email,
                    'resource': request.path,
                    'ip_address': request.remote_addr,
                    'status': 'INSUFFICIENT_PRIVILEGES'
                }
            )
            return jsonify({"error": "Forbidden"}), 403
        
        return f(*args, **kwargs)
    return decorated_function


# Get all users info route
@admin_bp.route("/all-user", methods=['GET'])
@admin_required
def get_all_users():
    users = User.query.order_by(User.id.asc()).all()
    user_schema = UserSchema(many=True)
    user_data = user_schema.dump(users)
    return jsonify(data=user_data)

# Add new user route
@admin_bp.route("/create-user", methods=["POST"])
@admin_required
@validated_json("email", "prenom", "nom", "mdp", "role")
def add_user():
    admin_id = session.get('user_id')
    admin = User.query.filter_by(id=admin_id).first()
    
    data = request.get_json()
    email = data.get("email", "").strip()
    prenom = data.get("prenom", "").strip()
    nom = data.get("nom", "").strip()
    mdp = data.get("mdp", "")
    role = data.get("role", "").strip()
    
    # Vérification si le nom d'utilisateur existe déjà.
    user_already_exists = User.query.filter_by(email=email).first() is not None

    if user_already_exists:
        return jsonify({"error": "Cette addresse email est déjà utilisée."}), 409
    
    error = validate_user_fields(email, prenom, nom, mdp, role)
    if error:
        return jsonify({"error": error}), 400
    
    # Création du nouvel utilisateur du mot de passe.
    hashed_password = bcrypt.generate_password_hash(mdp).decode('utf-8')
    new_user = User(
        email=email,
        prenom=prenom,
        nom=nom,
        mdp=hashed_password,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    
    security_logger.info(
        f"Admin created new user: {new_user.email} with role {new_user.role}",
        extra={
            'action': 'USER_CREATED',
            'user_id': admin.id,
            'user_email': admin.email,
            'resource': f"user:{new_user.id}",
            'ip_address': request.remote_addr,
            'status': 'SUCCESS',
            'target_email': new_user.email,
            'target_role': new_user.role
        }
    )
    
    return jsonify({
        "user_id": new_user.id
    }), 201

# Modify user route
@admin_bp.route("/update-user/<user_id>", methods=['POST'])
@admin_required
def modify_user(user_id):
    admin_id = session.get('user_id')
    admin = User.query.filter_by(id=admin_id).first()
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    old_email = user.email
    old_role = user.role
    
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
    
    password_changed = False
    if new_password:
        new_hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.mdp = new_hashed_password
        password_changed = True
    
    db.session.commit()
    
    changes = []
    if old_email != new_email:
        changes.append(f"email: {old_email} -> {new_email}")
    if old_role != new_role:
        changes.append(f"role: {old_role} -> {new_role}")
    if password_changed:
        changes.append("password updated")
    
    security_logger.info(
        f"Admin updated user: {user.email} - Changes: {', '.join(changes) if changes else 'profile info'}",
        extra={
            'action': 'USER_UPDATED',
            'user_id': admin.id,
            'user_email': admin.email,
            'resource': f"user:{user.id}",
            'ip_address': request.remote_addr,
            'status': 'SUCCESS',
            'target_email': user.email,
            'changes': changes
        }
    )
    
    return jsonify({
        "id": user.id,
        "message": "User updated successfully"
    })
    
# Delete user route
@admin_bp.route("/delete-user/<user_id>", methods=['POST', 'DELETE'])
@admin_required
def delete_user(user_id):
    admin_id = session.get('user_id')
    admin = User.query.filter_by(id=admin_id).first()
    
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
    user_role = user.role
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    
    security_logger.warning(
        f"Admin deleted user: {user_email}",
        extra={
            'action': 'USER_DELETED',
            'user_id': admin.id,
            'user_email': admin.email,
            'resource': f"user:{user_id}",
            'ip_address': request.remote_addr,
            'status': 'SUCCESS',
            'target_email': user_email,
            'target_role': user_role
        }
    )
    
    return jsonify({
        "message": "User deleted successfully"
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
@require_login({"Administrateur", "Utilisateur"})
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
        margin_rate = _coerce_float(body.get("marginRate") if body.get("marginRate") is not None else body.get("margin_rate"))
        margin_rate_location = _coerce_float(body.get("marginRateLocation") if body.get("marginRateLocation") is not None else body.get("margin_rate_location"))
        location_time = _coerce_int(body.get("locationTime") if body.get("locationTime") is not None else body.get("location_time"))
        location_subscription_cost = _coerce_float(body.get("locationSubscriptionCost") if body.get("locationSubscriptionCost") is not None else body.get("location_subscription_cost"))
        location_maintenance_cost = _coerce_float(
            (body.get("locationInterestsCost") if body.get("locationInterestsCost") is not None else body.get("location_maintenance_cost"))
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    general_conditions_sales = (
        body.get("generalConditionsSales") if body.get("generalConditionsSales") is not None else body.get("general_conditions_sales", "")
    ) or ""
    # Sanitize HTML to prevent XSS attacks - allow common HTML tags
    general_conditions_sales = bleach.clean(general_conditions_sales, tags=['b', 'i', 'u', 'p', 'br', 'strong', 'em', 'ul', 'ol', 'li'], strip=True)
    
    company_name = (body.get("companyName") if body.get("companyName") is not None else body.get("company_name", "")) or ""
    company_address_line1 = (body.get("companyAddressLine1") if body.get("companyAddressLine1") is not None else body.get("company_address_line1", "")) or ""
    company_address_line2 = (body.get("companyAddressLine2") if body.get("companyAddressLine2") is not None else body.get("company_address_line2", "")) or ""
    company_zip = (body.get("companyZip") if body.get("companyZip") is not None else body.get("company_zip", "")) or ""
    company_city = (body.get("companyCity") if body.get("companyCity") is not None else body.get("company_city", "")) or ""
    company_phone = (body.get("companyPhone") if body.get("companyPhone") is not None else body.get("company_phone", "")) or ""
    company_email = (body.get("companyEmail") if body.get("companyEmail") is not None else body.get("company_email", "")) or ""
    company_iban = (body.get("companyIban") if body.get("companyIban") is not None else body.get("company_iban", "")) or ""
    company_tva = (body.get("companyTva") if body.get("companyTva") is not None else body.get("company_tva", "")) or ""
    company_siret = (body.get("companySiret") if body.get("companySiret") is not None else body.get("company_siret", "")) or ""
    company_aprm = (body.get("companyAprm") if body.get("companyAprm") is not None else body.get("company_aprm", "")) or ""

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
    
    admin_id = session.get('user_id')
    admin = User.query.filter_by(id=admin_id).first()
    
    security_logger.info(
        f"Admin updated application parameters",
        extra={
            'action': 'PARAMETERS_UPDATED',
            'user_id': admin.id if admin else admin_id,
            'user_email': admin.email if admin else 'unknown',
            'resource': 'application_parameters',
            'ip_address': request.remote_addr,
            'status': 'SUCCESS'
        }
    )

    return jsonify({"message": "Parameters updated successfully"}), 200


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
    
    admin_id = session.get('user_id')
    admin = User.query.filter_by(id=admin_id).first()
    
    security_logger.info(
        f"Admin added new VAT rate: {taux}%",
        extra={
            'action': 'VAT_CREATED',
            'user_id': admin.id if admin else admin_id,
            'user_email': admin.email if admin else 'unknown',
            'resource': f"vat:{new_vat.id}",
            'ip_address': request.remote_addr,
            'status': 'SUCCESS',
            'vat_rate': taux
        }
    )
    
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

    vat_rate = vat.taux
    db.session.delete(vat)
    db.session.commit()
    
    admin_id = session.get('user_id')
    admin = User.query.filter_by(id=admin_id).first()
    
    security_logger.warning(
        f"Admin deleted VAT rate: {vat_rate}%",
        extra={
            'action': 'VAT_DELETED',
            'user_id': admin.id if admin else admin_id,
            'user_email': admin.email if admin else 'unknown',
            'resource': f"vat:{tva_id}",
            'ip_address': request.remote_addr,
            'status': 'SUCCESS',
            'vat_rate': vat_rate
        }
    )
    
    return jsonify({"status": "deleted"})