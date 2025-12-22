from models import TauxTVA
import re

# Validate user fields for database entry
VALID_ROLES = {"Utilisateur", "Administrateur"}

def validate_user_fields(email, nom, prenom, mdp=None, role=None):
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

def _coerce_float(value, default=0.0):
        if value in (None, ""):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError("Ce champ doit etre un nombre.")


def _coerce_int(value, default=0):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError("Ce champ doit etre un entier.")