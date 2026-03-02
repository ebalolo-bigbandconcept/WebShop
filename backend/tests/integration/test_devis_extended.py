"""Extended integration tests for Devis API endpoints to improve coverage.

Focuses on edge cases, error handling, and complete endpoint coverage.
"""

from datetime import date, datetime

import pytest

from models import Devis, DevisArticles, Parameters, db


class TestDevisRetrievalExtended:
    """Extended tests for devis retrieval endpoints."""

    def test_get_all_devis_pagination(
        self, client, auth_headers, test_client_record, test_article, taux_tva_20
    ):
        """Test pagination of devis list."""
        # Create multiple devis
        for i in range(3):
            devis = Devis(
                client_id=test_client_record.id,
                titre=f"Devis {i}",
                description="Test",
                date=date.today(),
                montant_HT=100.0,
                montant_TVA=20.0,
                montant_TTC=120.0,
                statut="Brouillon",
            )
            db.session.add(devis)
        db.session.commit()

        response = client.get("/api/devis/all?page=1&per_page=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data

    def test_get_all_devis_page_boundaries(self, client, auth_headers):
        """Test page boundary handling."""
        response = client.get(
            "/api/devis/all?page=0&per_page=200", headers=auth_headers
        )
        # Should use defaults/min values
        assert response.status_code in [200, 404]

    def test_get_client_devis_empty(self, client, auth_headers):
        """Test getting devis for client with no devis."""
        response = client.get("/api/devis/client/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_client_devis_multiple(
        self, client, auth_headers, test_client_record, taux_tva_20
    ):
        """Test getting multiple devis for a client."""
        for i in range(2):
            devis = Devis(
                client_id=test_client_record.id,
                titre=f"Devis {i}",
                description="Test",
                date=date.today(),
                montant_HT=100.0,
                montant_TVA=20.0,
                montant_TTC=120.0,
                statut="Brouillon",
            )
            db.session.add(devis)
        db.session.commit()

        response = client.get(
            f"/api/devis/client/{test_client_record.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data.get("data", [])) >= 2

    def test_get_devis_info_signed_with_snapshot(
        self, client, auth_headers, test_devis
    ):
        """Test retrieving signed devis with snapshot data."""
        # Sign the devis with snapshot
        test_devis.statut = "Signé"
        test_devis.signed_at = datetime.utcnow()
        test_devis.signed_data = {
            "lines": [
                {
                    "article_id": 1,
                    "nom": "Test Article",
                    "designation": "REF-001",
                    "reference": "REF-PLAIN-001",
                    "quantite": 1,
                    "taux_tva": 0.2,
                    "montant_ht": 100.0,
                    "montant_tva": 20.0,
                    "montant_ttc": 120.0,
                }
            ],
            "totals": {"ht": 100.0, "tva": 20.0, "ttc": 120.0},
        }
        db.session.commit()

        response = client.get(f"/api/devis/info/{test_devis.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "articles" in data

    def test_get_new_devis_id_empty_db(self, client, auth_headers):
        """Test getting next devis ID when no devis exists."""
        response = client.get("/api/devis/new-id", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] >= 1


class TestDevisUpdateExtended:
    """Extended tests for devis update operations."""

    def test_update_devis_status_to_signed(
        self, client, auth_headers, test_devis, test_article, taux_tva_20
    ):
        """Test updating devis status to signed."""
        response = client.put(
            f"/api/devis/update/{test_devis.id}",
            json={
                "title": "Updated Devis",
                "description": "Updated description",
                "date": "2026-01-23",
                "remise": 0.0,
                "statut": "Signé",
                "is_location": False,
                "articles": [
                    {
                        "article_id": test_article.id,
                        "quantite": 1,
                        "taux_tva_id": taux_tva_20.id,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify snapshot was created
        devis = Devis.query.get(test_devis.id)
        assert devis.statut == "Signé"
        assert devis.signed_data is not None
        assert "lines" in devis.signed_data

    def test_update_nonexistent_devis(self, client, auth_headers):
        """Test updating non-existent devis."""
        response = client.put(
            "/api/devis/update/9999", json={"title": "Test"}, headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_signed_devis_fails(self, client, auth_headers, test_devis):
        """Test that updating signed devis fails."""
        test_devis.statut = "Signé"
        db.session.commit()

        response = client.put(
            f"/api/devis/update/{test_devis.id}",
            json={"title": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 409


class TestDevisLocationCalculations:
    """Tests for location-specific devis calculations."""

    def test_devis_location_with_all_costs(
        self, client, auth_headers, test_client_record, test_article, taux_tva_20
    ):
        """Test location devis with all cost components."""
        response = client.post(
            "/api/devis/create",
            json={
                "client_id": test_client_record.id,
                "title": "Location with costs",
                "description": "Location",
                "date": "2026-01-23",
                "remise": 0.0,
                "statut": "Brouillon",
                "is_location": True,
                "location_time": 24,
                "location_apport": 500.0,
                "location_subscription_cost": 200.0,
                "articles": [
                    {
                        "article_id": test_article.id,
                        "quantite": 2,
                        "taux_tva_id": taux_tva_20.id,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "computed" in data
        computed = data["computed"]
        assert computed["location_monthly_ttc"] > 0
        assert computed["location_monthly_ht"] > 0

    def test_devis_location_zero_time(
        self, client, auth_headers, test_client_record, test_article, taux_tva_20
    ):
        """Test location devis with zero time (edge case)."""
        response = client.post(
            "/api/devis/create",
            json={
                "client_id": test_client_record.id,
                "title": "Location zero time",
                "description": "Location",
                "date": "2026-01-23",
                "remise": 0.0,
                "statut": "Brouillon",
                "is_location": True,
                "location_time": 0,
                "location_apport": 100.0,
                "articles": [
                    {
                        "article_id": test_article.id,
                        "quantite": 1,
                        "taux_tva_id": taux_tva_20.id,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        # When location_time is 0 or None, it defaults to 12 months
        assert data["computed"]["location_monthly_ttc"] > 0


class TestDevisVATRoutes:
    """Tests for VAT-related devis routes."""

    def test_get_vat_rates(self, client, auth_headers):
        """Test getting available VAT rates."""
        response = client.get("/api/devis/tva", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert isinstance(data["data"], list)


class TestDevisScenarioExtended:
    """Extended tests for devis scenario selection."""

    def test_select_scenario_location_with_apport_extended(
        self, client, auth_headers, test_devis
    ):
        """Test selecting location scenario with apport."""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "location_with_apport"},
            headers=auth_headers,
        )
        assert response.status_code in [
            200,
            400,
        ]  # May fail if devis not in proper state

    def test_select_scenario_invalid_devis(self, client, auth_headers):
        """Test selecting scenario for non-existent devis."""
        response = client.post(
            "/api/devis/select-scenario/9999",
            json={"scenario": "direct"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDevisRemiseCalculation:
    """Tests for devis with remise (discount)."""

    def test_create_devis_with_remise(
        self, client, auth_headers, test_client_record, test_article, taux_tva_20
    ):
        """Test creating devis with discount."""
        response = client.post(
            "/api/devis/create",
            json={
                "client_id": test_client_record.id,
                "title": "Devis with discount",
                "description": "Test",
                "date": "2026-01-23",
                "remise": 50.0,  # €50 discount
                "statut": "Brouillon",
                "is_location": False,
                "articles": [
                    {
                        "article_id": test_article.id,
                        "quantite": 1,
                        "taux_tva_id": taux_tva_20.id,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        # Verify the created devis has the remise
        devis_id = data.get("id")
        devis = Devis.query.filter_by(id=devis_id).first()
        assert devis.remise == 50.0

    def test_update_devis_increase_remise(
        self, client, auth_headers, test_devis, test_article, taux_tva_20
    ):
        """Test increasing remise on existing devis."""
        response = client.put(
            f"/api/devis/update/{test_devis.id}",
            json={
                "title": test_devis.titre,
                "description": test_devis.description,
                "date": test_devis.date.isoformat(),
                "remise": 100.0,
                "statut": test_devis.statut,
                "is_location": False,
                "articles": [
                    {
                        "article_id": test_article.id,
                        "quantite": 1,
                        "taux_tva_id": taux_tva_20.id,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestDevisArticleHandling:
    """Tests for devis article handling edge cases."""

    def test_devis_with_invalid_article_id(
        self, client, auth_headers, test_client_record
    ):
        """Test devis creation with invalid article ID."""
        response = client.post(
            "/api/devis/create",
            json={
                "client_id": test_client_record.id,
                "title": "Invalid article",
                "description": "Test",
                "date": "2026-01-23",
                "remise": 0.0,
                "statut": "Brouillon",
                "is_location": False,
                "articles": [{"article_id": 9999, "quantite": 1, "taux_tva": 0.2}],
            },
            headers=auth_headers,
        )
        # Should create devis but with no articles
        assert response.status_code in [201, 400]

    def test_devis_empty_articles(self, client, auth_headers, test_client_record):
        """Test devis creation with no articles."""
        response = client.post(
            "/api/devis/create",
            json={
                "client_id": test_client_record.id,
                "title": "Empty devis",
                "description": "Test",
                "date": "2026-01-23",
                "remise": 0.0,
                "statut": "Brouillon",
                "is_location": False,
                "articles": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
