"""
DocuSign Routes
Handles sending PDFs for signing and receiving webhook notifications
"""

from flask import Blueprint, request, jsonify
import logging
import xml.etree.ElementTree as ET
from services.docusign_service import (
    send_envelope_for_signing,
    handle_webhook,
    get_envelope_status,
    list_all_envelopes
)

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
