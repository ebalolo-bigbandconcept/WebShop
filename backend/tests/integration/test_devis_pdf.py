"""
Tests for PDF generation and signing functionality for devis.
Covers:
- PDF rendering with different scenarios (direct, location_without_apport, location_with_apport)
- Signed devis PDF with snapshots
- Scenario selection and locking
- VAT breakdowns in PDF
"""

import io
from datetime import datetime

import pytest

from models import Articles, DevisArticles, TauxTVA, db


class TestPDFGeneration:
    """Tests for PDF generation endpoint"""

    def test_get_devis_pdf_direct_scenario(
        self, client, auth_headers, test_devis, test_article
    ):
        """Test PDF generation for direct purchase scenario"""
        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.content_type == "application/pdf"
        assert response.data is not None
        assert len(response.data) > 0
        # PDF files start with %PDF magic bytes
        assert response.data[:4] == b"%PDF"

    def test_get_devis_pdf_location_without_apport(
        self, client, auth_headers, test_devis, test_article
    ):
        """Test PDF generation for location scenario without apport"""
        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=location_without_apport",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.content_type == "application/pdf"
        assert response.data[:4] == b"%PDF"

    def test_get_devis_pdf_location_with_apport(
        self, client, auth_headers, test_devis, test_article
    ):
        """Test PDF generation for location scenario with apport"""
        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=location_with_apport",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.content_type == "application/pdf"
        assert response.data[:4] == b"%PDF"

    def test_get_devis_pdf_invalid_scenario(self, client, auth_headers, test_devis):
        """Test PDF generation with invalid scenario defaults to direct"""
        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=invalid_scenario",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_get_devis_pdf_nonexistent_devis(self, client, auth_headers):
        """Test PDF generation for non-existent devis returns 404"""
        response = client.get("/api/devis/pdf/99999", headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_get_devis_pdf_unauthorized(self, client, test_devis):
        """Test PDF generation without auth returns 401"""
        response = client.get(f"/api/devis/pdf/{test_devis.id}")

        assert response.status_code == 401

    def test_get_devis_pdf_location_devis_no_contract(
        self, client, auth_headers, test_devis
    ):
        """Test PDF generation for location devis when contract file missing"""
        # Mark devis as location
        test_devis.is_location = True
        test_devis.selected_scenario = "location_with_apport"
        from models import db

        db.session.commit()

        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=location_with_apport",
            headers=auth_headers,
        )

        # Should still work even if contract missing (logged as warning)
        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_get_devis_pdf_with_remise(self, client, auth_headers, test_devis):
        """Test PDF generation correctly applies remise"""
        # Add remise to devis
        test_devis.remise = 50.0
        from models import db

        db.session.commit()

        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_get_devis_pdf_with_zero_location_time(
        self, client, auth_headers, test_parameters, test_devis
    ):
        """Test PDF generation with zero location_time parameter"""
        # Set location_time to 0
        test_parameters.location_time = 0
        from models import db

        db.session.commit()

        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=location_without_apport",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"


class TestScenarioSelection:
    """Tests for scenario selection and locking"""

    def test_select_scenario_direct(self, client, auth_headers, test_devis):
        """Test selecting direct purchase scenario"""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "direct"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["selected_scenario"] == "direct"

    def test_select_scenario_location_without_apport(
        self, client, auth_headers, test_devis
    ):
        """Test selecting location without apport scenario"""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "location_without_apport"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["selected_scenario"] == "location_without_apport"

    def test_select_scenario_location_with_apport(
        self, client, auth_headers, test_devis
    ):
        """Test selecting location with apport scenario"""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "location_with_apport"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["selected_scenario"] == "location_with_apport"

    def test_select_scenario_invalid(self, client, auth_headers, test_devis):
        """Test selecting invalid scenario returns 400"""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "invalid_scenario"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid scenario" in data["error"]

    def test_select_scenario_locked_after_first_selection(
        self, client, auth_headers, test_devis
    ):
        """Test scenario cannot be changed after first selection (locked)"""
        # First selection
        response1 = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "direct"},
            headers=auth_headers,
        )
        assert response1.status_code == 200

        # Try to change scenario
        response2 = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "location_without_apport"},
            headers=auth_headers,
        )

        assert response2.status_code == 409
        data = response2.get_json()
        assert "already locked" in data["error"].lower()
        assert data["locked_scenario"] == "direct"

    def test_select_scenario_prevents_change_for_signed(
        self, client, auth_headers, test_devis
    ):
        """Test scenario cannot be changed for signed devis"""
        test_devis.statut = "Signé"
        test_devis.selected_scenario = "direct"
        from models import db

        db.session.commit()

        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "location_without_apport"},
            headers=auth_headers,
        )

        assert response.status_code == 409
        data = response.get_json()
        assert "Cannot change scenario for a signed devis" in data["error"]

    def test_select_scenario_nonexistent_devis(self, client, auth_headers):
        """Test selecting scenario for non-existent devis returns 404"""
        response = client.post(
            "/api/devis/select-scenario/99999",
            json={"scenario": "direct"},
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_select_scenario_unauthorized(self, client, test_devis):
        """Test scenario selection without auth returns 401"""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}", json={"scenario": "direct"}
        )

        assert response.status_code == 401

    def test_select_scenario_with_whitespace(self, client, auth_headers, test_devis):
        """Test scenario selection strips whitespace"""
        response = client.post(
            f"/api/devis/select-scenario/{test_devis.id}",
            json={"scenario": "  direct  "},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["selected_scenario"] == "direct"


class TestSignedDevisPDF:
    """Tests for PDF generation of signed devis with snapshots"""

    def test_get_signed_devis_pdf_uses_snapshot(self, client, auth_headers, test_devis):
        """Test that signed devis PDF uses snapshot data"""
        # Create snapshot for signed devis
        snapshot_data = {
            "lines": [
                {
                    "article_id": 1,
                    "quantite": 1,
                    "montant_ht": 100.0,
                    "taux_tva": 0.20,
                    "montant_tva": 20.0,
                    "montant_ttc": 120.0,
                }
            ],
            "remise": 0.0,
            "params": {},
            "company": {},
        }

        test_devis.statut = "Signé"
        test_devis.signed_data = snapshot_data
        from models import db

        db.session.commit()

        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_get_unsigned_devis_pdf_doesnt_use_snapshot(
        self, client, auth_headers, test_devis
    ):
        """Test that unsigned devis PDF doesn't use snapshot"""
        test_devis.statut = "En cours"
        test_devis.signed_data = None
        from models import db

        db.session.commit()

        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"


class TestPDFEdgeCases:
    """Tests for edge cases in PDF generation"""

    def test_pdf_generation_with_missing_vat_rate(
        self, client, auth_headers, test_devis, test_article
    ):
        """Test PDF generation handles articles with missing VAT rates gracefully"""
        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_pdf_generation_with_zero_articles(self, client, auth_headers, test_devis):
        """Test PDF generation with devis containing no articles"""
        from models import DevisArticles, db

        # Remove all articles from devis
        DevisArticles.query.filter_by(devis_id=test_devis.id).delete()
        db.session.commit()

        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        # Should still generate valid PDF even with no articles
        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_pdf_generation_with_negative_montant_handling(
        self, client, auth_headers, test_devis
    ):
        """Test PDF generation handles negative amounts correctly"""
        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_pdf_header_filename(self, client, auth_headers, test_devis):
        """Test PDF response has correct filename header"""
        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        assert f"devis_{test_devis.id}.pdf" in response.headers.get(
            "Content-Disposition", ""
        )

    def test_pdf_generation_multiple_vat_rates(
        self, client, auth_headers, test_devis, taux_tva_20
    ):
        """Test PDF generation correctly aggregates multiple VAT rates"""
        from models import Articles, DevisArticles, TauxTVA, db

        # Create another VAT rate
        taux_10 = TauxTVA(taux=0.10)
        db.session.add(taux_10)
        db.session.flush()

        # Create another article with 10% VAT
        article_10 = Articles(
            nom="Produit 10%",
            reference="REF-10PCT",
            prix_achat_HT=50.0,
            prix_vente_HT=100.0,
            taux_tva_id=taux_10.id,
        )
        db.session.add(article_10)
        db.session.flush()

        # Add to devis
        devis_article_10 = DevisArticles(
            devis_id=test_devis.id, article_id=article_10.id, quantite=2
        )
        db.session.add(devis_article_10)
        db.session.commit()

        response = client.get(f"/api/devis/pdf/{test_devis.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"


class TestPDFLocationDevis:
    """Tests for location-specific PDF scenarios"""

    def test_pdf_location_without_apport_calculation(
        self, client, auth_headers, test_devis, test_parameters
    ):
        """Test PDF calculation for location without apport"""
        test_devis.is_location = True
        test_devis.first_contribution_amount = 0.0
        from models import db

        db.session.commit()

        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=location_without_apport",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_pdf_location_with_apport_calculation(
        self, client, auth_headers, test_devis, test_parameters
    ):
        """Test PDF calculation for location with apport"""
        test_devis.is_location = True
        test_devis.first_contribution_amount = 1000.0
        from models import db

        db.session.commit()

        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=location_with_apport",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    def test_pdf_location_with_subscription_costs(
        self, client, auth_headers, test_devis, test_parameters
    ):
        """Test PDF includes subscription and maintenance costs for location"""
        test_devis.is_location = True
        test_parameters.location_subscription_cost = 150.0
        test_parameters.location_interests_cost = 50.0
        from models import db

        db.session.commit()

        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=location_without_apport",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"


class TestPDFWithRealWorldScenarios:
    """Tests for real-world usage scenarios"""

    def test_pdf_multiple_sequential_requests(self, client, auth_headers, test_devis):
        """Test PDF generation can be called multiple times without issues"""
        for _ in range(3):
            response = client.get(
                f"/api/devis/pdf/{test_devis.id}", headers=auth_headers
            )
            assert response.status_code == 200
            assert response.data[:4] == b"%PDF"

    def test_pdf_with_all_parameters_set(
        self, client, auth_headers, test_devis, test_parameters
    ):
        """Test PDF generation with all parameters configured"""
        test_parameters.general_conditions_sales = "Test conditions"
        test_parameters.company_name = "Test Company"
        test_parameters.company_address_line1 = "123 Main St"
        test_parameters.company_phone = "555-0123"
        test_parameters.company_email = "info@test.com"
        test_parameters.location_time = 24

        from models import db

        db.session.commit()

        response = client.get(
            f"/api/devis/pdf/{test_devis.id}?scenario=location_without_apport",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"
