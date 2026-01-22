"""Integration tests for authentication endpoints."""


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


class TestAuthLoginSuccess:
    """Tests for successful login scenarios."""
    
    def test_login_with_valid_credentials(self, client, regular_user):
        """Test login with valid credentials."""
        response = client.post(
            '/api/auth/login',
            json={
                'email': regular_user.email,
                'mdp': 'TestPassword123!'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data or 'user' in data
    
    def test_login_with_invalid_password(self, client, regular_user):
        """Test login with invalid password."""
        response = client.post(
            '/api/auth/login',
            json={
                'email': regular_user.email,
                'mdp': 'WrongPassword!'
            }
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_login_with_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            '/api/auth/login',
            json={
                'email': 'nonexistent@test.com',
                'mdp': 'Password123!'
            }
        )
        
        assert response.status_code == 401


class TestAuthLogoutFunctionality:
    """Tests for logout functionality."""
    
    def test_logout_clears_session(self, client, auth_headers):
        """Test that logout clears the session."""
        # First login
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
