from flask import Blueprint, request, jsonify, session, render_template, make_response
from models import db, Articles, ArticlesSchema, TauxTVA, Parameters
import logging
from .admin import admin_required
from utils import validate_article_fields
from weasyprint import HTML
from datetime import datetime
import os

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
    reference = request.json["reference"]
    prix_achat_HT = request.json["prix_achat_HT"]
    taux_tva = request.json["taux_tva"]
    
    if not taux_tva:
        return jsonify({"error": "Le taux de TVA est requis."}), 400
        
    taux_tva_id = TauxTVA.query.filter_by(taux=taux_tva).first().id
    
    # Get margin rate from parameters and calculate selling price
    params = Parameters.query.first()
    margin_rate = params.margin_rate if params else 0.0
    prix_vente_HT = float(prix_achat_HT) * margin_rate
    
    error = validate_article_fields(nom, reference, prix_achat_HT, prix_vente_HT, taux_tva_id)
    if error:
        return jsonify({"error": error}), 400
    
    new_article = Articles(
        nom=nom,
        reference=reference,
        prix_achat_HT=prix_achat_HT,
        prix_vente_HT=prix_vente_HT,
        taux_tva_id=taux_tva_id
    )
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
    new_reference = request.json["reference"]
    new_prix_achat_HT = request.json["prix_achat_HT"]
    new_taux_tva = request.json["taux_tva"]
    
    if not new_taux_tva:
        return jsonify({"error": "Le taux de TVA est requis."}), 400
        
    new_taux_tva_id = TauxTVA.query.filter_by(taux=new_taux_tva).first().id

    params = Parameters.query.first()
    margin_rate = params.margin_rate if params else 0.0
    new_prix_vente_HT = float(new_prix_achat_HT) * margin_rate
    
    error = validate_article_fields(new_nom, new_reference, new_prix_achat_HT, new_prix_vente_HT, new_taux_tva_id)
    if error:
        return jsonify({"error": error}), 400
    
    article.nom = new_nom
    article.reference = new_reference
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

# Export all articles as PDF
@articles_bp.route("/export-pdf", methods=['GET'])
def export_articles_pdf():
    # Check if user is authenticated
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        articles = Articles.query.order_by(Articles.id.asc()).all()
        
        if not articles:
            return jsonify({"error": "Aucuns articles trouvé"}), 404
        
        # Get company info from parameters
        params = Parameters.query.first()
        company_name = params.company_name if params else "Artech Sécurité"
        
        # Format current date
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        # Prepare articles data
        articles_data = []
        for article in articles:
            articles_data.append({
                'id': article.id,
                'nom': article.nom,
                'reference': article.reference,
                'prix_achat_HT': article.prix_achat_HT,
                'prix_vente_HT': article.prix_vente_HT,
                'taux_tva': article.taux_tva
            })
        
        # Render HTML using Jinja2 template
        html_out = render_template(
            "articles_list.html",
            articles=articles_data,
            date=current_date,
            company_name=company_name
        )
        
        # Calculate the absolute path to the pdf folder
        base_path = '/app/pdf/'
        
        # Generate PDF
        pdf_bytes = HTML(string=html_out, base_url=base_path).write_pdf()
        
        # Return PDF as response
        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename=liste_articles_{current_date.replace('/', '-')}.pdf"
        return response
    
    except Exception as e:
        logging.error(f"Error generating articles PDF: {e}")
        return jsonify({"error": "Erreur lors de la génération du PDF"}), 500