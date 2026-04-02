"""Targeted auth tests to increase branch coverage in routes/auth.py."""

import pytest
from flask_bcrypt import Bcrypt

import routes.auth as auth_module
from models import User, db


class ExplodingTuple(tuple):
    """Tuple-like response that raises on item access to exercise alias fallback exception."""

    def __getitem__(self, index):
        raise RuntimeError("forced tuple indexing failure")


class TestAuthCoverageBranches:
    def test_me_with_stale_session_user_returns_401(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = 999999

        response = client.get("/api/user/me")

        assert response.status_code == 401
        assert response.get_json() == {"user": None}

    def test_register_success_sets_session_and_cookie(self, client):
        payload = {
            "email": "new.user@example.com",
            "prenom": "New",
            "nom": "User",
            "mdp": "StrongPass123!",
        }

        response = client.post("/api/user/register", json=payload)

        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == payload["email"]
        assert any("XSRF-TOKEN=" in c for c in response.headers.getlist("Set-Cookie"))

        me_response = client.get("/api/user/me")
        assert me_response.status_code == 200
        assert me_response.get_json()["email"] == payload["email"]

    def test_register_duplicate_email_returns_409(self, client):
        first_payload = {
            "email": "dup.user@example.com",
            "prenom": "Dup",
            "nom": "User",
            "mdp": "StrongPass123!",
        }
        client.post("/api/user/register", json=first_payload)

        response = client.post("/api/user/register", json=first_payload)

        assert response.status_code == 409
        assert "already exists" in response.get_json()["error"]

    def test_register_validation_error_returns_400(self, client):
        response = client.post(
            "/api/user/register",
            json={
                "email": "weak.user@example.com",
                "prenom": "Weak",
                "nom": "User",
                "mdp": "weak",
            },
        )

        assert response.status_code == 400
        assert "mot de passe" in response.get_json()["error"].lower()

    def test_auth_alias_login_handles_tuple_index_exception(self, client, monkeypatch):
        monkeypatch.setattr(
            auth_module, "login_user", lambda: ExplodingTuple((None, 401))
        )

        with pytest.raises(RuntimeError, match="forced tuple indexing failure"):
            client.post(
                "/api/auth/login",
                json={"email": "whatever@example.com", "mdp": "TestPassword123!"},
            )

    def test_auth_alias_login_fallback_success_for_test_password(self, client):
        bcrypt = Bcrypt()
        hashed = bcrypt.generate_password_hash("DifferentPass123!").decode("utf-8")
        user = User(
            email="fallback.alias@example.com",
            prenom="Alias",
            nom="Fallback",
            mdp=hashed,
            role="Utilisateur",
        )
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/api/auth/login",
            json={"email": user.email, "mdp": "TestPassword123!"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["email"] == user.email
