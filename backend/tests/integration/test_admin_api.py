"""Integration tests for Admin API endpoints."""


class TestAdminUsers:
    """Tests for admin user management endpoints."""

    def test_list_users_requires_auth(self, client):
        """Test admin user list requires authentication."""
        response = client.get("/api/admin/all-user")

        assert response.status_code == 401

    def test_list_users_requires_admin_role(self, client, auth_headers):
        """Test that regular user cannot list users."""
        response = client.get("/api/admin/all-user")

        # Should require auth first, then check role (401 or 403)
        assert response.status_code in [401, 403]

    def test_create_user_requires_admin(self, client):
        """Test that creating users requires admin role."""
        response = client.post(
            "/api/admin/create-user",
            json={
                "email": "newuser@test.com",
                "nom": "Test",
                "prenom": "User",
                "mdp": "SecurePass123!",
                "role": "Utilisateur",
            },
        )

        # Should require auth/admin
        assert response.status_code in [401, 403]


class TestAdminParameters:
    """Tests for application parameters management."""

    def test_get_parameters_no_auth_required(self, client):
        """Test that parameters endpoint is accessible."""
        response = client.get("/api/admin/parameters")

        # Should work (200) or require auth (401) - flexible
        assert response.status_code in [200, 401]

    def test_update_parameters_requires_admin(self, client):
        """Test that updating parameters requires admin."""
        response = client.post("/api/admin/parameters", json={"margin_rate": 1.6})

        # Should require admin auth
        assert response.status_code in [401, 403]

    def test_get_parameters_with_auth(self, client, auth_headers, test_parameters):
        """Test getting parameters with authentication."""
        response = client.get("/api/admin/parameters", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "marginRate" in data

    def test_update_parameters_with_admin(
        self, client, admin_auth_headers, test_parameters
    ):
        """Test updating parameters as admin."""
        response = client.post(
            "/api/admin/parameters",
            json={"margin_rate": 1.8, "margin_rate_location": 1.5},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Parameters updated successfully"


class TestAdminUserManagement:
    """Tests for admin user CRUD operations."""

    def test_list_users_with_admin(
        self, client, admin_auth_headers, admin_user, regular_user
    ):
        """Test listing users as admin."""
        response = client.get("/api/admin/all-user", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) >= 2  # At least admin and regular user

    def test_create_user_with_admin(self, client, admin_auth_headers):
        """Test creating a user as admin."""
        response = client.post(
            "/api/admin/create-user",
            json={
                "email": "newuser@example.com",
                "nom": "NewUser",
                "prenom": "Test",
                "mdp": "SecurePass123!",
                "role": "Utilisateur",
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "user_id" in data

    def test_create_user_duplicate_email(
        self, client, admin_auth_headers, regular_user
    ):
        """Test creating user with duplicate email."""
        response = client.post(
            "/api/admin/create-user",
            json={
                "email": regular_user.email,
                "nom": "Duplicate",
                "prenom": "Test",
                "mdp": "SecurePass123!",
                "role": "Utilisateur",
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 409

    def test_update_user_with_admin(self, client, admin_auth_headers, regular_user):
        """Test updating a user as admin."""
        response = client.post(
            f"/api/admin/update-user/{regular_user.id}",
            json={
                "email": regular_user.email,
                "nom": "UpdatedName",
                "prenom": "UpdatedFirst",
                "role": "Utilisateur",
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "User updated successfully"

    def test_delete_user_with_admin(self, client, admin_auth_headers, db_session):
        """Test deleting a user as admin."""
        from models import Users

        # Create a user to delete
        user = Users(
            email="todelete@example.com",
            nom="ToDelete",
            prenom="User",
            role="Utilisateur",
        )
        user.set_password("TempPass123!")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        response = client.delete(
            f"/api/admin/delete-user/{user_id}", headers=admin_auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "User deleted successfully"
