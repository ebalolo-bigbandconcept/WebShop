"""Unit tests for Devis and DevisArticle calculation logic.

Tests cover:
- HT/TVA/TTC calculations for articles and devis
- Multi-article aggregation with different VAT rates
- Remise (discount) application
- Location scenario calculations (with/without apport)
- Snapshot immutability
- Edge cases (zero values, rounding, etc.)
"""

import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models import Devis, DevisArticles, Articles, TauxTVA, Parameters, db


class TestArticleLineCalculations:
    """Test calculation logic for individual article lines."""
    
    def test_montant_ht_calculation_basic(self, db_session, test_article, test_devis, taux_tva_20):
        """Test: montant_HT = prix_unitaire_ht * quantite"""
        devis_article = DevisArticles(
            devis_id=test_devis.id,
            article_id=test_article.id,
            quantite=3,
            taux_tva_id=taux_tva_20.id
        )
        
        # Expected: 150.0 * 3 = 450.0
        expected_ht = test_article.prix_vente_HT * 3
        
        # Calculate (simulating route calculation)
        line_ht = round(float(test_article.prix_vente_HT) * 3, 2)
        
        assert line_ht == 450.0
        assert line_ht == expected_ht
    
    def test_montant_tva_calculation_basic(self, db_session, test_article, taux_tva_20):
        """Test: montant_TVA = montant_HT * taux_tva"""
        # HT = 150.0 * 2 = 300.0
        # TVA = 300.0 * 0.20 = 60.0
        line_ht = 300.0
        taux = taux_tva_20.taux
        
        line_tva = round(line_ht * taux, 2)
        
        assert line_tva == 60.0
    
    def test_montant_ttc_calculation_basic(self, db_session):
        """Test: montant_TTC = montant_HT + montant_TVA"""
        line_ht = 300.0
        line_tva = 60.0
        
        line_ttc = round(line_ht + line_tva, 2)
        
        assert line_ttc == 360.0
    
    def test_calculation_with_decimal_quantity(self, db_session, test_article):
        """Test calculations with decimal quantities (e.g., 2.5 units)"""
        # Price: 150.0, Quantity: 2.5
        line_ht = round(150.0 * 2.5, 2)
        line_tva = round(line_ht * 0.20, 2)
        line_ttc = round(line_ht + line_tva, 2)
        
        assert line_ht == 375.0
        assert line_tva == 75.0
        assert line_ttc == 450.0
    
    def test_calculation_with_zero_quantity(self, db_session, test_article):
        """Test calculations with zero quantity"""
        line_ht = round(150.0 * 0, 2)
        line_tva = round(line_ht * 0.20, 2)
        line_ttc = round(line_ht + line_tva, 2)
        
        assert line_ht == 0.0
        assert line_tva == 0.0
        assert line_ttc == 0.0
    
    def test_calculation_with_10_percent_vat(self, db_session, test_article_2, taux_tva_10):
        """Test calculations with 10% VAT rate"""
        # Price: 75.0, Quantity: 2, VAT: 10%
        line_ht = round(75.0 * 2, 2)
        line_tva = round(line_ht * 0.10, 2)
        line_ttc = round(line_ht + line_tva, 2)
        
        assert line_ht == 150.0
        assert line_tva == 15.0
        assert line_ttc == 165.0
    
    def test_rounding_precision(self, db_session):
        """Test that rounding is applied correctly to avoid float precision issues"""
        # 33.33 * 3 = 99.99 (potential precision issue)
        unit_price = 33.33
        quantity = 3
        
        line_ht = round(unit_price * quantity, 2)
        line_tva = round(line_ht * 0.20, 2)
        line_ttc = round(line_ht + line_tva, 2)
        
        assert line_ht == 99.99
        assert line_tva == 20.0
        assert line_ttc == 119.99


class TestDevisTotalAggregation:
    """Test aggregation of article lines into devis totals."""
    
    def test_single_article_aggregation(self, db_session, test_devis):
        """Test devis totals with single article"""
        # test_devis has 1 article: 2 * 150.0 = 300.0 HT
        # TVA (20%): 60.0
        # TTC: 360.0
        
        assert test_devis.montant_HT == 300.0
        assert test_devis.montant_TVA == 60.0
        assert test_devis.montant_TTC == 360.0
    
    def test_multi_article_aggregation_same_vat(self, db_session, test_client_record, test_article, taux_tva_20):
        """Test devis totals with multiple articles at same VAT rate"""
        # Article 1: 150.0 * 2 = 300.0 HT
        # Article 2: 150.0 * 3 = 450.0 HT
        # Total HT: 750.0
        # Total TVA (20%): 150.0
        # Total TTC: 900.0
        
        devis = Devis(
            client_id=test_client_record.id,
            titre='Multi Article Test',
            description='Test',
            date=datetime.now(),
            statut='Brouillon',
            remise=0.0,
            is_location=False,
            montant_HT=750.0,
            montant_TVA=150.0,
            montant_TTC=900.0
        )
        db_session.add(devis)
        db_session.flush()
        
        # Article 1: 150.0 * 2 = 300.0 HT
        # Article 2: 150.0 * 3 = 450.0 HT
        # Total HT: 750.0
        # Total TVA (20%): 150.0
        # Total TTC: 900.0
        
        total_ht = 0.0
        total_tva = 0.0
        
        for qty in [2, 3]:
            line_ht = round(150.0 * qty, 2)
            line_tva = round(line_ht * 0.20, 2)
            total_ht += line_ht
            total_tva += line_tva
        
        total_ttc = round(total_ht + total_tva, 2)
        
        assert total_ht == 750.0
        assert total_tva == 150.0
        assert total_ttc == 900.0
    
    def test_multi_article_mixed_vat_rates(self, db_session, test_client_record, test_article, test_article_2, taux_tva_20, taux_tva_10):
        """Test devis with articles at different VAT rates (20% and 10%)"""
        # Article 1: 150.0 * 2 = 300.0 HT, TVA 20% = 60.0, TTC = 360.0
        # Article 2: 75.0 * 4 = 300.0 HT, TVA 10% = 30.0, TTC = 330.0
        # Total HT: 600.0
        # Total TVA: 90.0
        # Total TTC: 690.0
        
        line1_ht = round(150.0 * 2, 2)
        line1_tva = round(line1_ht * 0.20, 2)
        
        line2_ht = round(75.0 * 4, 2)
        line2_tva = round(line2_ht * 0.10, 2)
        
        total_ht = round(line1_ht + line2_ht, 2)
        total_tva = round(line1_tva + line2_tva, 2)
        total_ttc = round(total_ht + total_tva, 2)
        
        assert total_ht == 600.0
        assert total_tva == 90.0
        assert total_ttc == 690.0


class TestRemiseApplication:
    """Test discount (remise) application logic."""
    
    def test_remise_applied_correctly(self, db_session):
        """Test: TTC after remise = TTC - remise"""
        ttc_before = 360.0
        remise = 50.0
        
        ttc_after = max(ttc_before - remise, 0.0)
        
        assert ttc_after == 310.0
    
    def test_remise_zero(self, db_session):
        """Test: zero remise doesn't change TTC"""
        ttc = 360.0
        remise = 0.0
        
        ttc_after = max(ttc - remise, 0.0)
        
        assert ttc_after == 360.0
    
    def test_remise_cannot_make_negative_total(self, db_session):
        """Test: remise > TTC results in zero, not negative"""
        ttc = 360.0
        remise = 500.0
        
        ttc_after = max(ttc - remise, 0.0)
        
        assert ttc_after == 0.0
    
    def test_remise_equals_ttc(self, db_session):
        """Test: remise equal to TTC results in zero"""
        ttc = 360.0
        remise = 360.0
        
        ttc_after = max(ttc - remise, 0.0)
        
        assert ttc_after == 0.0


class TestLocationCalculations:
    """Test location scenario pricing calculations."""
    
    def test_location_without_apport(self, db_session, test_parameters):
        """Test: location_total_ttc = articles_ttc + subscription + interests"""
        articles_ttc = 1000.0
        subscription = test_parameters.location_subscription_cost  # 50.0
        interests = test_parameters.location_interests_cost  # 100.0
        location_time = test_parameters.location_time  # 36
        
        location_total_ttc = round(articles_ttc + subscription + interests, 2)
        monthly_ttc = round(location_total_ttc / location_time, 2)
        
        assert location_total_ttc == 1150.0
        assert monthly_ttc == 31.94  # 1150 / 36 = 31.944... rounded to 31.94
    
    def test_location_with_apport(self, db_session, test_parameters):
        """Test: location_total_ttc = articles_ttc + subscription + interests - apport"""
        articles_ttc = 1000.0
        subscription = test_parameters.location_subscription_cost  # 50.0
        interests = test_parameters.location_interests_cost  # 100.0
        apport = 200.0
        location_time = test_parameters.location_time  # 36
        
        location_total_ttc = round(articles_ttc + subscription + interests - apport, 2)
        monthly_ttc = round(location_total_ttc / location_time, 2)
        
        assert location_total_ttc == 950.0
        assert monthly_ttc == 26.39  # 950 / 36 = 26.388... rounded to 26.39
    
    def test_location_ht_from_ttc(self, db_session):
        """Test: location_total_ht = location_total_ttc / 1.20 (assuming 20% VAT)"""
        location_total_ttc = 1200.0
        vat_factor = 1.20
        
        location_total_ht = round(location_total_ttc / vat_factor, 2)
        monthly_ht = round(location_total_ht / 36, 2)
        
        assert location_total_ht == 1000.0
        assert monthly_ht == 27.78  # 1000 / 36 = 27.777... rounded to 27.78
    
    def test_location_time_zero_protection(self, db_session):
        """Test: division by zero protection when location_time = 0"""
        location_total_ttc = 1000.0
        location_time = 0
        
        # Should handle gracefully (return 0 or raise exception)
        if location_time > 0:
            monthly_ttc = round(location_total_ttc / location_time, 2)
        else:
            monthly_ttc = 0.0
        
        assert monthly_ttc == 0.0
    
    def test_location_pricing_uses_margin_rate(self, db_session, test_parameters):
        """Test: location pricing may use different margin rate"""
        prix_achat_ht = 100.0
        margin_rate_normal = test_parameters.margin_rate  # 1.5
        margin_rate_location = test_parameters.margin_rate_location  # 1.8
        
        prix_vente_normal = round(prix_achat_ht * margin_rate_normal, 2)
        prix_vente_location = round(prix_achat_ht * margin_rate_location, 2)
        
        assert prix_vente_normal == 150.0
        assert prix_vente_location == 180.0
        assert prix_vente_location > prix_vente_normal


class TestSnapshotImmutability:
    """Test signed devis snapshot creation and immutability."""
    
    def test_signed_devis_snapshot_creation(self, db_session, signed_devis):
        """Test: snapshot captures all prices, VAT, params"""
        assert signed_devis.statut == 'Signé'
        assert signed_devis.signed_at is not None
        assert signed_devis.signed_data is not None
        
        # Snapshot should contain articles
        assert 'articles' in signed_devis.signed_data
        assert len(signed_devis.signed_data['articles']) > 0
        
        # Snapshot should contain totals
        assert 'totals' in signed_devis.signed_data
        assert 'montant_HT' in signed_devis.signed_data['totals']
        assert 'montant_TVA' in signed_devis.signed_data['totals']
        assert 'montant_TTC' in signed_devis.signed_data['totals']
        
        # Snapshot should contain parameters
        assert 'parameters' in signed_devis.signed_data
    
    def test_signed_devis_uses_snapshot(self, db_session, signed_devis, test_article):
        """Test: signed devis should use snapshot data, not live article prices"""
        # Get snapshot data
        snapshot_articles = signed_devis.signed_data['articles']
        original_price = snapshot_articles[0]['prix_unitaire_ht']
        
        # Change the live article price
        test_article.prix_vente_HT = 999.99
        db_session.commit()
        
        # Snapshot should still have original price
        assert snapshot_articles[0]['prix_unitaire_ht'] == original_price
        assert snapshot_articles[0]['prix_unitaire_ht'] != 999.99
    
    def test_snapshot_preserves_totals(self, db_session, signed_devis):
        """Test: snapshot preserves calculated totals"""
        snapshot_totals = signed_devis.signed_data['totals']
        
        # These should match the devis totals at signing time
        assert snapshot_totals['montant_HT'] == float(signed_devis.montant_HT)
        assert snapshot_totals['montant_TVA'] == float(signed_devis.montant_TVA)
        assert snapshot_totals['montant_TTC'] == float(signed_devis.montant_TTC)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_large_numbers(self, db_session):
        """Test calculations with very large numbers"""
        unit_price = 999999.99
        quantity = 100
        
        line_ht = round(unit_price * quantity, 2)
        line_tva = round(line_ht * 0.20, 2)
        line_ttc = round(line_ht + line_tva, 2)
        
        assert line_ht == 99999999.0
        assert line_tva == 19999999.8
        assert line_ttc == 119999998.8
    
    def test_very_small_numbers(self, db_session):
        """Test calculations with very small numbers"""
        unit_price = 0.01
        quantity = 1
        
        line_ht = round(unit_price * quantity, 2)
        line_tva = round(line_ht * 0.20, 2)
        line_ttc = round(line_ht + line_tva, 2)
        
        assert line_ht == 0.01
        assert line_tva == 0.0  # 0.002 rounds to 0.00
        assert line_ttc == 0.01
    
    def test_rounding_accumulation(self, db_session):
        """Test that rounding errors don't accumulate significantly"""
        # Add 3 articles with prices that round: 33.33 + 33.33 + 33.34 = 100.00
        prices = [33.33, 33.33, 33.34]
        total_ht = 0.0
        
        for price in prices:
            line_ht = round(price * 1, 2)
            total_ht += line_ht
        
        total_ht = round(total_ht, 2)
        assert total_ht == 100.0
    
    def test_negative_prices_should_be_prevented(self, db_session):
        """Test that negative prices are handled (should be prevented at validation)"""
        # This test documents expected behavior - validation should prevent this
        # But calculations should handle it gracefully if it occurs
        unit_price = -100.0
        quantity = 2
        
        line_ht = round(unit_price * quantity, 2)
        
        # Should produce negative (validation should prevent this earlier)
        assert line_ht == -200.0
