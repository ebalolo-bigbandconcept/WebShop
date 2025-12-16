from flask import Blueprint, request, jsonify, session, render_template, make_response, redirect
from models import db, Devis, DevisSchema, DevisArticles, Clients
from datetime import datetime
from weasyprint import HTML
from docusign_esign import ApiClient, EnvelopesApi, EnvelopeDefinition, Document, Signer, SignHere, Tabs, Recipients, ApiClient
from docusign_esign.client.api_exception import ApiException
import logging, os, requests, json

# Create a Blueprint for authentication-related routes
devis_bp = Blueprint('devis_bp', __name__, url_prefix='/api/devis')

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
    
    # Convert Devis object to dict including articles
    devis_schema = DevisSchema()
    devis_data = devis_schema.dump(devis)

    # Render HTML using Jinja2 template
    html_out = render_template("pdf.html", devis=devis_data)
    
    # Calculate the absolute path to the folder containing your template and static files
    base_path = '/app/pdf/'

    # Generate PDF
    pdf = HTML(string=html_out,base_url=base_path).write_pdf()

    # Return PDF as response
    response = make_response(pdf)
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