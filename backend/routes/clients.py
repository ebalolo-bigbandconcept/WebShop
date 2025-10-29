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
@clients_bp.route('/info/<client_id>', methods=['GET'])
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