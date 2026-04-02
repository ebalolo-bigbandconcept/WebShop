"""Targeted admin tests to increase branch coverage in routes/admin.py."""

import pytest
from flask_bcrypt import Bcrypt

from models import InterestRateRange, Parameters, TauxTVA, User, db


def _create_user(email, role="Utilisateur", password="UserPass123!"):
    bcrypt = Bcrypt()
    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(email=email, prenom="Test", nom="User", mdp=hashed, role=role)
    db.session.add(user)
    db.session.commit()
    return user


class TestAdminCoverageBranches:
    def test_update_user_prevents_demoting_last_admin(
        self, client, admin_auth_headers, admin_user
    ):
        response = client.post(
            f"/api/admin/update-user/{admin_user.id}",
            json={
                "email": admin_user.email,
                "prenom": admin_user.prenom,
                "nom": admin_user.nom,
                "role": "Utilisateur",
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 403

    def test_update_user_prevents_self_admin_role_change_with_multiple_admins(
        self, client, admin_auth_headers, admin_user
    ):
        _create_user("second.admin@example.com", role="Administrateur")

        response = client.post(
            f"/api/admin/update-user/{admin_user.id}",
            json={
                "email": admin_user.email,
                "prenom": admin_user.prenom,
                "nom": admin_user.nom,
                "role": "Utilisateur",
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 403

    def test_update_user_duplicate_email_conflict(self, client, admin_auth_headers):
        target = _create_user("target.user@example.com", role="Utilisateur")
        other = _create_user("other.user@example.com", role="Utilisateur")

        response = client.post(
            f"/api/admin/update-user/{target.id}",
            json={
                "email": other.email,
                "prenom": target.prenom,
                "nom": target.nom,
                "role": target.role,
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 409

    def test_update_user_updates_email_role_and_password(
        self, client, admin_auth_headers
    ):
        user = _create_user("before.update@example.com", role="Utilisateur")

        response = client.post(
            f"/api/admin/update-user/{user.id}",
            json={
                "email": "after.update@example.com",
                "prenom": "Updated",
                "nom": "Name",
                "mdp": "NewStrongPass123!",
                "role": "Administrateur",
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        refreshed = User.query.get(user.id)
        assert refreshed.email == "after.update@example.com"
        assert refreshed.role == "Administrateur"

    def test_delete_user_prevents_self_deletion(
        self, client, admin_auth_headers, admin_user
    ):
        response = client.delete(
            f"/api/admin/delete-user/{admin_user.id}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 403

    def test_get_user_info_missing_user_returns_server_error(
        self, client, admin_auth_headers
    ):
        with pytest.raises(AttributeError):
            client.post("/api/admin/info-user/999999", headers=admin_auth_headers)

    def test_get_parameters_creates_defaults_if_missing(self, client, auth_headers):
        Parameters.query.delete()
        db.session.commit()

        response = client.get("/api/admin/parameters", headers=auth_headers)

        assert response.status_code == 200
        assert Parameters.query.first() is not None

    def test_update_parameters_creates_row_if_missing(self, client, admin_auth_headers):
        Parameters.query.delete()
        db.session.commit()

        response = client.post(
            "/api/admin/parameters",
            json={
                "marginRate": 1.9,
                "marginRateLocation": 2.1,
                "locationTime": 24,
                "locationSubscriptionCost": 19.9,
                "locationInterestsCost": 10.0,
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        saved = Parameters.query.first()
        assert saved is not None
        assert saved.margin_rate == 1.9

    def test_list_tva_and_add_duplicate_and_delete_success(
        self, client, admin_auth_headers
    ):
        unique_rate = TauxTVA(taux=0.157)
        db.session.add(unique_rate)
        db.session.commit()

        list_response = client.get("/api/admin/tva", headers=admin_auth_headers)
        assert list_response.status_code == 200
        assert "data" in list_response.get_json()

        duplicate_response = client.post(
            "/api/admin/tva",
            json={"taux": 0.157},
            headers=admin_auth_headers,
        )
        assert duplicate_response.status_code == 200
        assert duplicate_response.get_json()["id"] == unique_rate.id

        deletable = TauxTVA(taux=0.321)
        db.session.add(deletable)
        db.session.commit()

        delete_response = client.delete(
            f"/api/admin/tva/{deletable.id}", headers=admin_auth_headers
        )
        assert delete_response.status_code == 200
        assert delete_response.get_json()["status"] == "deleted"

    def test_interest_rate_list_add_update_delete_paths(
        self, client, admin_auth_headers
    ):
        list_response = client.get(
            "/api/admin/interest-rates", headers=admin_auth_headers
        )
        assert list_response.status_code == 200
        assert "data" in list_response.get_json()

        invalid_range_response = client.post(
            "/api/admin/interest-rates",
            json={"minimum": 1000, "maximum": 500, "interests": 100},
            headers=admin_auth_headers,
        )
        assert invalid_range_response.status_code == 400

        overlap_response = client.post(
            "/api/admin/interest-rates",
            json={"minimum": 100, "maximum": 4000, "interests": 80},
            headers=admin_auth_headers,
        )
        assert overlap_response.status_code == 409

        create_response = client.post(
            "/api/admin/interest-rates",
            json={"minimum": -5000, "maximum": -1, "interests": 200},
            headers=admin_auth_headers,
        )
        assert create_response.status_code == 200
        created_id = create_response.get_json()["id"]

        not_found_update = client.put(
            "/api/admin/interest-rates/999999",
            json={"minimum": 1, "maximum": 2, "interests": 1},
            headers=admin_auth_headers,
        )
        assert not_found_update.status_code == 404

        min_gte_max_update = client.put(
            f"/api/admin/interest-rates/{created_id}",
            json={"minimum": 5000, "maximum": 5000, "interests": 220},
            headers=admin_auth_headers,
        )
        assert min_gte_max_update.status_code == 400

        existing = InterestRateRange.query.filter_by(minimum=0).first()
        overlap_update = client.put(
            f"/api/admin/interest-rates/{created_id}",
            json={
                "minimum": existing.minimum,
                "maximum": existing.maximum,
                "interests": 230,
            },
            headers=admin_auth_headers,
        )
        assert overlap_update.status_code == 409

        valid_update = client.put(
            f"/api/admin/interest-rates/{created_id}",
            json={"minimum": -9000, "maximum": -6000, "interests": 250},
            headers=admin_auth_headers,
        )
        assert valid_update.status_code == 200

        not_found_delete = client.delete(
            "/api/admin/interest-rates/999999", headers=admin_auth_headers
        )
        assert not_found_delete.status_code == 404

        delete_response = client.delete(
            f"/api/admin/interest-rates/{created_id}", headers=admin_auth_headers
        )
        assert delete_response.status_code == 200
        assert delete_response.get_json()["status"] == "deleted"
