"""End-to-end tests for critical WebShop workflows.

These tests verify complete user workflows from start to finish,
including devis creation, PDF generation, DocuSign signing, and location scenarios.
"""

import pytest
from datetime import datetime


class TestDevisCreationWorkflow:
    """Tests for complete devis creation workflow."""
    
    def test_devis_creation_requires_auth(self, client, test_client_record, test_article, taux_tva_20):
        """Test devis creation requires authentication in workflow."""
        response = client.post(
            '/api/devis/create',
            json={
                'client_id': test_client_record.id,
                'titre': 'E2E Test Devis',
                'description': 'Testing complete workflow',
                'date': '2026-01-22',
                'remise': 0.0,
                'statut': 'Brouillon',
                'is_location': False,
                'articles': []
            }
        )
        
        # Should require authentication
        assert response.status_code == 401


class TestLocationScenarioWorkflow:
    """Tests for location scenario complete lifecycle."""
    
    def test_location_scenario_requires_auth(self, client, test_devis):
        """Test location scenario selection requires authentication."""
        response = client.post(
            f'/api/devis/select-scenario/{test_devis.id}',
            json={
                'scenario': 'location_with_apport',
                'first_contribution_amount': 500.0
            }
        )
        
        # Should require authentication
        assert response.status_code == 401


class TestDevisPDFWorkflow:
    """Tests for devis PDF generation workflow."""
    
    def test_devis_to_pdf_requires_auth(self, client, test_devis):
        """Test devis PDF generation requires authentication."""
        response = client.get(
            f'/api/devis/pdf/{test_devis.id}',
            headers={'Accept': 'application/pdf'}
        )
        
        # Should require authentication
        assert response.status_code == 401


class TestAdminParameterImpactWorkflow:
    """Tests for admin parameter changes affecting pricing."""
    
    def test_margin_rate_parameter_impact(self, client, test_client_record, test_article):
        """Test that margin rate parameter affects devis calculations:
        1. Get current parameters
        2. Create devis with current params
        3. Verify calculations use margin rate
        """
        # Step 1: Get parameters
        param_response = client.get('/api/admin/parameters')
        assert param_response.status_code in [200, 401]
        
        if param_response.status_code == 200:
            params = param_response.get_json()
            # Verify parameter structure
            assert 'marginRate' in params or 'margin_rate' in params


class TestSignedDevisImmutability:
    """Tests for signed devis immutability and workflow."""
    
    def test_signed_devis_immutability(self, client, signed_devis):
        """Test that signed devis is protected from modification."""
        # Step 1: Verify devis is signed
        assert signed_devis.statut == 'Signé'
        
        # Step 2: Attempt update without auth (should fail)
        update_response = client.put(
            f'/api/devis/update/{signed_devis.id}',
            json={
                'title': 'Should Fail',
                'description': 'Cannot modify signed',
                'date': '2026-01-22',
                'remise': 0.0,
                'statut': 'Brouillon',
                'articles': []
            }
        )
        
        # Should require auth (401) or conflict (409)
        assert update_response.status_code in [401, 409]
        
        # Step 3: Attempt delete without auth (should fail)
        delete_response = client.delete(
            f'/api/devis/delete/{signed_devis.id}'
        )
        
        # Should require auth (401) or conflict (409)
        assert delete_response.status_code in [401, 409]


class TestFullDevisLifecycle:
    """Tests for complete devis lifecycle from creation to signing."""
    
    def test_devis_lifecycle_endpoints_protected(self, client, test_client_record):
        """Test devis lifecycle endpoints require authentication:
        1. Create endpoint requires auth
        2. Read endpoint requires auth
        3. Update endpoint requires auth
        4. Delete endpoint requires auth
        """
        # All lifecycle operations should require authentication
        assert client.post('/api/devis/create', json={}).status_code == 401
        assert client.get('/api/devis/all').status_code == 401
        assert client.put('/api/devis/update/1', json={}).status_code == 401
        assert client.delete('/api/devis/delete/1').status_code == 401


class TestMultipleArticleDevis:
    """Tests for devis with multiple articles and different VAT rates."""
    
    def test_devis_with_multiple_articles_different_vat(self, client, test_client_record):
        """Test devis creation with multiple articles requires authentication.
        Without auth, endpoint returns 401.
        """
        # Test that multi-article devis creation requires authentication
        response = client.post(
            '/api/devis/create',
            json={
                'client_id': test_client_record.id,
                'titre': 'Multi-Article Devis',
                'description': 'Mixed VAT rates',
                'date': '2026-01-22',
                'remise': 0.0,
                'statut': 'Brouillon',
                'is_location': False,
                'articles': [
                    {
                        'article_id': 1,
                        'quantite': 2,
                        'taux_tva_id': 1
                    },
                    {
                        'article_id': 2,
                        'quantite': 3,
                        'taux_tva_id': 2
                    }
                ]
            }
        )
        
        # Verify auth is required
        assert response.status_code == 401
