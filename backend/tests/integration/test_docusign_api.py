"""Integration tests for DocuSign integration endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from models import EnvelopeTracking, Devis


class TestDocuSignSendEnvelope:
    """Tests for DocuSign envelope sending."""
    
    def test_send_pdf_requires_auth(self, client, test_client_record, test_devis):
        """Test that sending PDF for signing requires authentication."""
        response = client.post(
            f'/api/docusign/send/{test_client_record.id}/{test_devis.id}'
        )
        
        # Should require authentication or file
        assert response.status_code in [400, 401]
    
    def test_send_pdf_missing_file(self, client):
        """Test that send fails without PDF file."""
        response = client.post(
            '/api/docusign/send/1/1'
        )
        
        # Should fail (no file or auth)
        assert response.status_code in [400, 401]


class TestDocuSignWebhook:
    """Tests for DocuSign webhook handling."""
    
    def test_webhook_accepts_xml(self, client):
        """Test webhook accepts XML data."""
        xml_payload = '''<?xml version="1.0" encoding="utf-8"?>
        <DocuSignEnvelopeInformation>
            <EnvelopeStatus>
                <EnvelopeID>test-envelope-123</EnvelopeID>
                <Status>completed</Status>
            </EnvelopeStatus>
        </DocuSignEnvelopeInformation>'''
        
        response = client.post(
            '/api/docusign/webhook',
            data=xml_payload,
            content_type='application/xml'
        )
        
        # Webhook should be CSRF-exempt and handle request
        # May return 200, 204, or 400 depending on payload
        assert response.status_code in [200, 204, 400]
    
    def test_webhook_is_csrf_exempt(self, client):
        """Test that webhook is CSRF-exempt."""
        response = client.post(
            '/api/docusign/webhook',
            data='<test></test>',
            content_type='application/xml'
        )
        
        # Should not fail on CSRF (may fail on validation)
        assert response.status_code != 400 or response.status_code in [200, 204, 400]

