"""
Extended tests for admin API endpoints.
Covers error handling, validation, and edge cases.
"""
import pytest
from models import User, TauxTVA, Parameters, Articles, db
from flask_bcrypt import Bcrypt


class TestUserManagementExtended:
    """Extended tests for user management"""

    def test_create_user_duplicate_email(self, client, admin_auth_headers, app):
        """Test creating user with duplicate email returns 409"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("existing").decode('utf-8')
        existing = User(email="existing@test.com", prenom="Existing", nom="User",
                       mdp=hashed, role="Utilisateur")
        db.session.add(existing)
        db.session.commit()
        
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": "existing@test.com",
                "prenom": "New",
                "nom": "User",
                "mdp": "password123",
                "role": "Utilisateur"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 409

    def test_create_user_invalid_email(self, client, admin_auth_headers):
        """Test creating user with invalid email returns 400"""
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": "notanemail",
                "prenom": "Test",
                "nom": "User",
                "mdp": "password123",
                "role": "Utilisateur"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400

    def test_create_user_invalid_role(self, client, admin_auth_headers):
        """Test creating user with invalid role returns 400"""
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": "test@example.com",
                "prenom": "Test",
                "nom": "User",
                "mdp": "password123",
                "role": "InvalidRole"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400

    def test_create_user_missing_required_fields(self, client, admin_auth_headers):
        """Test creating user with missing fields returns 400"""
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": "test@example.com",
                "prenom": "Test"
                # Missing nom, mdp, role
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400

    def test_update_user_nonexistent(self, client, admin_auth_headers):
        """Test updating non-existent user returns 404"""
        response = client.post(
            '/api/admin/update-user/99999',
            json={
                "email": "updated@example.com",
                "prenom": "Updated",
                "nom": "User",
                "role": "Utilisateur"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 404

    def test_update_user_invalid_email(self, client, admin_auth_headers, app):
        """Test updating user with invalid email returns 400"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("password").decode('utf-8')
        user = User(email="user@test.com", prenom="Test", nom="User",
                   mdp=hashed, role="Utilisateur")
        db.session.add(user)
        db.session.commit()
        
        response = client.post(
            f'/api/admin/update-user/{user.id}',
            json={
                "email": "invalidemail",
                "prenom": "Test",
                "nom": "User",
                "role": "Utilisateur"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400

    def test_delete_user_nonexistent(self, client, admin_auth_headers):
        """Test deleting non-existent user returns 404"""
        response = client.post(
            '/api/admin/delete-user/99999',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 404

    def test_admin_endpoints_require_auth(self, client):
        """Test admin endpoints return 401 without authentication"""
        endpoints = [
            ('/api/admin/all-user', 'GET'),
            ('/api/admin/create-user', 'POST'),
            ('/api/admin/parameters', 'GET'),
            ('/api/admin/tva', 'GET'),
        ]
        
        for endpoint, method in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401

    def test_admin_endpoints_require_admin_role(self, client, regular_user, app):
        """Test admin endpoints return 403 for non-admin users"""
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("UserPass123!").decode('utf-8')
        user = User(email="regularuser@test.com", prenom="Regular", nom="User",
                   mdp=hashed, role="Utilisateur")
        db.session.add(user)
        db.session.commit()
        
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
        
        response = client.get('/api/admin/all-user')
        assert response.status_code == 403


class TestParametersExtended:
    """Extended tests for parameters management"""

    def test_update_parameters_with_invalid_numbers(self, client, admin_auth_headers, test_parameters):
        """Test updating parameters with invalid number values"""
        response = client.post(
            '/api/admin/parameters',
            json={
                "marginRate": "not_a_number",
                "marginRateLocation": 1.5,
                "locationTime": 12
            },
            headers=admin_auth_headers
        )
        
        # Should handle gracefully (may convert or reject)
        assert response.status_code in [200, 400]

    def test_update_parameters_with_negative_values(self, client, admin_auth_headers, test_parameters):
        """Test updating parameters with negative values"""
        response = client.post(
            '/api/admin/parameters',
            json={
                "marginRate": -1.0,
                "marginRateLocation": -0.5,
                "locationTime": -12
            },
            headers=admin_auth_headers
        )
        
        # Should still succeed (validation may allow negatives for some fields)
        assert response.status_code == 200

    def test_update_parameters_partial_update(self, client, admin_auth_headers, test_parameters):
        """Test updating only some parameters"""
        response = client.post(
            '/api/admin/parameters',
            json={
                "marginRate": 1.8
                # Only updating one field
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200

    def test_update_parameters_with_html_in_conditions(self, client, admin_auth_headers, test_parameters):
        """Test updating parameters with HTML in general conditions"""
        response = client.post(
            '/api/admin/parameters',
            json={
                "generalConditionsSales": "<p>Test <b>conditions</b> with <script>alert('xss')</script> HTML</p>"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        # HTML should be sanitized
        data = response.get_json()
        assert "<script>" not in data.get("generalConditionsSales", "")


class TestTVAManagementExtended:
    """Extended tests for TVA (VAT) rate management"""

    def test_create_tva_invalid_rate(self, client, admin_auth_headers):
        """Test creating TVA with invalid rate format"""
        response = client.post(
            '/api/admin/tva',
            json={
                "taux": "not_a_number"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400

    def test_create_tva_negative_rate(self, client, admin_auth_headers):
        """Test creating TVA with negative rate"""
        response = client.post(
            '/api/admin/tva',
            json={
                "taux": -0.20
            },
            headers=admin_auth_headers
        )
        
        # May allow or reject negative rates
        assert response.status_code in [200, 201, 400]

    def test_create_tva_missing_rate(self, client, admin_auth_headers):
        """Test creating TVA without rate field"""
        response = client.post(
            '/api/admin/tva',
            json={},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400

    def test_delete_tva_nonexistent(self, client, admin_auth_headers):
        """Test deleting non-existent TVA returns 404"""
        response = client.delete(
            '/api/admin/tva/99999',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 404

    def test_delete_tva_in_use(self, client, admin_auth_headers, taux_tva_20, test_article):
        """Test deleting TVA that's in use by articles"""
        response = client.delete(
            f'/api/admin/tva/{taux_tva_20.id}',
            headers=admin_auth_headers
        )
        
        # May fail due to foreign key constraint or succeed with cascade
        assert response.status_code in [200, 204, 400, 409]


class TestArticleManagementExtended:
    """Extended tests for article management"""

    def test_get_articles_requires_auth(self, client, test_article):
        """Test getting articles requires authentication"""
        response = client.get('/api/articles/all')
        assert response.status_code == 401

    def test_get_articles_with_auth(self, client, auth_headers, test_article):
        """Test authenticated users can get articles"""
        response = client.get(
            '/api/articles/all?page=1&per_page=10',
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestAdminSecurityAndValidation:
    """Tests for security and validation in admin routes"""

    def test_sql_injection_in_user_email(self, client, admin_auth_headers):
        """Test SQL injection attempt in user creation"""
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": "test@test.com' OR '1'='1",
                "prenom": "SQL",
                "nom": "Injection",
                "mdp": "password123",
                "role": "Utilisateur"
            },
            headers=admin_auth_headers
        )
        
        # Should either fail validation or safely handle
        assert response.status_code in [400, 409]

    def test_xss_in_user_fields(self, client, admin_auth_headers):
        """Test XSS attempt in user fields"""
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": "xss@test.com",
                "prenom": "<script>alert('xss')</script>",
                "nom": "Test",
                "mdp": "password123",
                "role": "Utilisateur"
            },
            headers=admin_auth_headers
        )
        
        # May succeed but should sanitize on output
        assert response.status_code in [200, 201, 400]

    def test_very_long_input_fields(self, client, admin_auth_headers):
        """Test handling of very long input in user creation"""
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": "a" * 1000 + "@test.com",
                "prenom": "x" * 1000,
                "nom": "y" * 1000,
                "mdp": "password123",
                "role": "Utilisateur"
            },
            headers=admin_auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 400

    def test_empty_string_fields(self, client, admin_auth_headers):
        """Test handling of empty strings in required fields"""
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": "",
                "prenom": "",
                "nom": "",
                "mdp": "",
                "role": "Utilisateur"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400

    def test_null_values_in_fields(self, client, admin_auth_headers):
        """Test handling of null values"""
        response = client.post(
            '/api/admin/create-user',
            json={
                "email": None,
                "prenom": None,
                "nom": None,
                "mdp": None,
                "role": None
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400
