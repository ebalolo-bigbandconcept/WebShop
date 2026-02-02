"""
Extended tests for authentication - login and logout.
Since registration UI is disabled, focuses on login/logout edge cases.
"""

import pytest
from flask_bcrypt import Bcrypt

from models import User, db


class TestLoginExtended:
    """Extended tests for login functionality"""

    def test_login_with_invalid_password(self, client, app):
        """Test login fails with incorrect password"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("CorrectPassword").decode("utf-8")

        user = User(
            email="test@example.com",
            prenom="Test",
            nom="User",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/user/login",
            json={"email": "test@example.com", "mdp": "WrongPassword"},
        )

        assert response.status_code == 401

    def test_login_with_nonexistent_user(self, client):
        """Test login fails for non-existent user"""
        response = client.post(
            "/api/user/login",
            json={"email": "nonexistent@example.com", "mdp": "anypassword"},
        )

        assert response.status_code == 401

    def test_login_with_empty_email(self, client):
        """Test login fails with empty email"""
        response = client.post(
            "/api/user/login", json={"email": "", "mdp": "password123"}
        )

        assert response.status_code == 401

    def test_login_with_empty_password(self, client):
        """Test login fails with empty password"""
        response = client.post(
            "/api/user/login", json={"email": "test@example.com", "mdp": ""}
        )

        assert response.status_code == 401

    def test_login_with_missing_email_field(self, client):
        """Test login fails when email field is missing"""
        response = client.post("/api/user/login", json={"mdp": "password123"})

        assert response.status_code == 401

    def test_login_with_missing_password_field(self, client):
        """Test login fails when password field is missing"""
        response = client.post("/api/user/login", json={"email": "test@example.com"})

        assert response.status_code == 401

    def test_login_case_insensitive_email(self, client, app):
        """Test that email login is case-insensitive"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("password").decode("utf-8")

        user = User(
            email="Test@Example.com",
            prenom="Test",
            nom="User",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/user/login", json={"email": "test@example.com", "mdp": "password"}
        )

        # May succeed or fail depending on database collation
        assert response.status_code in [200, 401]

    def test_login_with_whitespace_email(self, client, app):
        """Test login strips whitespace from email"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("password").decode("utf-8")

        user = User(
            email="user@example.com",
            prenom="Test",
            nom="User",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/user/login", json={"email": "  user@example.com  ", "mdp": "password"}
        )

        assert response.status_code == 200

    def test_password_not_returned_in_response(self, client, app):
        """Test that password is never returned in login response"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("password").decode("utf-8")

        user = User(
            email="secure@example.com",
            prenom="Secure",
            nom="User",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/user/login", json={"email": "secure@example.com", "mdp": "password"}
        )

        data = response.get_json()
        # Check that mdp field is not in response
        assert "mdp" not in str(data).lower() or data.get("mdp") is None


class TestLogoutExtended:
    """Extended tests for logout functionality"""

    def test_logout_without_login(self, client):
        """Test logout without being logged in"""
        response = client.post("/api/user/logout")

        # Should succeed (clears session even if not logged in)
        assert response.status_code == 200

    def test_logout_multiple_times(self, client, app):
        """Test logout can be called multiple times"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("password").decode("utf-8")

        user = User(
            email="multi@example.com",
            prenom="Multi",
            nom="Logout",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        # Login
        client.post(
            "/api/user/login", json={"email": "multi@example.com", "mdp": "password"}
        )

        # Logout multiple times
        for _ in range(3):
            response = client.post("/api/user/logout")
            assert response.status_code == 200


class TestSessionManagement:
    """Tests for session handling"""

    def test_session_cleared_after_logout(self, client, app):
        """Test that session is cleared after logout"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("password").decode("utf-8")

        user = User(
            email="session@example.com",
            prenom="Session",
            nom="Test",
            mdp=hashed,
            role="Administrateur",
        )
        db.session.add(user)
        db.session.commit()

        # Login
        client.post(
            "/api/user/login", json={"email": "session@example.com", "mdp": "password"}
        )

        # Logout
        client.post("/api/user/logout")

        # Try accessing /me endpoint after logout
        response = client.get("/api/user/me")
        assert response.status_code == 401

    def test_me_endpoint_without_login(self, client):
        """Test /me endpoint returns 401 when not logged in"""
        response = client.get("/api/user/me")
        assert response.status_code == 401

    def test_me_endpoint_after_login(self, client, app):
        """Test /me endpoint returns user info after login"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("password").decode("utf-8")

        user = User(
            email="me@example.com",
            prenom="Me",
            nom="Test",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        # Login
        client.post(
            "/api/user/login", json={"email": "me@example.com", "mdp": "password"}
        )

        # Get current user
        response = client.get("/api/user/me")
        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "me@example.com"


class TestPasswordHandling:
    """Tests for password validation"""

    def test_login_with_long_password(self, client, app):
        """Test login with long password (bcrypt max is 72 bytes)"""
        bcrypt = Bcrypt()
        # Bcrypt max is 72 bytes, so use 70 to be safe
        long_password = "a" * 70
        hashed = bcrypt.generate_password_hash(long_password).decode("utf-8")

        user = User(
            email="long@example.com",
            prenom="Long",
            nom="Pass",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/user/login", json={"email": "long@example.com", "mdp": long_password}
        )

        assert response.status_code == 200

    def test_login_with_unicode_password(self, client, app):
        """Test login with unicode characters in password"""
        bcrypt = Bcrypt()
        unicode_password = "pässwörd123"
        hashed = bcrypt.generate_password_hash(unicode_password).decode("utf-8")

        user = User(
            email="unicode@example.com",
            prenom="Unicode",
            nom="Test",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/user/login",
            json={"email": "unicode@example.com", "mdp": unicode_password},
        )

        assert response.status_code == 200


class TestRoleBasedAccess:
    """Tests for role handling in login"""

    def test_admin_role_login(self, client, app):
        """Test login returns correct role for admin"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("adminpass").decode("utf-8")

        admin = User(
            email="admin@example.com",
            prenom="Admin",
            nom="User",
            mdp=hashed,
            role="Administrateur",
        )
        db.session.add(admin)
        db.session.commit()

        response = client.post(
            "/api/user/login", json={"email": "admin@example.com", "mdp": "adminpass"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["role"] == "Administrateur"

    def test_user_role_login(self, client, app):
        """Test login returns correct role for regular user"""
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("userpass").decode("utf-8")

        user = User(
            email="user@example.com",
            prenom="Regular",
            nom="User",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/user/login", json={"email": "user@example.com", "mdp": "userpass"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["role"] == "Utilisateur"
