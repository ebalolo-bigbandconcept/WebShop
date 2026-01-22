from models import TauxTVA, User
from flask import request, jsonify, session
from functools import wraps
from typing import Optional, Callable, Any
import re

# Validate user fields for database entry
VALID_ROLES = {"Utilisateur", "Administrateur"}

def validate_user_fields(email: str, nom: str, prenom: str, mdp: Optional[str] = None, role: Optional[str] = None) -> Optional[str]:
    if not is_valid_email(email) or len(email) > 345:
        return "Format d'email invalide ou trop long."
    if len(prenom) < 1 or len(prenom) > 50:
        return "Le prénom doit contenir entre 1 et 50 caractères."
    if len(nom) < 1 or len(nom) > 50:
        return "Le nom doit contenir entre 1 et 50 caractères."
    if role and role not in VALID_ROLES:
        return "Rôle invalide."
    if mdp is not None:
        if not is_strong_password(mdp):
            return "Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial."
    return None

def validate_client_fields(nom: str, prenom: str, rue: str, ville: str, code_postal: str, telephone: str, email: str) -> Optional[str]:
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

def validate_article_fields(nom: str, reference: str, prix_achat_HT: float, prix_vente_HT: float, taux_tva_id: int) -> Optional[str]:
    if len(nom) < 1 or len(nom) > 200:
        return "Le nom de l'article doit contenir entre 1 et 200 caractères."
    # Reference becomes optional; allow empty string
    if float(prix_achat_HT) < 0:
        return "Le prix d'achat HT ne peut pas être négatif."
    if float(prix_vente_HT) < 0:
        return "Le prix de vente HT ne peut pas être négatif."
    taux_tva = TauxTVA.query.filter_by(id=taux_tva_id).first()
    if not taux_tva:
        return "Le taux de TVA spécifié n'existe pas."
    return None

# Email validation function
def is_valid_email(email: str) -> bool:
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Password strength validation function
def is_strong_password(password: str) -> bool:
    # Au moins 8 caractères, une majuscule, une minuscule, un chiffre, un caractère spécial
    regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
    return re.match(regex, password) is not None

def _coerce_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError("Ce champ doit etre un nombre.")

def _coerce_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError("Ce champ doit etre un entier.")

def validated_json(*required_fields: str) -> Callable:
    """Decorator to validate JSON requests and required fields.
    Prevents crashes on malformed JSON.
    
    Args:
        *required_fields: Field names that must be present in the JSON body
        
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            try:
                data = request.get_json(force=True)
                if data is None:
                    return jsonify({"error": "Request body must be valid JSON"}), 400
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": "Invalid JSON in request body"}), 400
        return wrapped
    return decorator


def require_login(roles: Optional[set] = None) -> Callable:
    """Decorator to ensure the caller is authenticated and optionally has the right role."""
    roles = set(roles) if roles else None

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            user_id = session.get("user_id")
            if not user_id:
                return jsonify({"error": "Unauthorized"}), 401

            user = User.query.filter_by(id=user_id).first()
            if not user:
                session.pop("user_id", None)
                return jsonify({"error": "Unauthorized"}), 401

            if roles and user.role not in roles:
                return jsonify({"error": "Forbidden"}), 403

            return f(*args, **kwargs)

        return wrapped

    return decorator