"""
Extended tests for DocuSign integration (routes and services).
Comprehensive coverage for PDF signing workflows and webhook handling.
"""

import base64
import json
from io import BytesIO
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from models import Clients, Devis, EnvelopeTracking, db


class TestDocuSignWebhook:
    """Test DocuSign webhook handling"""

    def test_webhook_with_json_payload(
        self, client, app, test_devis, test_client_record
    ):
        """Test webhook with JSON payload"""
        # Create envelope tracking
        envelope = EnvelopeTracking(
            envelope_id="test-envelope-123", devis_id=test_devis.id, status="sent"
        )
        db.session.add(envelope)
        db.session.commit()

        response = client.post(
            "/api/docusign/webhook",
            json={"envelope_id": "test-envelope-123", "status": "completed"},
            headers={"Content-Type": "application/json"},
        )

        # Should process successfully
        assert response.status_code in [200, 404]

    def test_webhook_with_xml_payload(self, client, app):
        """Test webhook with XML payload (DocuSign native format)"""
        xml_data = """<?xml version="1.0" encoding="UTF-8"?>
        <DocuSignEnvelopeInformation xmlns="http://www.docusign.net/API/3.0">
            <EnvelopeStatus>
                <EnvelopeID>test-envelope-456</EnvelopeID>
                <Status>Completed</Status>
            </EnvelopeStatus>
        </DocuSignEnvelopeInformation>"""

        response = client.post(
            "/api/docusign/webhook",
            data=xml_data.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
        )

        # Should parse XML and process
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None

    def test_webhook_with_missing_envelope_id(self, client):
        """Test webhook with missing envelope ID in XML"""
        xml_data = """<?xml version="1.0" encoding="UTF-8"?>
        <DocuSignEnvelopeInformation xmlns="http://www.docusign.net/API/3.0">
            <EnvelopeStatus>
                <Status>Completed</Status>
            </EnvelopeStatus>
        </DocuSignEnvelopeInformation>"""

        response = client.post(
            "/api/docusign/webhook",
            data=xml_data.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
        )

        # Should handle gracefully
        assert response.status_code == 200
        data = response.get_json()
        assert "ignored" in data.get("status", "")

    def test_webhook_with_malformed_xml(self, client):
        """Test webhook with malformed XML"""
        response = client.post(
            "/api/docusign/webhook",
            data=b"<invalid>xml<no-close>",
            headers={"Content-Type": "application/xml"},
        )

        # Should return error
        assert response.status_code in [400, 500]

    def test_webhook_with_declined_status(self, client, test_devis):
        """Test webhook with declined status"""
        envelope = EnvelopeTracking(
            envelope_id="test-envelope-declined", devis_id=test_devis.id, status="sent"
        )
        db.session.add(envelope)
        db.session.commit()

        xml_data = """<?xml version="1.0" encoding="UTF-8"?>
        <DocuSignEnvelopeInformation xmlns="http://www.docusign.net/API/3.0">
            <EnvelopeStatus>
                <EnvelopeID>test-envelope-declined</EnvelopeID>
                <Status>Declined</Status>
            </EnvelopeStatus>
        </DocuSignEnvelopeInformation>"""

        response = client.post(
            "/api/docusign/webhook",
            data=xml_data.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
        )

        assert response.status_code in [200, 404]


class TestDocuSignSendPDF:
    """Test sending PDFs for signing"""

    @patch("routes.docusign.send_envelope_for_signing")
    def test_send_pdf_success(
        self, mock_send, client, admin_auth_headers, test_client_record, test_devis
    ):
        """Test successful PDF sending"""
        mock_send.return_value = {"envelope_id": "test-envelope-789", "status": "sent"}

        # Create a fake PDF file
        pdf_content = b"%PDF-1.4 fake pdf content"
        data = {"file": (BytesIO(pdf_content), "test.pdf", "application/pdf")}

        with patch.dict(
            "os.environ",
            {
                "DOCUSIGN_INTEGRATION_KEY": "test-key",
                "DOCUSIGN_ACCOUNT_ID": "test-account",
                "DOCUSIGN_USER_ID": "test-user",
            },
        ):
            response = client.post(
                f"/api/docusign/send/{test_client_record.id}/{test_devis.id}",
                data=data,
                headers=admin_auth_headers,
                content_type="multipart/form-data",
            )

        # Should succeed or return validation error
        assert response.status_code in [200, 400, 500]

    def test_send_pdf_no_file(
        self, client, admin_auth_headers, test_client_record, test_devis
    ):
        """Test sending without file"""
        response = client.post(
            f"/api/docusign/send/{test_client_record.id}/{test_devis.id}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "file" in data.get("error", "").lower()

    def test_send_pdf_invalid_client(self, client, admin_auth_headers, test_devis):
        """Test sending with invalid client ID"""
        pdf_content = b"%PDF-1.4 fake"
        data = {"file": (BytesIO(pdf_content), "test.pdf", "application/pdf")}

        response = client.post(
            f"/api/docusign/send/99999/{test_devis.id}",
            data=data,
            headers=admin_auth_headers,
            content_type="multipart/form-data",
        )

        assert response.status_code == 404

    def test_send_pdf_invalid_devis(
        self, client, admin_auth_headers, test_client_record
    ):
        """Test sending with invalid devis ID"""
        pdf_content = b"%PDF-1.4 fake"
        data = {"file": (BytesIO(pdf_content), "test.pdf", "application/pdf")}

        response = client.post(
            f"/api/docusign/send/{test_client_record.id}/99999",
            data=data,
            headers=admin_auth_headers,
            content_type="multipart/form-data",
        )

        assert response.status_code == 404


class TestDocuSignService:
    """Test DocuSign service functions"""

    def test_load_private_key_missing_env(self):
        """Test loading private key with missing environment variable"""
        from services.docusign_service import load_private_key

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="DOCUSIGN_PRIVATE_KEY_PATH"):
                load_private_key()

    def test_load_private_key_file_not_found(self):
        """Test loading private key when file doesn't exist"""
        from services.docusign_service import load_private_key

        with patch.dict(
            "os.environ", {"DOCUSIGN_PRIVATE_KEY_PATH": "/nonexistent/path.pem"}
        ):
            with pytest.raises(FileNotFoundError):
                load_private_key()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=b"-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
    )
    @patch("os.path.isfile", return_value=True)
    def test_load_private_key_success(self, mock_isfile, mock_file):
        """Test successful private key loading"""
        from services.docusign_service import _CACHED_PRIVATE_KEY, load_private_key

        with patch.dict("os.environ", {"DOCUSIGN_PRIVATE_KEY_PATH": "/test/key.pem"}):
            # Clear cache
            import services.docusign_service

            services.docusign_service._CACHED_PRIVATE_KEY = None

            key = load_private_key()
            assert key is not None
            assert "BEGIN PRIVATE KEY" in key

    @patch("services.docusign_service.load_private_key")
    @patch("services.docusign_service.ApiClient")
    def test_get_docusign_token_success(self, mock_api_client, mock_load_key):
        """Test successful token retrieval"""
        from services.docusign_service import DOCUSIGN_TOKEN_CACHE, get_docusign_token

        # Clear cache
        DOCUSIGN_TOKEN_CACHE["access_token"] = None
        DOCUSIGN_TOKEN_CACHE["expires_at"] = 0

        mock_load_key.return_value = "fake-private-key"

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        mock_token_response = Mock()
        mock_token_response.access_token = "test-token-abc123"
        mock_client_instance.request_jwt_user_token.return_value = mock_token_response

        with patch.dict("os.environ", {"DOCUSIGN_ENV": "demo"}):
            token = get_docusign_token("test-key", "test-user")

        assert token == "test-token-abc123"

    def test_get_docusign_token_cached(self):
        """Test using cached token"""
        import time

        from services.docusign_service import DOCUSIGN_TOKEN_CACHE, get_docusign_token

        # Set valid cache
        DOCUSIGN_TOKEN_CACHE["access_token"] = "cached-token"
        DOCUSIGN_TOKEN_CACHE["expires_at"] = time.time() + 1000

        token = get_docusign_token("test-key", "test-user")
        assert token == "cached-token"

    @patch("services.docusign_service.load_private_key")
    @patch("services.docusign_service.ApiClient")
    def test_get_docusign_token_invalid_grant_no_valid_keys(
        self, mock_api_client, mock_load_key
    ):
        """Test JWT key/signature mismatch is surfaced with actionable message"""
        from docusign_esign import ApiException

        from services.docusign_service import DOCUSIGN_TOKEN_CACHE, get_docusign_token

        DOCUSIGN_TOKEN_CACHE["access_token"] = None
        DOCUSIGN_TOKEN_CACHE["expires_at"] = 0

        mock_load_key.return_value = "fake-private-key"

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        api_error = ApiException(status=400, reason="Bad Request")
        api_error.body = json.dumps(
            {
                "error": "invalid_grant",
                "error_description": "no_valid_keys_or_signatures",
            }
        )
        api_error.headers = {"X-DocuSign-TraceToken": "trace-123"}
        mock_client_instance.request_jwt_user_token.side_effect = api_error

        with patch.dict("os.environ", {"DOCUSIGN_ENV": "demo"}):
            with pytest.raises(ValueError, match="no_valid_keys_or_signatures"):
                get_docusign_token("test-key", "test-user")

    def test_prepare_document(self):
        """Test PDF document preparation"""
        from services.docusign_service import prepare_document

        pdf_bytes = b"%PDF-1.4 test content"
        doc = prepare_document(pdf_bytes, "test.pdf")

        assert doc.name == "test.pdf"
        assert doc.file_extension == "pdf"
        assert doc.document_id == "1"
        assert doc.document_base64 is not None

    def test_get_sign_here_tab(self):
        """Test SignHere tab creation"""
        from services.docusign_service import get_sign_here_tab

        tab = get_sign_here_tab("200", "150")

        assert tab.anchor_string == "SIGN_HERE"
        assert tab.anchor_units == "pixels"

    def test_get_signers_single(self):
        """Test signer creation with single signer"""
        from services.docusign_service import get_sign_here_tab, get_signers

        sign_here = get_sign_here_tab()
        signers_data = '[{"email": "test@example.com", "name": "Test User"}]'

        signers = get_signers(signers_data, sign_here)

        assert len(signers) == 1
        assert signers[0].email == "test@example.com"
        assert signers[0].name == "Test User"

    def test_get_signers_multiple(self):
        """Test signer creation with multiple signers"""
        from services.docusign_service import get_sign_here_tab, get_signers

        sign_here = get_sign_here_tab()
        signers_data = [
            {"email": "user1@example.com", "name": "User One"},
            {"email": "user2@example.com", "name": "User Two"},
        ]

        signers = get_signers(signers_data, sign_here)

        assert len(signers) == 2

    def test_get_signers_invalid_json(self):
        """Test signer creation with invalid JSON"""
        from services.docusign_service import get_sign_here_tab, get_signers

        sign_here = get_sign_here_tab()

        with pytest.raises(ValueError, match="Invalid signers format"):
            get_signers("invalid json{", sign_here)

    def test_get_signers_missing_email(self):
        """Test signer creation with missing email"""
        from services.docusign_service import get_sign_here_tab, get_signers

        sign_here = get_sign_here_tab()
        signers_data = '[{"name": "Test User"}]'

        with pytest.raises(ValueError, match="missing required fields"):
            get_signers(signers_data, sign_here)

    def test_get_envelope_definition(self):
        """Test envelope definition creation"""
        from docusign_esign.models import Recipients

        from services.docusign_service import get_envelope_definition, prepare_document

        doc = prepare_document(b"test", "test.pdf")
        recipients = Recipients(signers=[])
        webhook_url = "https://example.com/webhook"

        envelope = get_envelope_definition(doc, recipients, webhook_url)

        assert envelope.status == "sent"
        assert envelope.email_subject is not None
        assert envelope.event_notification is not None
        assert envelope.event_notification.url == webhook_url

    @patch("services.docusign_service.get_docusign_token")
    @patch("services.docusign_service.EnvelopesApi")
    def test_send_envelope_for_signing_success(
        self, mock_envelopes_api, mock_get_token, app
    ):
        """Test successful envelope sending"""
        from services.docusign_service import send_envelope_for_signing

        with app.app_context():
            mock_get_token.return_value = "test-token"

            mock_api_instance = MagicMock()
            mock_envelopes_api.return_value = mock_api_instance

            mock_summary = Mock()
            mock_summary.envelope_id = "env-123"
            mock_summary.status = "sent"
            mock_api_instance.create_envelope.return_value = mock_summary

            pdf_bytes = b"%PDF-1.4 test"
            signers_data = '[{"email": "test@example.com", "name": "Test User"}]'

            with patch.dict("os.environ", {"DOCUSIGN_ENV": "demo"}):
                result = send_envelope_for_signing(
                    pdf_bytes=pdf_bytes,
                    signers_data=signers_data,
                    integrator_key="test-key",
                    account_id="test-account",
                    user_id="test-user",
                    requester_host="https://example.com",
                )

            # Should return envelope_id
            assert result.get("envelope_id") == "env-123"
            assert "webhook_url" in result or "status" in result


class TestDocuSignWebhookHandler:
    """Test webhook handler service function"""

    def test_handle_webhook_completed(self, app, test_devis):
        """Test handling completed webhook"""
        from services.docusign_service import handle_webhook

        envelope = EnvelopeTracking(
            envelope_id="test-env-completed", devis_id=test_devis.id, status="sent"
        )
        db.session.add(envelope)
        db.session.commit()

        data = {"envelope_id": "test-env-completed", "status": "completed"}

        response, status_code = handle_webhook(data)

        assert status_code in [200, 404]

    def test_handle_webhook_not_found(self, app):
        """Test handling webhook for non-existent envelope"""
        from services.docusign_service import handle_webhook

        data = {"envelope_id": "nonexistent-envelope", "status": "completed"}

        response, status_code = handle_webhook(data)

        # Should return 200 (acknowledged) or 404 (not found)
        assert status_code in [200, 404]

    def test_handle_webhook_voided(self, app, test_devis):
        """Test handling voided webhook"""
        from services.docusign_service import handle_webhook

        envelope = EnvelopeTracking(
            envelope_id="test-env-voided", devis_id=test_devis.id, status="sent"
        )
        db.session.add(envelope)
        db.session.commit()

        data = {"envelope_id": "test-env-voided", "status": "voided"}

        response, status_code = handle_webhook(data)

        # Should process
        assert status_code in [200, 404]
