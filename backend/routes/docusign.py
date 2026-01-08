"""
DocuSign Routes
Handles sending PDFs for signing and receiving webhook notifications
"""

from flask import Blueprint, request, jsonify
import logging
import xml.etree.ElementTree as ET
import os
import json
from services.docusign_service import (
    send_envelope_for_signing,
    handle_webhook,
    get_envelope_status,
    list_all_envelopes
)
from models import db, Clients, Devis

docusign_bp = Blueprint('docusign', __name__, url_prefix='/api/docusign')
logger = logging.getLogger(__name__)


@docusign_bp.route('/send-pdf', methods=['POST'])
def send_pdf():
    """
    Send PDF for signing via DocuSign
    
    Expected form data:
    - file: PDF file
    - integrator_key: DocuSign Integration Key
    - account_id: DocuSign Account ID
    - user_id: DocuSign User ID
    - signers: JSON string with signer info [{email, name}, ...]
    - callback_url: (optional) URL to notify on completion
    """
    try:
        # Fetching data
        data = request.form
        logger.info("Received data for PDF signing")

        # Get required fields
        integrator_key = data.get("integrator_key")
        account_id = data.get("account_id")
        user_id = data.get("user_id")
        signers = data.get("signers")
        callback_url = data.get("callback_url")

        # Validate required fields
        if not all([integrator_key, account_id, user_id, signers]):
            return jsonify({
                "error": "Missing required fields: integrator_key, account_id, user_id, signers"
            }), 400

        # Get PDF file
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "Missing PDF file"}), 400

        logger.info("Received file for signing")

        # Get requester host from request headers
        requester_host = request.headers.get('X-Forwarded-For', request.remote_addr)
        if 'Origin' in request.headers:
            requester_host = request.headers.get('Origin')
        elif 'Referer' in request.headers:
            requester_host = request.headers.get('Referer')

        # Send envelope for signing
        result = send_envelope_for_signing(
            pdf_bytes=file.read(),
            signers_data=signers,
            integrator_key=integrator_key,
            account_id=account_id,
            user_id=user_id,
            callback_url=callback_url,
            requester_host=requester_host,
            filename=file.filename or "Document à signer"
        )

        logger.info(f"Successfully sent envelope: {result['envelope_id']}")
        return jsonify(result), 200

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Error sending PDF: {e}")
        return jsonify({"error": str(e)}), 500


@docusign_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle DocuSign webhook notifications
    
    Receives envelope status changes:
    - completed: Document was signed
    - declined: Signer declined to sign
    - voided: Envelope was voided
    
    Supports both XML (native DocuSign format) and JSON payloads
    """
    try:
        content_type = request.headers.get('Content-Type', '')
        data = None

        if 'json' in content_type:
            data = request.get_json()
        else:
            # DocuSign typically sends XML
            xml_data = request.data.decode('utf-8')
            logger.info(f"Received webhook XML: {xml_data[:500]}")

            root = ET.fromstring(xml_data)

            # Parse envelope ID and status from XML
            envelope_id = None
            status = None

            # Find EnvelopeStatus node
            for envelope_status in root.findall('.//EnvelopeStatus'):
                envelope_id_elem = envelope_status.find('EnvelopeID')
                status_elem = envelope_status.find('Status')

                if envelope_id_elem is not None:
                    envelope_id = envelope_id_elem.text
                if status_elem is not None:
                    status = status_elem.text.lower()

            if not envelope_id:
                logger.warning("No envelope ID found in webhook")
                return jsonify({"status": "ignored", "reason": "no envelope ID"}), 200

            data = {
                "envelope_id": envelope_id,
                "status": status
            }

        # Handle the webhook
        response_data, status_code = handle_webhook(data)
        return jsonify(response_data), status_code

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return jsonify({"error": str(e)}), 500


@docusign_bp.route('/envelope/<envelope_id>/status', methods=['GET'])
def get_status(envelope_id):
    """
    Get the status of a specific envelope
    
    Args:
        envelope_id: DocuSign envelope ID
    """
    response_data, status_code = get_envelope_status(envelope_id)
    return jsonify(response_data), status_code


@docusign_bp.route('/envelopes', methods=['GET'])
def list_envelopes():
    """
    List all tracked envelopes with their status
    """
    envelopes, status_code = list_all_envelopes()
    if status_code == 200:
        return jsonify(envelopes), status_code
    else:
        return jsonify(envelopes), status_code


@docusign_bp.route('/send/<client_id>/<devis_id>', methods=['POST'])
def send_pdf_sign(client_id, devis_id):
    """
    Send PDF for signing via DocuSign
    Integrated endpoint for sending devis PDFs to clients
    """
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        client = Clients.query.filter_by(id=client_id).first()
        if not client:
            return jsonify({"error": "Client non trouvé."}), 404
        
        devis = Devis.query.filter_by(id=devis_id).first()
        if not devis:
            return jsonify({"error": "Devis non trouvé."}), 404
        
        email = client.email
        nom = client.nom
        prenom = client.prenom

        # Get DocuSign credentials from environment variables or Docker secrets
        integrator_key = open("/run/secrets/DOCUSIGN_INTEGRATION_KEY").read().strip() if os.path.exists("/run/secrets/DOCUSIGN_INTEGRATION_KEY") else os.getenv("DOCUSIGN_INTEGRATION_KEY")
        account_id = open("/run/secrets/DOCUSIGN_ACCOUNT_ID").read().strip() if os.path.exists("/run/secrets/DOCUSIGN_ACCOUNT_ID") else os.getenv("DOCUSIGN_ACCOUNT_ID")
        user_id = open("/run/secrets/DOCUSIGN_USER_ID").read().strip() if os.path.exists("/run/secrets/DOCUSIGN_USER_ID") else os.getenv("DOCUSIGN_USER_ID")

        if not all([integrator_key, account_id, user_id]):
            return jsonify({"error": "DocuSign credentials not configured"}), 500

        # Use integrated DocuSign service
        result = send_envelope_for_signing(
            pdf_bytes=file.read(),
            signers_data=json.dumps([{
                'email': email,
                'name': f"{prenom} {nom}"
            }]),
            integrator_key=integrator_key,
            account_id=account_id,
            user_id=user_id,
            callback_url=None,  # Webhook is internal now
            requester_host=request.headers.get('Origin', request.remote_addr),
            filename=file.filename or "devis.pdf",
            devis_id=devis_id  # Pass devis_id for auto-update
        )
        
        envelope_id = result.get('envelope_id')
        
        # Store envelope_id in the devis and update status
        if envelope_id:
            devis.envelope_id = envelope_id
            devis.statut = "En attente de signature"
            db.session.commit()
            logger.info(f"Devis {devis_id} envoyé pour signature. Envelope ID: {envelope_id}")
        
        return jsonify(result), 200
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        logger.exception("Erreur lors de l'envoi du PDF pour signature:")
        return jsonify({"error": str(e)}), 500
