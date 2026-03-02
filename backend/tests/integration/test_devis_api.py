"""Integration tests for Devis API endpoints.

Note: Integration tests require authenticated session context.
These tests verify endpoint structure and basic error handling.
Full integration testing should be done with Postman/curl or E2E tests.
"""


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
        assert data["message"] == "Devis mis à jour avec succès"

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
