from flask import Blueprint, request, jsonify, session
from models import db, Articles, ArticlesSchema, TauxTVA, Parameters
import logging
from .admin import admin_required
from utils import validate_article_fields

# Create a Blueprint for articles-related routes
articles_bp = Blueprint('articles_bp', __name__, url_prefix='/api/articles')


### Articles routes ###
# Get all articles info route
@articles_bp.route("/all", methods=['GET'])
def get_all_articles():
    # Check if user is authenticated
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    tableEmpty = Articles.query.first() is None
    if tableEmpty:
        return jsonify({"error": "Aucuns articles trouvé"}), 404
    
    articles = Articles.query.order_by(Articles.id.asc()).all()
    articles_schema = ArticlesSchema(many=True)
    articles_data = articles_schema.dump(articles)
    return jsonify(data=articles_data)

# Get specific article info route
@articles_bp.route('/info/<article_id>', methods=['GET'])
def get_article_info(article_id):
    # Check if user is authenticated
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    article = Articles.query.filter_by(id=article_id).first()
    if not article:
        return jsonify({"error": "Article non trouvé"}), 404
    
    article_schema = ArticlesSchema()
    return article_schema.jsonify(article)

# Add new article route
@articles_bp.route("/create", methods=["POST"])
def add_article():
    # Check if user is authenticated
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    nom = request.json["nom"]
    description = request.json["description"]
    prix_achat_HT = request.json["prix_achat_HT"]
    taux_tva = request.json["taux_tva"]
    
    if not taux_tva:
        return jsonify({"error": "Le taux de TVA est requis."}), 400
        
    taux_tva_id = TauxTVA.query.filter_by(taux=taux_tva).first().id
    
    # Get margin rate from parameters and calculate selling price
    params = Parameters.query.first()
    margin_rate = params.margin_rate if params else 0.0
    prix_vente_HT = float(prix_achat_HT) * margin_rate
    
    error = validate_article_fields(nom, description, prix_achat_HT, prix_vente_HT, taux_tva_id)
    if error:
        return jsonify({"error": error}), 400
    
    new_article = Articles(nom=nom,description=description,prix_achat_HT=prix_achat_HT,prix_vente_HT=prix_vente_HT,taux_tva_id=taux_tva_id)
    db.session.add(new_article)
    db.session.commit()
    logging.info(f"Nouvel article ajouté: {new_article.nom} (id: {new_article.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": new_article.id
    })

# Modify article route
@articles_bp.route("/update/<article_id>", methods=['POST'])
def modify_article(article_id):
    # Check if user is authenticated
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    article = Articles.query.filter_by(id=article_id).first()
    if not article:
        return jsonify({"error": "Article non trouvé"}), 404
    
    new_nom = request.json["nom"]
    new_description = request.json["description"]
    new_prix_achat_HT = request.json["prix_achat_HT"]
    new_taux_tva = request.json["taux_tva"]
    
    if not new_taux_tva:
        return jsonify({"error": "Le taux de TVA est requis."}), 400
        
    new_taux_tva_id = TauxTVA.query.filter_by(taux=new_taux_tva).first().id

    params = Parameters.query.first()
    margin_rate = params.margin_rate if params else 0.0
    new_prix_vente_HT = float(new_prix_achat_HT) * margin_rate
    
    error = validate_article_fields(new_nom, new_description, new_prix_achat_HT, new_prix_vente_HT, new_taux_tva_id)
    if error:
        return jsonify({"error": error}), 400
    
    article.nom = new_nom
    article.description = new_description
    article.prix_achat_HT = new_prix_achat_HT
    article.prix_vente_HT = new_prix_vente_HT
    article.taux_tva_id = new_taux_tva_id
    
    db.session.commit()
    logging.info(f"Article modifié: {article.nom} (id: {article.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": article.id
    })

# Delete article route
@articles_bp.route("/delete/<article_id>", methods=['POST'])
def delete_article(article_id):
    # Check if user is authenticated
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    article = Articles.query.filter_by(id=article_id).first()
    if not article:
        return jsonify({"error": "Article non trouvé"}), 404
    
    article_name = article.nom
    Articles.query.filter_by(id=article_id).delete()
    db.session.commit()
    logging.info(f"Article supprimé: {article_name} (id: {article_id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "200": "Article successfully deleted."
    })