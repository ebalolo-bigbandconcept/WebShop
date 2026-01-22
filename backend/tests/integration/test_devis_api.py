"""Integration tests for Devis API endpoints.

Note: Integration tests require authenticated session context.
These tests verify endpoint structure and basic error handling.
Full integration testing should be done with Postman/curl or E2E tests.
"""


class TestDevisCreate:
    """Tests for devis creation endpoint."""
    
    def test_create_devis_requires_auth(self, client, test_client_record, test_article, taux_tva_20):
        """Test that devis creation requires authentication."""
        response = client.post(
            '/api/devis/create',
            json={
                'client_id': test_client_record.id,
                'titre': 'Devis Test',
                'description': 'Test devis description',
                'date': '2026-01-22',
                'remise': 0.0,
                'statut': 'Brouillon',
                'is_location': False,
                'articles': []
            }
        )
        
        # Should require authentication
        assert response.status_code == 401


class TestDevisRead:
    """Tests for devis retrieval endpoints."""
    
    def test_get_all_devis_requires_auth(self, client):
        """Test that listing devis requires authentication."""
        response = client.get('/api/devis/all')
        
        # Should require authentication
        assert response.status_code == 401
    
    def test_get_devis_by_id_requires_auth(self, client, test_devis):
        """Test that retrieving devis requires authentication."""
        response = client.get(f'/api/devis/info/{test_devis.id}')
        
        # Should require authentication
        assert response.status_code == 401
    
    def test_get_nonexistent_devis(self, client):
        """Test retrieving non-existent devis requires auth."""
        response = client.get('/api/devis/info/99999')
        
        # Should require authentication
        assert response.status_code == 401


class TestDevisUpdate:
    """Tests for devis modification endpoint."""
    
    def test_update_devis_requires_auth(self, client, test_devis):
        """Test that devis update requires authentication."""
        response = client.put(
            f'/api/devis/update/{test_devis.id}',
            json={
                'title': 'Updated Devis',
                'description': 'Updated description',
                'date': '2026-01-22',
                'remise': 10.0,
                'statut': 'Brouillon',
                'articles': []
            }
        )
        
        # Should require authentication
        assert response.status_code == 401


class TestDevisDelete:
    """Tests for devis deletion endpoint."""
    
    def test_delete_devis_requires_auth(self, client, test_devis):
        """Test that devis deletion requires authentication."""
        response = client.delete(f'/api/devis/delete/{test_devis.id}')
        
        # Should require authentication
        assert response.status_code == 401


class TestDevisScenario:
    """Tests for devis scenario selection."""
    
    def test_select_scenario_requires_auth(self, client, test_devis):
        """Test that scenario selection requires authentication."""
        response = client.post(
            f'/api/devis/select-scenario/{test_devis.id}',
            json={
                'scenario': 'location_with_apport',
                'first_contribution_amount': 500.0
            }
        )
        
        # Should require authentication
        assert response.status_code == 401
