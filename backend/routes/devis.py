from flask import Blueprint, request, jsonify, session
from models import db, Devis, DevisSchema, DevisArticles
from datetime import datetime
import logging

# Create a Blueprint for authentication-related routes
devis_bp = Blueprint('devis_bp', __name__, url_prefix='/devis')

# Get every devis of every devis route
@devis_bp.route('/all', methods=['GET'])
def get_every_devis():
    devis = Devis.query.all()
    if len(devis) == 0:
        return jsonify({"error": "Aucuns devis trouvé"}), 404
    
    devis_schema = DevisSchema(many=True)
    devis_data = devis_schema.dump(devis)
    return jsonify(data=devis_data)

# Get every devis of a client route
@devis_bp.route('/client/<client_id>', methods=['GET'])
def get_client_devis(client_id):
    devis = Devis.query.filter_by(client_id=client_id).all()
    if not devis:
        return jsonify({"error": "Aucuns devis trouvé"}), 404
    
    devis_schema = DevisSchema(many=True)
    devis_data = devis_schema.dump(devis)
    return jsonify(data=devis_data)

# Get specific devis info route
@devis_bp.route('/info/<devis_id>', methods=['GET'])
def get_devis_info(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404
    
    devis_schema = DevisSchema()
    return devis_schema.jsonify(devis)

# Get new devis id route (for display in front only)
@devis_bp.route('/new-id', methods=['GET'])
def get_new_devis_id():
    new_devis_id = Devis.query.order_by(Devis.id.desc()).first()
    if new_devis_id is None:
        return jsonify({
            "id": 1
        })
        
    return jsonify({
        "id": new_devis_id.id + 1
    })

# Create new devis route
@devis_bp.route('/create', methods=['POST'])
def create_devis():
    titre = request.json["title"]
    description = request.json["description"]
    date = datetime.strptime(request.json["date"],"%Y-%m-%d").date()
    montant_HT = request.json["montant_HT"]
    montant_TVA = request.json["montant_TVA"]
    montant_TTC = request.json["montant_TTC"]
    statut = request.json["statut"]
    client_id = request.json["client_id"]
    articles_data = request.json["articles"]
    
    new_devis = Devis(client_id=client_id,titre=titre,description=description,date=date,montant_HT=montant_HT,montant_TVA=montant_TVA,montant_TTC=montant_TTC,statut=statut)
    db.session.add(new_devis)
    db.session.flush()
    
    for article in articles_data:
        devis_article = DevisArticles(devis_id=new_devis.id,article_id=article["article_id"],quantite=article['quantite'],)
        db.session.add(devis_article)
        
    db.session.commit()
    logging.info(f"Nouveau devis créé: {new_devis.titre} (id: {new_devis.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": new_devis.id
    })

# Update devis route
@devis_bp.route('/update/<devis_id>', methods=['PUT'])
def update_devis(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404
    
    devis.titre = request.json["title"]
    devis.description = request.json["description"]
    devis.date = datetime.strptime(request.json["date"],"%Y-%m-%d").date()
    devis.montant_HT = request.json["montant_HT"]
    devis.montant_TVA = request.json["montant_TVA"]
    devis.montant_TTC = request.json["montant_TTC"]
    devis.statut = request.json["statut"]
    articles_data = request.json["articles"]
    
    try:
        DevisArticles.query.filter_by(devis_id=devis.id).delete()
        
        for article in articles_data:
            devis_article = DevisArticles(devis_id=devis.id,article_id=article["article_id"],quantite=article["quantite"])
            db.session.add(devis_article)
    
        db.session.commit()
        
        logging.info(f"Devis modifié: {devis.titre} (id: {devis.id}) par l'utilisateur {session.get('user_id')}")
    
        return jsonify({
            "id": devis.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Delete devis route
@devis_bp.route('/delete/<devis_id>', methods=['DELETE'])
def delete_devis(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Article non trouvé"}), 404
    
    devis_nom = devis.titre
    Devis.query.filter_by(id=devis_id).delete()
    DevisArticles.query.filter_by(devis_id=devis.id).delete()
    db.session.commit()
    logging.info(f"Devis supprimé: {devis_nom} (id: {devis_id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "200": "Devis successfully deleted."
    })