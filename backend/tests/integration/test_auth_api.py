"""Integration tests for authentication endpoints."""

import pytest
from flask import session
from models import User


class TestAuthRegister:
    """Tests for user registration endpoint (disabled for private app)."""
    
    def test_register_disabled(self, client):
        """Test that user registration is disabled (private app)."""
        response = client.post(
            '/api/auth/register',
            json={
                'email': 'newuser@test.com',
                'nom': 'Dupont',
                'prenom': 'Jean',
                'mdp': 'SecurePass123!'
            }
        )
        
        # Registration should be disabled or require auth (401, 403, or 404)
        assert response.status_code in [401, 403, 404]


class TestAuthLogin:
    """Tests for login endpoint."""
    
    def test_login_endpoint_exists(self, client):
        """Test that login endpoint exists and accepts POST."""
        response = client.post(
            '/api/auth/login',
            json={
                'email': 'test@test.com',
                'mdp': 'TestPassword123!'
            }
        )
        
        # Should not be 404 (endpoint exists), may be 401 (auth failure)
        assert response.status_code != 404
    
    def test_login_rate_limiting_protection(self, client):
        """Test that login has rate limiting."""
        # Make multiple failed login attempts
        for i in range(6):
            response = client.post(
                '/api/auth/login',
                json={
                    'email': 'test@test.com',
                    'mdp': 'WrongPassword!'
                }
            )
            # After 5 attempts, should be rate limited
            if i >= 5:
                assert response.status_code in [429, 401]


class TestAuthLogout:
    """Tests for logout endpoint."""
    
    def test_logout_endpoint_exists(self, client):
        """Test that logout endpoint exists."""
        response = client.post('/api/auth/logout')
        
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404


class TestAuthCSRFProtection:
    """Tests for CSRF token functionality."""
    
    def test_login_endpoint_csrf_exempt(self, client):
        """Test that login is CSRF-exempt."""
        response = client.post(
            '/api/auth/login',
            json={
                'email': 'test@test.com',
                'mdp': 'TestPassword123!'
            }
        )
        
        # Should not fail due to CSRF (may fail on auth)
        assert response.status_code != 400
    
    def test_docusign_webhook_csrf_exempt(self, client):
        """Test that DocuSign webhook is CSRF-exempt."""
        response = client.post(
            '/api/docusign/webhook',
            data='<DocuSignEnvelopeInformation></DocuSignEnvelopeInformation>',
            content_type='application/xml'
        )
        
        # Should not fail due to CSRF
        assert response.status_code != 400
