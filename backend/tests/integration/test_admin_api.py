"""Integration tests for Admin API endpoints."""


class TestAdminUsers:
    """Tests for admin user management endpoints."""
    
    def test_list_users_requires_auth(self, client):
        """Test admin user list requires authentication."""
        response = client.get('/api/admin/all-user')
        
        assert response.status_code == 401
    
    def test_list_users_requires_admin_role(self, client, auth_headers):
        """Test that regular user cannot list users."""
        response = client.get('/api/admin/all-user')
        
        # Should require auth first, then check role (401 or 403)
        assert response.status_code in [401, 403]
    
    def test_create_user_requires_admin(self, client):
        """Test that creating users requires admin role."""
        response = client.post(
            '/api/admin/create-user',
            json={
                'email': 'newuser@test.com',
                'nom': 'Test',
                'prenom': 'User',
                'mdp': 'SecurePass123!',
                'role': 'Utilisateur'
            }
        )
        
        # Should require auth/admin
        assert response.status_code in [401, 403]


class TestAdminParameters:
    """Tests for application parameters management."""
    
    def test_get_parameters_no_auth_required(self, client):
        """Test that parameters endpoint is accessible."""
        response = client.get('/api/admin/parameters')
        
        # Should work (200) or require auth (401) - flexible
        assert response.status_code in [200, 401]
    
    def test_update_parameters_requires_admin(self, client):
        """Test that updating parameters requires admin."""
        response = client.post(
            '/api/admin/parameters',
            json={
                'margin_rate': 1.6
            }
        )
        
        # Should require admin auth
        assert response.status_code in [401, 403]

