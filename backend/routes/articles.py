import logging
import os
from datetime import datetime

from flask import Blueprint, jsonify, make_response, render_template, request, session
from weasyprint import HTML

from models import Articles, ArticlesSchema, Parameters, TauxTVA, db
from utils import validate_article_fields

from .admin import admin_required

# Create a Blueprint for articles-related routes
articles_bp = Blueprint("articles_bp", __name__, url_prefix="/api/articles")


### Articles routes ###
# Get all articles info route
@articles_bp.route("/all", methods=["GET"])
def get_all_articles():
    # Check if user is authenticated
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # Ensure reasonable pagination values
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Max 100 items per page

    paginated = Articles.query.order_by(Articles.id.desc()).paginate(
        page=page, per_page=per_page
    )

    if paginated.total == 0:
        return jsonify({"error": "Aucuns articles trouvé"}), 404

    articles_schema = ArticlesSchema(many=True)
    articles_data = articles_schema.dump(paginated.items)

    return jsonify(
        {
            "data": articles_data,
            "pagination": {
                "current_page": page,
                "total_pages": paginated.pages,
                "total_items": paginated.total,
                "per_page": per_page,
                "has_next": paginated.has_next,
                "has_prev": paginated.has_prev,
            },
        }
    )


# Get specific article info route
@articles_bp.route("/info/<article_id>", methods=["GET"])
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

    if taux_tva is None:
        return jsonify({"error": "Le taux de TVA est requis."}), 400
    try:
        taux_val = float(taux_tva)
    except (TypeError, ValueError):
        return jsonify({"error": "Le taux de TVA est invalide."}), 400
    # Accept either 0.20 or 20.0 style inputs
    if taux_val > 1:
        taux_val = taux_val / 100.0
    tva_obj = TauxTVA.query.filter_by(taux=taux_val).first()
    if not tva_obj:
        return jsonify({"error": "Taux TVA introuvable"}), 400
    taux_tva_id = tva_obj.id

    # Get margin rate from parameters and calculate selling price
    params = Parameters.query.first()
    margin_rate = params.margin_rate if params else 0.0
    prix_vente_HT = float(prix_achat_HT) * margin_rate

    error = validate_article_fields(
        nom, reference, prix_achat_HT, prix_vente_HT, taux_tva_id
    )
    if error:
        return jsonify({"error": error}), 400

    new_article = Articles(
        nom=nom,
        reference=reference,
        prix_achat_HT=prix_achat_HT,
        prix_vente_HT=prix_vente_HT,
        taux_tva_id=taux_tva_id,
    )
    db.session.add(new_article)
    db.session.commit()
    logging.info(
        f"Nouvel article ajouté: {new_article.nom} (id: {new_article.id}) par l'utilisateur {session.get('user_id')}"
    )

    return jsonify({"id": new_article.id})


# Modify article route
@articles_bp.route("/update/<article_id>", methods=["POST"])
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

    if new_taux_tva is None:
        return jsonify({"error": "Le taux de TVA est requis."}), 400
    try:
        new_taux_val = float(new_taux_tva)
    except (TypeError, ValueError):
        return jsonify({"error": "Le taux de TVA est invalide."}), 400
    if new_taux_val > 1:
        new_taux_val = new_taux_val / 100.0
    new_tva_obj = TauxTVA.query.filter_by(taux=new_taux_val).first()
    if not new_tva_obj:
        return jsonify({"error": "Taux TVA introuvable"}), 400
    new_taux_tva_id = new_tva_obj.id

    params = Parameters.query.first()
    margin_rate = params.margin_rate if params else 0.0
    new_prix_vente_HT = float(new_prix_achat_HT) * margin_rate

    error = validate_article_fields(
        new_nom, new_reference, new_prix_achat_HT, new_prix_vente_HT, new_taux_tva_id
    )
    if error:
        return jsonify({"error": error}), 400

    article.nom = new_nom
    article.reference = new_reference
    article.prix_achat_HT = new_prix_achat_HT
    article.prix_vente_HT = new_prix_vente_HT
    article.taux_tva_id = new_taux_tva_id

    db.session.commit()
    logging.info(
        f"Article modifié: {article.nom} (id: {article.id}) par l'utilisateur {session.get('user_id')}"
    )

    return jsonify({"id": article.id})


# Delete article route
@articles_bp.route("/delete/<article_id>", methods=["DELETE"])
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
    logging.info(
        f"Article supprimé: {article_name} (id: {article_id}) par l'utilisateur {session.get('user_id')}"
    )

    return jsonify({"message": "Article supprimé avec succès"})


# Export all articles as PDF
@articles_bp.route("/export-pdf", methods=["GET"])
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
            articles_data.append(
                {
                    "id": article.id,
                    "nom": article.nom,
                    "reference": article.reference,
                    "prix_achat_HT": article.prix_achat_HT,
                    "prix_vente_HT": article.prix_vente_HT,
                    "taux_tva": article.taux_tva,
                }
            )

        # Render HTML using Jinja2 template
        html_out = render_template(
            "articles_list.html",
            articles=articles_data,
            date=current_date,
            company_name=company_name,
        )

        # Calculate the absolute path to the pdf folder
        base_path = "/app/pdf/"

        # Generate PDF
        pdf_bytes = HTML(string=html_out, base_url=base_path).write_pdf()

        # Return PDF as response
        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=liste_articles_{current_date.replace('/', '-')}.pdf"
        )
        return response

    except Exception as e:
        logging.error(f"Error generating articles PDF: {e}")
        return jsonify({"error": "Erreur lors de la génération du PDF"}), 500
