from flask import Blueprint, request, jsonify, session
from models import db, Clients, ClientsSchema
from utils import validate_client_fields
import logging

# Create a Blueprint for clients-related routes
clients_bp = Blueprint('clients_bp', __name__, url_prefix='/clients')

# Get all clients info route
@clients_bp.route("/all", methods=['GET'])
def get_all_clients():
    tableEmpty = Clients.query.first() is None
    if tableEmpty:
        return jsonify({"error": "Aucun clients trouvé"}), 404
    
    clients = Clients.query.all()
    clients_schema = ClientsSchema(many=True)
    clients_data = clients_schema.dump(clients)
    return jsonify(data=clients_data)

# Add new client route
@clients_bp.route("/create", methods=["POST"])
def add_client():
    nom = request.json["nom"]
    prenom = request.json["prenom"]
    rue = request.json["rue"]
    ville = request.json["ville"]
    code_postal = request.json["code_postal"]
    telephone = request.json["telephone"]
    email = request.json["email"]
    force = request.json["force"]
    
    error = validate_client_fields(nom, prenom, rue, ville, code_postal, telephone, email)
    if error:
        return jsonify({"error": error}), 400
    
    # Check if email already exists
    existing = Clients.query.filter_by(email=email).first()
    if existing and not force:
        return jsonify({
            "warning": "L'adresse e-mail est déjà utilisée par un autre client.",
            "email_exists": True
        }), 409  # 409 Conflict
    
    new_client = Clients(nom=nom,prenom=prenom,rue=rue,ville=ville,code_postal=code_postal,telephone=telephone,email=email,caduque=False)
    db.session.add(new_client)
    db.session.commit()
    logging.info(f"Nouvel client ajouté: {new_client.email} (id: {new_client.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": new_client.id
    })

# Modify client route
@clients_bp.route("/update/<client_id>", methods=["POST"])
def modify_client(client_id):
    client = Clients.query.get(client_id)
    if not client:
        return jsonify({"error": "Client introuvable"}), 404

    new_nom = request.json["nom"]
    new_prenom = request.json["prenom"]
    new_rue = request.json["rue"]
    new_ville = request.json["ville"]
    new_code_postal = request.json["code_postal"]
    new_telephone = request.json["telephone"]
    new_email = request.json["email"]
    new_caduque = request.json["caduque"]
    force = request.json["force"]

    # Validate fields
    error = validate_client_fields(new_nom, new_prenom, new_rue, new_ville, new_code_postal, new_telephone, new_email)
    if error:
        return jsonify({"error": error}), 400
    
    # Email already used by someone else?
    existing = Clients.query.filter(Clients.email == new_email, Clients.id != client_id).first()
    if existing and not force:
        return jsonify({"error": "Cette adresse email est déjà utilisée par un autre client.",}), 409

    # Update client data
    client.nom = new_nom
    client.prenom = new_prenom
    client.rue = new_rue
    client.ville = new_ville
    client.code_postal = new_code_postal
    client.telephone = new_telephone
    client.email = new_email
    client.caduque = new_caduque

    db.session.commit()
    logging.info(f"Client modifié: {client.email} (id: {client.id}) par l'utilisateur {session.get('user_id')}")

    return jsonify({
        "id": client.id,
        "message": "Client mis à jour avec succès"
    }), 200

# Get client info route
@clients_bp.route('/info/<client_id>', methods=['GET'])
def get_client_info(client_id):
    client = Clients.query.filter_by(id=client_id).first()
    return jsonify({
        "id": client.id,
        "prenom": client.prenom,
        "nom": client.nom,
        "rue": client.rue,
        "ville": client.ville,
        "code_postal": client.code_postal,
        "telephone": client.telephone,
        "email": client.email,
        "caduque": client.caduque,
    })