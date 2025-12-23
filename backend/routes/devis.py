from flask import Blueprint, request, jsonify, session, render_template, make_response, redirect
from models import db, Devis, DevisSchema, DevisArticles, Clients, Articles, TauxTVA, Parameters
from datetime import datetime
from weasyprint import HTML
from PyPDF2 import PdfMerger
import io, logging, os, requests, json

# Create a Blueprint for authentication-related routes
devis_bp = Blueprint('devis_bp', __name__, url_prefix='/api/devis')

def _build_article_map(articles_payload):
    article_ids = [article.get("article_id") for article in articles_payload if article.get("article_id")]
    if not article_ids:
        return {}
    articles = Articles.query.filter(Articles.id.in_(article_ids)).all()
    return {article.id: article for article in articles}


def _resolve_tva_id(article_payload, articles_map):
    taux_tva_id = article_payload.get("taux_tva_id")
    if taux_tva_id:
        return taux_tva_id

    taux_value = article_payload.get("taux_tva")
    if taux_value is not None:
        existing_tva = TauxTVA.query.filter_by(taux=taux_value).first()
        if existing_tva:
            return existing_tva.id
        new_tva = TauxTVA(taux=taux_value)
        db.session.add(new_tva)
        db.session.flush()
        return new_tva.id

    article = articles_map.get(article_payload.get("article_id"))
    return article.taux_tva_id if article else None


# Public endpoint to list all VAT rates (no admin required)
@devis_bp.route('/tva', methods=['GET'])
def list_vat_public():
    vats = TauxTVA.query.order_by(TauxTVA.id.asc()).all()
    return jsonify({"data": [{"id": v.id, "taux": v.taux} for v in vats]})

# Get every devis of every devis route
@devis_bp.route('/all', methods=['GET'])
def get_every_devis():
    devis = Devis.query.order_by(Devis.id.asc()).all()
    if len(devis) == 0:
        return jsonify({"error": "Aucuns devis trouvé"}), 404
    
    devis_schema = DevisSchema(many=True)
    devis_data = devis_schema.dump(devis)
    return jsonify(data=devis_data)

# Get every devis of a client route
@devis_bp.route('/client/<client_id>', methods=['GET'])
def get_client_devis(client_id):
    devis = Devis.query.filter_by(client_id=client_id).order_by(Devis.id.asc()).all()
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
    is_location = request.json.get("is_location", False)
    first_contribution_amount = request.json.get("first_contribution_amount")
    location_monthly_total = request.json.get("location_monthly_total")
    location_monthly_total_ht = request.json.get("location_monthly_total_ht")
    location_total = request.json.get("location_total")
    location_total_ht = request.json.get("location_total_ht")
    
    new_devis = Devis(
        client_id=client_id,
        titre=titre,
        description=description,
        date=date,
        montant_HT=montant_HT,
        montant_TVA=montant_TVA,
        montant_TTC=montant_TTC,
        statut=statut,
        is_location=is_location,
        first_contribution_amount=first_contribution_amount,
        location_monthly_total=location_monthly_total,
        location_monthly_total_ht=location_monthly_total_ht,
        location_total=location_total,
        location_total_ht=location_total_ht,
    )
    db.session.add(new_devis)
    db.session.flush()
    
    articles_map = _build_article_map(articles_data)
    for article in articles_data:
        tva_id = _resolve_tva_id(article, articles_map)
        devis_article = DevisArticles(
            devis_id=new_devis.id,
            article_id=article["article_id"],
            quantite=article['quantite'],
            taux_tva_id=tva_id,
            commentaire=article.get('commentaire')
        )
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
    devis.is_location = request.json.get("is_location", False)
    devis.first_contribution_amount = request.json.get("first_contribution_amount")
    devis.location_monthly_total = request.json.get("location_monthly_total")
    devis.location_monthly_total_ht = request.json.get("location_monthly_total_ht")
    devis.location_total = request.json.get("location_total")
    devis.location_total_ht = request.json.get("location_total_ht")
    articles_data = request.json["articles"]
    
    try:
        DevisArticles.query.filter_by(devis_id=devis.id).delete()

        articles_map = _build_article_map(articles_data)
        for article in articles_data:
            tva_id = _resolve_tva_id(article, articles_map)
            devis_article = DevisArticles(
                devis_id=devis.id,
                article_id=article["article_id"],
                quantite=article["quantite"],
                taux_tva_id=tva_id,
                commentaire=article.get('commentaire')
            )
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
    # Delete devis articles first to avoid foreign key constraint violation
    DevisArticles.query.filter_by(devis_id=devis.id).delete()
    Devis.query.filter_by(id=devis_id).delete()
    db.session.commit()
    logging.info(f"Devis supprimé: {devis_nom} (id: {devis_id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "200": "Devis successfully deleted."
    })

# Create PDF of the devis
@devis_bp.route('/pdf/<devis_id>', methods=['GET'])
def get_devis_pdf(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404

    # Scenario selection for PDF rendering
    selected_scenario = request.args.get("scenario") or "direct"
    if selected_scenario not in {"direct", "location_without_apport", "location_with_apport"}:
        selected_scenario = "direct"
    
    # Convert Devis object to dict including articles
    devis_schema = DevisSchema()
    devis_data = devis_schema.dump(devis)

    # Compute totals by VAT rate from per-line or article default
    vat_totals_map = {}
    for item in devis_data.get('articles', []):
        try:
            taux = None
            if item.get('taux_tva') and item['taux_tva'].get('taux') is not None:
                taux = float(item['taux_tva']['taux'])
            else:
                taux = float(item['article']['taux_tva']['taux'])

            qty = float(item.get('quantite') or 0)
            unit_ht = float(item.get('article', {}).get('prix_vente_HT') or 0)
            line_ht = qty * unit_ht
            line_tva = line_ht * (taux or 0.0)
            line_ttc = line_ht + line_tva

            bucket = vat_totals_map.setdefault(taux, {"total_ht": 0.0, "total_tva": 0.0, "total_ttc": 0.0})
            bucket["total_ht"] += line_ht
            bucket["total_tva"] += line_tva
            bucket["total_ttc"] += line_ttc
        except Exception:
            # Skip malformed items silently for PDF rendering
            continue

    # Build a minimal map for 20% and 10% showing only total TVA
    vat_tva_totals = {}
    for wanted in (0.20, 0.10):
        if wanted in vat_totals_map:
            vat_tva_totals[wanted] = round(vat_totals_map[wanted]["total_tva"], 2)

    # Fetch parameters for general conditions, location duration and fees
    params = Parameters.query.first()
    general_conditions = params.general_conditions_sales if params else ""
    location_time = params.location_time if params else 0
    subscription_ttc = params.location_subscription_cost if params else 0.0
    maintenance_ttc = params.location_interests_cost if params else 0.0
    company_info = {
        "name": params.company_name if params else "",
        "address_line1": params.company_address_line1 if params else "",
        "address_line2": params.company_address_line2 if params else "",
        "zip": params.company_zip if params else "",
        "city": params.company_city if params else "",
        "phone": params.company_phone if params else "",
        "email": params.company_email if params else "",
        "iban": params.company_iban if params else "",
        "tva": params.company_tva if params else "",
        "siret": params.company_siret if params else "",
        "aprm": params.company_aprm if params else "",
    }

    def _compute_location_totals(apport_value):
        articles_ttc = float(devis_data.get("montant_TTC") or 0.0)
        apport = float(apport_value or 0.0)

        total_ht_value = articles_ttc + float(subscription_ttc or 0.0) + float(maintenance_ttc or 0.0) - apport
        total_ht_value = max(total_ht_value, 0.0)
        total_ttc_value = total_ht_value * 1.20

        monthly_ht = (total_ht_value / location_time) if location_time else 0.0
        monthly_ttc = (total_ttc_value / location_time) if location_time else 0.0

        return {
            "monthly_ht": round(monthly_ht, 2),
            "monthly_ttc": round(monthly_ttc, 2),
            "total_ht": round(total_ht_value, 2),
            "total_ttc": round(total_ttc_value, 2),
            "apport": round(apport, 2),
        }

    payment_options = {
        "direct": {"total_ttc": round(float(devis_data.get("montant_TTC") or 0.0), 2)},
        "location_without_apport": _compute_location_totals(0.0),
        "location_with_apport": _compute_location_totals(devis_data.get("first_contribution_amount")),
    }

    # Render HTML using Jinja2 template
    html_out = render_template(
        "pdf.html",
        devis=devis_data,
        vat_tva_totals=vat_tva_totals,
        general_conditions=general_conditions,
        location_time=location_time,
        company=company_info,
        selected_scenario=selected_scenario,
        payment_options=payment_options,
    )
    
    # Calculate the absolute path to the folder containing your template and static files
    base_path = '/app/pdf/'

    # Generate PDF
    pdf_bytes = HTML(string=html_out, base_url=base_path).write_pdf()

    # Append location contract only for location scenarios
    if devis.is_location and selected_scenario in {"location_without_apport", "location_with_apport"}:
        try:
            contract_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pdf", "location_contract.pdf"))
            if os.path.isfile(contract_path):
                merged = PdfMerger()
                merged.append(io.BytesIO(pdf_bytes))
                merged.append(contract_path)
                buffer = io.BytesIO()
                merged.write(buffer)
                pdf_bytes = buffer.getvalue()
            else:
                logging.warning(f"Location contract PDF not found at {contract_path}; returning devis PDF only.")
        except Exception as merge_err:
            logging.exception(f"Failed to append location contract PDF: {merge_err}")

    # Return PDF as response
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=devis_{devis_id}.pdf"
    return response

### DocuSign routes ###

# Send PDF to external service for signing
@devis_bp.route('/pdf/send/external/<client_id>/<devis_id>', methods=['POST'])
def external_send_pdf_sign(client_id, devis_id):
    try:
        file = request.files['file']
        client = Clients.query.filter_by(id=client_id).first()
        if not client:
            return jsonify({"error": "Client non trouvé."}), 404
        
        devis = Devis.query.filter_by(id=devis_id).first()
        if not devis:
            return jsonify({"error": "Devis non trouvé."}), 404
        
        email = client.email
        nom = client.nom
        prenom = client.prenom

        # Get other Docusign credentials from environment variables
        integrator_key = open("/run/secrets/DOCUSIGN_INTEGRATION_KEY").read().strip() if os.path.exists("/run/secrets/DOCUSIGN_INTEGRATION_KEY") else os.getenv("DOCUSIGN_INTEGRATION_KEY")
        account_id = open("/run/secrets/DOCUSIGN_ACCOUNT_ID").read().strip() if os.path.exists("/run/secrets/DOCUSIGN_ACCOUNT_ID") else os.getenv("DOCUSIGN_ACCOUNT_ID")
        user_id = open("/run/secrets/DOCUSIGN_USER_ID").read().strip() if os.path.exists("/run/secrets/DOCUSIGN_USER_ID") else os.getenv("DOCUSIGN_USER_ID")
        
        # Build callback URL for webhook notifications
        backend_url = os.getenv("BACKEND_URL", "http://backend:5000")
        callback_url = f"{backend_url}/api/devis/docusign/webhook"

        # Prepare files and data for the external service
        files = {'file': (file.filename, file.read(), file.content_type)}
        data = {
            'integrator_key': integrator_key,
            'account_id': account_id,
            'user_id': user_id,
            'callback_url': callback_url,
            'signers': json.dumps([{
                'email': email,
                'name': f"{prenom} {nom}"
            }])
        }
            

        # Make the POST request to the external service
        target_url = os.getenv("DOCUSIGN_SERVER_IP") + "/send-pdf"
        response = requests.post(target_url, files=files, data=data)
        response.raise_for_status()
        
        response_data = response.json()
        envelope_id = response_data.get('envelope_id')
        
        # Store envelope_id in the devis and update status
        if envelope_id:
            devis.envelope_id = envelope_id
            devis.statut = "En attente de signature"
            db.session.commit()
            logging.info(f"Devis {devis_id} envoyé pour signature. Envelope ID: {envelope_id}")
        
        logging.info(response_data)
        
        # Return the JSON response from the external service
        return jsonify(response_data), response.status_code
    
    except requests.exceptions.RequestException as e:
        logging.exception(f"Erreur lors de l'appel au service externe: {e}")
        return jsonify({"error": f"Erreur lors de l'appel au service externe: {e}"}), 500
    
    except Exception as e:
        logging.exception("Erreur lors de l'envoi du PDF via le service externe:")
        return jsonify({"error": str(e)}), 500

# Webhook endpoint to receive DocuSign status updates
@devis_bp.route('/docusign/webhook', methods=['POST'])
def docusign_webhook():
    """
    Receive webhook notifications from the external DocuSign server
    when envelope status changes (completed, declined, voided)
    """
    try:
        data = request.get_json()
        
        if not data:
            logging.error("Webhook reçu sans données")
            return jsonify({"error": "No data received"}), 400
        
        envelope_id = data.get('envelope_id')
        status = data.get('status')
        signed_at = data.get('signed_at')
        
        if not envelope_id or not status:
            logging.error(f"Webhook incomplet: {data}")
            return jsonify({"error": "Missing envelope_id or status"}), 400
        
        # Find the devis with this envelope_id
        devis = Devis.query.filter_by(envelope_id=envelope_id).first()
        
        if not devis:
            logging.warning(f"Devis non trouvé pour envelope_id: {envelope_id}")
            return jsonify({"error": "Devis not found"}), 404
        
        # Update devis status based on DocuSign status
        if status == "completed":
            devis.statut = "Signé"
            if signed_at:
                try:
                    devis.date_paiement = datetime.fromisoformat(signed_at.replace('Z', '+00:00')).date()
                except:
                    devis.date_paiement = datetime.now().date()
            else:
                devis.date_paiement = datetime.now().date()
            logging.info(f"Devis {devis.id} ({devis.titre}) marqué comme Signé via webhook DocuSign")
            
        elif status == "declined":
            devis.statut = "Refusé"
            logging.info(f"Devis {devis.id} ({devis.titre}) marqué comme Refusé via webhook DocuSign")
            
        elif status == "voided":
            devis.statut = "Annulé"
            logging.info(f"Devis {devis.id} ({devis.titre}) marqué comme Annulé via webhook DocuSign")
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "devis_id": devis.id,
            "new_status": devis.statut
        }), 200
        
    except Exception as e:
        logging.exception(f"Erreur lors du traitement du webhook DocuSign: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500