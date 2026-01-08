"""
DocuSign eSign API Service Module
Handles PDF signing via DocuSign with JWT authentication
"""

from flask import request, jsonify
from docusign_esign import ApiClient, ApiException, EnvelopesApi, EventNotification
from docusign_esign.models import Document, EnvelopeDefinition, Signer, SignHere, Tabs, Recipients, EnvelopeEvent
import base64
import time
import logging
import os
import json
import requests
import timezone
from datetime import datetime
from models import db, EnvelopeTracking, Devis, DevisArticles, Parameters, TauxTVA

logger = logging.getLogger(__name__)

# Token caching
_CACHED_PRIVATE_KEY = None
DOCUSIGN_TOKEN_CACHE = {
    "access_token": None,
    "expires_at": 0
}


def load_private_key():
    """Load and cache DocuSign private key from file"""
    global _CACHED_PRIVATE_KEY
    if _CACHED_PRIVATE_KEY:
        return _CACHED_PRIVATE_KEY

    private_key_path = os.getenv("DOCUSIGN_PRIVATE_KEY_PATH")
    if not private_key_path:
        raise ValueError("DOCUSIGN_PRIVATE_KEY_PATH environment variable is not set")

    if not os.path.isfile(private_key_path):
        raise FileNotFoundError(f"Private key file not found at path: {private_key_path}")

    # Read as bytes and decode to text (PEM keys are textual). Cache as string.
    with open(private_key_path, "rb") as f:
        _CACHED_PRIVATE_KEY = f.read().decode("utf-8")
    
    logger.info("Loaded DocuSign private key")
    return _CACHED_PRIVATE_KEY


def get_docusign_token(integrator_key, user_id):
    """
    Get DocuSign JWT access token with caching.
    
    Args:
        integrator_key: DocuSign Integration Key (Client ID)
        user_id: DocuSign User ID
        
    Returns:
        access_token: JWT token for API calls
    """
    # If cached token is still valid then reuse it
    if DOCUSIGN_TOKEN_CACHE["access_token"] and DOCUSIGN_TOKEN_CACHE["expires_at"] > time.time():
        logger.info("Using cached DocuSign JWT token")
        return DOCUSIGN_TOKEN_CACHE["access_token"]

    private_key = load_private_key()
    docusign_env = os.getenv("DOCUSIGN_ENV", "demo")
    auth_server = "account-d.docusign.com" if docusign_env == "demo" else "account.docusign.com"

    logger.info("Requesting new DocuSign JWT token")

    api_client = ApiClient()
    api_client.set_oauth_host_name(auth_server)

    try:
        token_response = api_client.request_jwt_user_token(
            client_id=integrator_key,
            user_id=user_id,
            oauth_host_name=auth_server,
            private_key_bytes=private_key.encode("utf-8"),
            expires_in=3600,
            scopes=["signature", "impersonation"]
        )

        access_token = token_response.access_token

        # Store token in cache
        DOCUSIGN_TOKEN_CACHE["access_token"] = access_token
        DOCUSIGN_TOKEN_CACHE["expires_at"] = time.time() + 3500

        logger.info("New DocuSign JWT token created and cached")
        return access_token

    except ApiException as e:
        logger.error(f"DocuSign JWT error: {e}")
        raise e


def prepare_document(pdf_bytes, filename="Document à signer"):
    """
    Prepare a PDF document for DocuSign signing.
    
    Args:
        pdf_bytes: PDF file bytes
        filename: Name of the document
        
    Returns:
        Document: DocuSign Document object
    """
    # Convert PDF to Base64
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    document = Document(
        document_base64=pdf_base64,
        name=filename,
        file_extension="pdf",
        document_id="1"
    )

    logger.info("Prepared document for DocuSign")
    return document


def get_sign_here_tab(anchor_x_offset="100", anchor_y_offset="100"):
    """
    Create a SignHere tab for document signing.
    
    Args:
        anchor_x_offset: X pixel offset for signature placement
        anchor_y_offset: Y pixel offset for signature placement
        
    Returns:
        SignHere: DocuSign SignHere tab object
    """
    sign_here = SignHere(
        anchor_string="SIGN_HERE",
        anchor_units="pixels",
        anchor_x_offset=anchor_x_offset,
        anchor_y_offset=anchor_y_offset
    )
    
    logger.info("Prepared sign here tab for DocuSign")
    return sign_here


def get_signers(signers_data, sign_here):
    """
    Create signer objects from provided data.
    
    Args:
        signers_data: JSON string or list of signer info with 'email' and 'name'
        sign_here: SignHere tab to apply to all signers
        
    Returns:
        signers: List of DocuSign Signer objects
    """
    # Format signers into json
    try:
        if isinstance(signers_data, str):
            if not signers_data.strip().startswith('['):
                signers_data = f'[{signers_data}]'
            signers_data = json.loads(signers_data)
        
        if not isinstance(signers_data, list):
            signers_data = [signers_data]

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode signers JSON string: {signers_data}")
        raise ValueError("Invalid signers format. Must be valid JSON string.")
    
    # Create every signer
    signers = []
    for i, signer_info in enumerate(signers_data):
        recipient_id = str(i + 1)

        email = signer_info.get("email")
        name = signer_info.get("name")

        if not email or not name:
            raise ValueError(f"Signer {i} missing required fields: email and name")

        signer = Signer(
            email=email,
            name=name,
            recipient_id=recipient_id,
            routing_order=1,
        )
        
        signer.tabs = Tabs(
            sign_here_tabs=[sign_here]
        )
        
        signers.append(signer)
        logger.info(f"Added signer {i}: {name} <{email}>")
    
    logger.info(f"Total signers added: {len(signers)}")
    return signers


def get_envelope_definition(document, recipients, webhook_url):
    """
    Create envelope definition with webhook notification.
    
    Args:
        document: DocuSign Document object
        recipients: DocuSign Recipients object with signers
        webhook_url: URL for webhook notifications
        
    Returns:
        EnvelopeDefinition: Configured envelope definition
    """
    # Webhook enabled - requires HTTPS backend
    event_notification = EventNotification(
        url=webhook_url,
        logging_enabled="true",
        require_acknowledgment="true",
        use_soap_interface="false",
        include_certificate_with_soap="false",
        sign_message_with_x509_cert="false",
        include_documents="true",
        include_envelope_void_reason="true",
        include_time_zone="true",
        include_sender_account_as_custom_field="true",
        include_document_fields="true",
        include_certificate_of_completion="true",
        envelope_events=[
            EnvelopeEvent(envelope_event_status_code="completed"),
            EnvelopeEvent(envelope_event_status_code="declined"),
            EnvelopeEvent(envelope_event_status_code="voided")
        ]
    )
    
    envelope_definition = EnvelopeDefinition(
        email_subject="Veuillez signer le document",
        documents=[document],
        recipients=recipients,
        status="sent",
        event_notification=event_notification
    )
    
    logger.info("Prepared envelope definition for DocuSign")
    return envelope_definition


def send_envelope_for_signing(pdf_bytes, signers_data, integrator_key, account_id, user_id, 
                             callback_url=None, requester_host=None, filename="Document à signer", devis_id=None):
    """
    Send a PDF for signing via DocuSign.
    
    Args:
        pdf_bytes: PDF file bytes
        signers_data: JSON string or list of signer info
        integrator_key: DocuSign Integration Key
        account_id: DocuSign Account ID
        user_id: DocuSign User ID
        callback_url: URL to notify when signing completes
        requester_host: Origin of the request
        filename: Name of the document
        devis_id: ID of the devis being signed (for auto-update)
        
    Returns:
        dict: Response containing envelope_id, webhook_url, tracking_id
    """
    try:
        # Prepare document and signers
        document = prepare_document(pdf_bytes, filename)
        sign_here = get_sign_here_tab()
        signers = get_signers(signers_data, sign_here)
        recipients = Recipients(signers=signers)
        
        # Get the webhook URL for DocuSign to call our API
        backend_url = os.getenv("BACKEND_URL", "http://localhost:5000")
        webhook_url = f"{backend_url}/api/docusign/webhook"
        
        envelope_definition = get_envelope_definition(document, recipients, webhook_url)

        # Get DocuSign token
        access_token = get_docusign_token(integrator_key, user_id)

        # Determine API endpoint
        docusign_env = os.getenv("DOCUSIGN_ENV", "demo")
        base_path = "https://demo.docusign.net/restapi" if docusign_env == "demo" else "https://www.docusign.net/restapi"

        logger.info("Sending envelope to DocuSign...")

        # Create API client and send envelope
        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header("Authorization", f"Bearer {access_token}")

        envelope_api = EnvelopesApi(api_client)
        results = envelope_api.create_envelope(account_id, envelope_definition=envelope_definition)

        logger.info(f"Envelope sent with ID: {results.envelope_id}")

        # Store envelope tracking information in database
        tracking = None
        try:
            tracking = EnvelopeTracking(
                envelope_id=results.envelope_id,
                devis_id=devis_id,
                callback_url=callback_url,
                requester_host=requester_host,
                status='sent'
            )
            db.session.add(tracking)
            db.session.commit()
            logger.info(f"Stored tracking info for envelope {results.envelope_id} (devis_id={devis_id})")
        except Exception as db_error:
            logger.error(f"Failed to store tracking info: {db_error}")
            db.session.rollback()

        return {
            "envelope_id": results.envelope_id,
            "webhook_url": webhook_url,
            "tracking_id": tracking.id if tracking else None
        }

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise e
    except ApiException as e:
        logger.error(f"DocuSign API error: {e}")
        raise e


def create_devis_signed_snapshot(devis):
    """
    Create a signed_data snapshot for a devis, capturing its current state.
    Similar logic to the update_devis endpoint.
    
    Args:
        devis: Devis model instance
        
    Returns:
        dict: Snapshot data to store in signed_data field
    """
    try:
        params = Parameters.query.first()
        remise_value = float(devis.remise or 0.0)
        
        snapshot_lines = []
        total_ht = 0.0
        total_tva = 0.0
        total_ttc = 0.0
        
        # Recalculate based on current articles
        for article in devis.articles:
            article_obj = article.article if article.article else None
            
            # Get unit price
            unit_price = 0.0
            if article_obj:
                unit_price = float(article_obj.prix_vente_HT or 0.0)
            
            # Get VAT rate
            taux_val = 0.0
            if article.taux_tva:
                taux_val = float(article.taux_tva.taux)
            elif article_obj and article_obj.taux_tva:
                taux_val = float(article_obj.taux_tva.taux)
            
            qty = float(article.quantite)
            line_ht = unit_price * qty
            line_tva = line_ht * (taux_val or 0.0)
            line_ttc = line_ht + line_tva
            
            total_ht += line_ht
            total_tva += line_tva
            total_ttc += line_ttc
            
            snapshot_lines.append({
                "article_id": article_obj.id if article_obj else article.article_id,
                "nom": getattr(article_obj, "nom", ""),
                "reference": getattr(article_obj, "reference", ""),
                "quantite": qty,
                "taux_tva": taux_val,
                "prix_unitaire_ht": unit_price,
                "montant_ht": line_ht,
                "montant_tva": line_tva,
                "montant_ttc": line_ttc,
                "commentaire": article.commentaire or "",
            })
        
        return {
            "lines": snapshot_lines,
            "totals": {
                "ht": round(total_ht, 2),
                "tva": round(total_tva, 2),
                "ttc": round(total_ttc, 2),
                "ttc_after_remise": round(max(total_ttc - remise_value, 0.0), 2),
            },
            "remise": round(remise_value, 2),
            "params": {
                "margin_rate": params.margin_rate if params else 0.0,
                "margin_rate_location": params.margin_rate_location if params else 0.0,
                "location_subscription_cost": params.location_subscription_cost if params else 0.0,
                "location_interests_cost": params.location_interests_cost if params else 0.0,
                "location_time": params.location_time if params else 0,
                "general_conditions_sales": params.general_conditions_sales if params else "",
            },
            "company": {
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
            },
            "location": {
                "is_location": devis.is_location,
                "first_contribution_amount": devis.first_contribution_amount,
                "location_monthly_total": devis.location_monthly_total,
                "location_monthly_total_ht": devis.location_monthly_total_ht,
                "location_total": devis.location_total,
                "location_total_ht": devis.location_total_ht,
            },
        }
    except Exception as e:
        logger.error(f"Error creating signed snapshot: {e}")
        raise e


def notify_external_site(envelope_id, status, tracking):
    """Send notification to external site about envelope status"""
    try:
        payload = {
            "envelope_id": envelope_id,
            "status": status,
            "requester_host": tracking.requester_host,
            "signed_at": tracking.signed_at.isoformat() if tracking.signed_at else None,
            "created_at": tracking.created_at.isoformat() if tracking.created_at else None
        }
        
        logger.info(f"Notifying {tracking.callback_url} about envelope {envelope_id}")
        
        response = requests.post(
            tracking.callback_url,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        tracking.notified_at = datetime.now(timezone.utc)
        tracking.notification_status = f"success_{response.status_code}"
        db.session.commit()
        
        logger.info(f"Successfully notified {tracking.callback_url} - Status: {response.status_code}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to notify {tracking.callback_url}: {e}")
        tracking.notification_status = f"failed_{str(e)[:100]}"
        db.session.commit()
        return False


def handle_webhook(data):
    """
    Handle DocuSign webhook event.
    
    Args:
        data: dict with envelope_id and status
        
    Returns:
        tuple: (dict response, status_code)
    """
    try:
        envelope_id = data.get("envelope_id") or data.get("envelopeId")
        status = data.get("status", "").lower()
        
        logger.info(f"Webhook received for envelope {envelope_id} with status {status}")
        
        # Find the tracking record
        tracking = EnvelopeTracking.query.filter_by(envelope_id=envelope_id).first()
        
        if not tracking:
            logger.warning(f"No tracking record found for envelope {envelope_id}")
            return {"status": "ignored", "reason": "envelope not tracked"}, 200
        
        # Update tracking status
        tracking.status = status
        
        # If envelope is completed (signed), record the timestamp and update devis
        if status == 'completed':
            tracking.signed_at = datetime.now(timezone.utc)
            logger.info(f"Envelope {envelope_id} completed at {tracking.signed_at}")
            
            # Auto-update the devis if devis_id is present
            if tracking.devis_id:
                try:
                    devis = Devis.query.filter_by(id=tracking.devis_id).first()
                    if devis:
                        logger.info(f"Auto-updating devis {tracking.devis_id} to signed status")
                        
                        # Only update if not already signed (idempotency)
                        if devis.statut != "Signé":
                            # Create signed snapshot
                            devis.signed_data = create_devis_signed_snapshot(devis)
                            devis.signed_at = datetime.now(timezone.utc)
                            devis.statut = "Signé"
                            
                            db.session.commit()
                            logger.info(f"Devis {tracking.devis_id} auto-signed via DocuSign webhook")
                        else:
                            logger.warning(f"Devis {tracking.devis_id} was already signed, skipping")
                    else:
                        logger.error(f"Devis {tracking.devis_id} not found")
                except Exception as e:
                    logger.error(f"Error updating devis {tracking.devis_id}: {e}")
                    db.session.rollback()
            
            # Commit tracking update if not already committed
            try:
                db.session.commit()
            except:
                pass
        else:
            db.session.commit()
        
        # Notify the external site if callback URL exists
        if tracking.callback_url and status in ['completed', 'declined', 'voided']:
            notify_external_site(envelope_id, status, tracking)
        
        return {"status": "processed", "envelope_id": envelope_id}, 200
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"error": str(e)}, 500


def get_envelope_status(envelope_id):
    """
    Get the status of an envelope.
    
    Args:
        envelope_id: DocuSign envelope ID
        
    Returns:
        tuple: (dict with envelope data, status_code)
    """
    try:
        tracking = EnvelopeTracking.query.filter_by(envelope_id=envelope_id).first()
        
        if not tracking:
            return {"error": "Envelope not found"}, 404
        
        return tracking.to_dict(), 200
        
    except Exception as e:
        logger.error(f"Error getting envelope status: {e}")
        return {"error": str(e)}, 500


def list_all_envelopes():
    """
    List all tracked envelopes.
    
    Returns:
        tuple: (list of envelopes, status_code)
    """
    try:
        envelopes = EnvelopeTracking.query.order_by(EnvelopeTracking.created_at.desc()).all()
        return [env.to_dict() for env in envelopes], 200
        
    except Exception as e:
        logger.error(f"Error listing envelopes: {e}")
        return {"error": str(e)}, 500
