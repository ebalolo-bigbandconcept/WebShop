from flask import Blueprint, request, jsonify, session, render_template, make_response, redirect
from models import db, Devis, DevisSchema, DevisArticles, Clients
from datetime import datetime
from weasyprint import HTML
from docusign_esign import ApiClient, EnvelopesApi, EnvelopeDefinition, Document, Signer, SignHere, Tabs, Recipients, ApiClient
from docusign_esign.client.api_exception import ApiException
import logging, os, base64, time, requests

# Docusign credentials
DOCUSIGN_BASE_PATH = "https://demo.docusign.net/restapi" # Only for dev
DOCUSIGN_ACCOUNT_ID = os.getenv("DOCUSIGN_ACCOUNT_ID")
DOCUSIGN_ACCESS_TOKEN = os.getenv("DOCUSIGN_ACCOUNT_TOKEN")

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

# Cache the token globally so we don’t request it every time
DOCUSIGN_TOKEN_CACHE = {
    "access_token": None,
    "expires_at": 0
}

def get_docusign_token():
    # Reuse cached token if valid
    if DOCUSIGN_TOKEN_CACHE["access_token"] and DOCUSIGN_TOKEN_CACHE["expires_at"] > time.time():
        return DOCUSIGN_TOKEN_CACHE["access_token"]
    
    private_key_path = os.getenv("DOCUSIGN_PRIVATE_KEY_PATH")
    with open(private_key_path, "r") as key_file:
        private_key = key_file.read()

    integration_key = os.getenv("DOCUSIGN_INTEGRATION_KEY")
    user_id = os.getenv("DOCUSIGN_USER_ID")
    auth_server = os.getenv("DOCUSIGN_AUTH_SERVER")

    api_client = ApiClient()
    api_client.set_oauth_host_name(auth_server.replace("https://", ""))

    try:
        token_response = api_client.request_jwt_user_token(
            client_id=integration_key,
            user_id=user_id,
            oauth_host_name=auth_server.replace("https://", ""),
            private_key_bytes=private_key.encode("utf-8"),
            expires_in=3600,
            scopes=["signature", "impersonation"]
        )
        access_token = token_response.access_token
        
        logging.info("Nouveau token JWT DocuSign obtenu.")
        return access_token
    except ApiException as e:
        logging.error("Erreur lors de l'obtention du token JWT: %s", e)
        raise e

# Send PDF for sign by email
@devis_bp.route('/pdf/send/<client_id>', methods=['POST'])
def send_pdf_sign(client_id):
    try:
        file = request.files['file']
        client = Clients.query.filter_by(id=client_id).first()
        if not client:
            return jsonify({"error": "Client non trouvé."}), 404
        
        signer_email = client.email
        signer_nom = client.nom
        signer_prenom = client.prenom
        
        # Convert PDF to base64
        file_content = base64.b64encode(file.read()).decode('utf-8')
        
        # Create DocuSign document
        document = Document(
            document_base64=file_content,
            name='Devis à signer',
            file_extension='pdf',
            document_id='1'
        )
        
        # Create signer and tabs
        sign_here = SignHere(anchor_string='SIGN_HERE', anchor_units='pixels', anchor_x_offset='100', anchor_y_offset='100')
        tabs = Tabs(sign_here_tabs=[sign_here])
        signer = Signer(email=signer_email, name=f"{signer_nom} {signer_prenom}", recipient_id='1', routing_order='1', tabs=tabs)

        recipients = Recipients(signers=[signer])

        # Create envelope definition
        envelope_definition = EnvelopeDefinition(
            email_subject='Please sign this document',
            documents=[document],
            recipients=recipients,
            status='sent'
        )
        
        # Get JWT access token
        access_token = get_docusign_token()
        account_id = os.getenv("DOCUSIGN_ACCOUNT_ID")
        base_path = os.getenv("DOCUSIGN_BASE_PATH", "https://demo.docusign.net/restapi")

        # Use the DocuSign API client
        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header("Authorization", f"Bearer {access_token}")

        envelope_api = EnvelopesApi(api_client)
        results = envelope_api.create_envelope(account_id, envelope_definition=envelope_definition)
        
        logging.info(f"Envelope envoyé avec ID: {results.envelope_id}")
        return jsonify({'envelope_id': results.envelope_id}), 200
    except ApiException as e:
        if "consent_required" in str(e):
            return jsonify({"error": "consent_required"}), 403
        logging.exception("Erreur lors de l'envoi du PDF à DocuSign:")
        return jsonify({"error": str(e)}), 500

# Send PDF to external service for signing
@devis_bp.route('/pdf/send/external/<client_id>', methods=['POST'])
def external_send_pdf_sign(client_id):
    try:
        file = request.files['file']
        client = Clients.query.filter_by(id=client_id).first()
        if not client:
            return jsonify({"error": "Client non trouvé."}), 404
        
        email = client.email
        nom = client.nom
        prenom = client.prenom
        
        # Read private key content from path
        private_key_path = os.getenv("DOCUSIGN_PRIVATE_KEY_PATH")
        with open(private_key_path, "r") as key_file:
            private_key_content = key_file.read()

        # Get other Docusign credentials from environment variables
        integrator_key = os.getenv("DOCUSIGN_INTEGRATION_KEY")
        account_id = os.getenv("DOCUSIGN_ACCOUNT_ID")
        user_id = os.getenv("DOCUSIGN_USER_ID")

        # Prepare files and data for the external service
        files = {'file': (file.filename, file.read(), file.content_type)}
        data = {
            'integrator_key': integrator_key,
            'account_id': account_id,
            'user_id': user_id,
            'private_key': private_key_content,
            'email': email,
            'name': f"{nom} {prenom}"
        }

        # Make the POST request to the external service
        target_url = "http://172.20.0.2:5001/api/send-pdf"
        response = requests.post(target_url,files=files,data=data)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        logging.info(response)
        
        # Return the JSON response from the external service
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.RequestException as e:
        logging.exception(f"Erreur lors de l'appel au service externe: {e}")
        return jsonify({"error": f"Erreur lors de l'appel au service externe: {e}"}), 500
    
    except Exception as e:
        logging.exception("Erreur lors de l'envoi du PDF via le service externe:")
        return jsonify({"error": str(e)}), 500

