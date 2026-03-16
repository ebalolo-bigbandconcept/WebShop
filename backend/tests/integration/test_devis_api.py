"""Integration tests for Devis API endpoints.

Note: Integration tests require authenticated session context.
These tests verify endpoint structure and basic error handling.
Full integration testing should be done with Postman/curl or E2E tests.
"""

from models import Devis, DevisArticles, db


class TestDevisCreate:
    """Tests for devis creation endpoint."""

    def test_create_devis_requires_auth(
        self, client, test_client_record, test_article, taux_tva_20
    ):
        """Test that devis creation requires authentication."""
        response = client.post(
            "/api/devis/create",
            json={
                "client_id": test_client_record.id,
                "titre": "Devis Test",
                "description": "Test devis description",
                "date": "2026-01-22",
                "remise": 0.0,
                "statut": "Brouillon",
                "is_location": False,
                "articles": [],
            },
        )

        # Should require authentication
        assert response.status_code == 401


class TestDevisRead:
    """Tests for devis retrieval endpoints."""

    def test_get_all_devis_requires_auth(self, client):
        """Test that listing devis requires authentication."""
        response = client.get("/api/devis/all")

        # Should require authentication
        assert response.status_code == 401

    def test_get_devis_by_id_requires_auth(self, client, test_devis):
        """Test that retrieving devis requires authentication."""
        response = client.get(f"/api/devis/info/{test_devis.id}")

        # Should require authentication
        assert response.status_code == 401

    def test_get_nonexistent_devis(self, client):
        """Test retrieving non-existent devis requires auth."""
        response = client.get("/api/devis/info/99999")

        # Should require authentication
        assert response.status_code == 401


class TestDevisUpdate:
    """Tests for devis modification endpoint."""

    def test_update_devis_requires_auth(self, client, test_devis):
        """Test that devis update requires authentication."""
        response = client.put(
            f"/api/devis/update/{test_devis.id}",
            json={
                "title": "Updated Devis",
                "description": "Updated description",
                "date": "2026-01-22",
                "remise": 10.0,
                "statut": "Brouillon",
                "articles": [],
            },
        )

        # Should require authentication
        assert response.status_code == 401


class TestDevisDelete:
    """Tests for devis deletion endpoint."""

    def test_delete_devis_requires_auth(self, client, test_devis):
        """Test that devis deletion requires authentication."""
        response = client.delete(f"/api/devis/delete/{test_devis.id}")

        # Should require authentication
        assert response.status_code == 401

    def test_delete_devis_success(self, client, test_devis, auth_headers):
        """Test successful devis deletion."""
        response = client.delete(
            f"/api/devis/delete/{test_devis.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Devis supprimé avec succès"

    def test_delete_nonexistent_devis(self, client, auth_headers):
        """Test deleting non-existent devis."""
        response = client.delete("/api/devis/delete/99999", headers=auth_headers)

        assert response.status_code == 404


class TestDevisDuplicate:
    """Tests for duplicating devis."""

    def test_duplicate_devis_requires_auth(self, client, test_devis):
        """Test that devis duplication requires authentication."""
        response = client.post(f"/api/devis/duplicate/{test_devis.id}")

        assert response.status_code == 401

    def test_duplicate_nonexistent_devis(self, client, auth_headers):
        """Test duplicating a non-existent devis."""
        response = client.post("/api/devis/duplicate/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_duplicate_devis_success(self, client, auth_headers, test_devis):
        """Test successful devis duplication with same data and new ID."""
        original = Devis.query.filter_by(id=test_devis.id).first()
        original_articles = DevisArticles.query.filter_by(devis_id=original.id).all()

        response = client.post(
            f"/api/devis/duplicate/{test_devis.id}", headers=auth_headers
        )

        assert response.status_code == 201
        duplicated_payload = response.get_json()
        duplicated_id = duplicated_payload["id"]

        assert duplicated_id != original.id

        duplicated = Devis.query.filter_by(id=duplicated_id).first()
        assert duplicated is not None
        assert duplicated.client_id == original.client_id
        assert duplicated.titre == original.titre
        assert duplicated.description == original.description
        assert duplicated.date == original.date
        assert duplicated.montant_HT == original.montant_HT
        assert duplicated.montant_TVA == original.montant_TVA
        assert duplicated.montant_TTC == original.montant_TTC
        assert duplicated.remise == original.remise
        assert duplicated.statut == original.statut

        duplicated_articles = DevisArticles.query.filter_by(
            devis_id=duplicated.id
        ).all()
        assert len(duplicated_articles) == len(original_articles)

        # Sort to compare records deterministically by article id then id.
        original_articles_sorted = sorted(
            original_articles, key=lambda article: (article.article_id, article.id)
        )
        duplicated_articles_sorted = sorted(
            duplicated_articles, key=lambda article: (article.article_id, article.id)
        )

        for original_article, duplicated_article in zip(
            original_articles_sorted, duplicated_articles_sorted
        ):
            assert duplicated_article.id != original_article.id
            assert duplicated_article.devis_id == duplicated.id
            assert duplicated_article.article_id == original_article.article_id
            assert duplicated_article.quantite == original_article.quantite
            assert duplicated_article.taux_tva_id == original_article.taux_tva_id
            assert duplicated_article.commentaire == original_article.commentaire
            assert duplicated_article.montant_HT == original_article.montant_HT
            assert duplicated_article.montant_TVA == original_article.montant_TVA
            assert duplicated_article.montant_TTC == original_article.montant_TTC


class TestDevisScenario:
    """Tests for devis scenario selection."""

    def test_select_scenario_requires_auth(self, client, test_devis):
        """Test that scenario selection requires authentication."""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={
                "scenario": "location_with_apport",
                "first_contribution_amount": 500.0,
            },
        )

        # Should require authentication
        assert response.status_code == 401

    def test_select_scenario_location_with_apport(
        self, client, test_devis, auth_headers
    ):
        """Test selecting location scenario with apport."""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={
                "scenario": "location_with_apport",
                "first_contribution_amount": 500.0,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Scenario selected successfully"


class TestDevisCreationWithArticles:
    """Tests for creating devis with articles."""

    def test_create_devis_with_article(
        self, client, auth_headers, test_client_record, test_article, taux_tva_20
    ):
        """Test creating a devis with an article."""
        response = client.post(
            "/api/devis/create",
            json={
                "client_id": test_client_record.id,
                "titre": "Devis avec article",
                "description": "Test devis",
                "date": "2026-01-22",
                "remise": 0.0,
                "statut": "Brouillon",
                "is_location": False,
                "articles": [
                    {
                        "article_id": test_article.id,
                        "quantite": 2,
                        "taux_tva_id": taux_tva_20.id,
                        "commentaire": "Article de test",
                    }
                ],
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data

    def test_create_devis_location(
        self, client, auth_headers, test_client_record, test_article, taux_tva_20
    ):
        """Test creating a location devis."""
        response = client.post(
            "/api/devis/create",
            json={
                "client_id": test_client_record.id,
                "titre": "Devis location",
                "description": "Test location",
                "date": "2026-01-22",
                "remise": 0.0,
                "statut": "Brouillon",
                "is_location": True,
                "location_time": 12,
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
        assert "id" in data


class TestDevisRetrieval:
    """Tests for retrieving devis."""

    def test_get_all_devis_with_auth(self, client, auth_headers, test_devis):
        """Test getting all devis with authentication."""
        response = client.get("/api/devis/all", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data

    def test_get_devis_by_id_with_auth(self, client, auth_headers, test_devis):
        """Test getting specific devis with authentication."""
        response = client.get(f"/api/devis/info/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == test_devis.id


class TestDevisUpdateOperations:
    """Tests for updating devis."""

    def test_update_devis_with_auth(
        self, client, auth_headers, test_devis, test_article, taux_tva_20
    ):
        """Test updating a devis."""
        response = client.put(
            f"/api/devis/update/{test_devis.id}",
            json={
                "titre": "Updated Devis Title",
                "description": "Updated description",
                "date": "2026-01-23",
                "remise": 50.0,
                "statut": "En attente",
                "is_location": False,
                "articles": [
                    {
                        "article_id": test_article.id,
                        "quantite": 3,
                        "taux_tva_id": taux_tva_20.id,
                    }
                ],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == test_devis.id
        assert data["titre"] == "Updated Devis Title"

    def test_update_nonexistent_devis(self, client, auth_headers):
        """Test updating non-existent devis."""
        response = client.put(
            "/api/devis/update/99999",
            json={
                "titre": "Test",
                "description": "Test",
                "date": "2026-01-22",
                "remise": 0.0,
                "statut": "Brouillon",
                "articles": [],
            },
            headers=auth_headers,
        )

        assert response.status_code == 404
