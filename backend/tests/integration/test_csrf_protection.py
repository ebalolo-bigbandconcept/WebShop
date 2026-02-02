"""Integration tests for CSRF protection."""


class TestCSRFProtection:
    """Tests for CSRF token validation on state-changing operations."""

    def test_safe_methods_no_csrf_required(self, client):
        """Test that GET requests don't require CSRF token."""
        response = client.get("/api/devis/all")

        # GET should not fail on CSRF (may need auth)
        assert response.status_code != 400

    def test_login_endpoint_csrf_exempt(self, client):
        """Test that login endpoint is CSRF-exempt."""
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "mdp": "SomePassword123!"},
        )

        # Should not fail on CSRF (may fail on auth, but not CSRF)
        assert response.status_code != 400

    def test_docusign_webhook_csrf_exempt(self, client):
        """Test that DocuSign webhook is CSRF-exempt."""
        response = client.post(
            "/api/docusign/webhook",
            data="<DocuSignEnvelopeInformation></DocuSignEnvelopeInformation>",
            content_type="application/xml",
        )

        # Should not fail on CSRF (may fail on validation, but not CSRF)
        assert response.status_code != 400


class TestRBACProtection:
    """Tests for role-based access control."""

    def test_devis_requires_login(self, client):
        """Test that devis endpoints require login."""
        response = client.get("/api/devis/all")

        # Should require authentication
        assert response.status_code == 401

    def test_admin_endpoints_are_protected(self, client):
        """Test that admin endpoints are protected."""
        response = client.get("/api/admin/all-user")

        # Should require authentication (401 or 403)
        assert response.status_code in [401, 403]
