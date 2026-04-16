"""Targeted unit tests for services/calculations.py coverage gaps."""

from models import Articles, TauxTVA, db
from services.calculations import (
    build_article_map,
    compute_article_lines,
    compute_monthly_from_total_ttc,
    ensure_tva_rate_id,
    resolve_article_vat,
    resolve_tva_id,
)


class TestCalculationsCoverage:
    def test_build_article_map_returns_empty_without_ids(self):
        payload = [{"article_id": None}, {}, {"article_id": 0}]

        article_map = build_article_map(payload)

        assert article_map == {}

    def test_ensure_tva_rate_id_creates_missing_rate(self, db_session):
        initial_count = TauxTVA.query.count()

        new_id = ensure_tva_rate_id(0.245)

        assert new_id is not None
        assert TauxTVA.query.count() == initial_count + 1
        assert TauxTVA.query.get(new_id).taux == 0.245

    def test_resolve_tva_id_with_dict_creates_rate(self):
        tva_id = resolve_tva_id({"taux_tva": {"taux": "0.133"}}, {})

        assert tva_id is not None
        assert TauxTVA.query.get(tva_id).taux == 0.133

    def test_resolve_tva_id_falls_back_to_article_map(self, taux_tva_20):
        article = Articles(
            nom="Fallback article",
            designation="FB-001",
            reference="FB-REF",
            prix_achat_HT=10.0,
            prix_vente_HT=20.0,
            location_price=5.0,
            taux_tva_id=taux_tva_20.id,
        )
        db.session.add(article)
        db.session.commit()

        tva_id = resolve_tva_id({"article_id": article.id}, {article.id: article})

        assert tva_id == taux_tva_20.id

    def test_resolve_article_vat_uses_article_relationship_when_no_tva_id(
        self, taux_tva_20
    ):
        article = Articles(
            nom="VAT relation",
            designation="VR-001",
            reference="VR-REF",
            prix_achat_HT=20.0,
            prix_vente_HT=30.0,
            location_price=8.0,
            taux_tva_id=taux_tva_20.id,
        )
        db.session.add(article)
        db.session.commit()

        taux_val, tva_id = resolve_article_vat(
            article_payload={"article_id": article.id},
            article_obj=article,
            articles_map={article.id: article},
            is_location=False,
        )

        assert tva_id == taux_tva_20.id
        assert taux_val == 0.2

    def test_compute_article_lines_location_uses_location_price(self, taux_tva_20):
        article = Articles(
            nom="Location priced",
            designation="LC-001",
            reference="LC-REF",
            prix_achat_HT=50.0,
            prix_vente_HT=100.0,
            location_price=12.0,
            taux_tva_id=taux_tva_20.id,
        )
        db.session.add(article)
        db.session.commit()

        lines, total_ht, total_tva, total_ttc = compute_article_lines(
            articles_data=[{"article_id": article.id, "quantite": 3}],
            articles_map={article.id: article},
            is_location=True,
            location_time=12,
        )

        assert len(lines) == 1
        assert lines[0]["unit_price_ht"] == 144.0
        assert total_ht == 432.0
        assert total_tva == 86.4
        assert total_ttc == 518.4

    def test_compute_monthly_from_total_ttc_handles_zero_duration(self):
        monthly_ht, monthly_ttc = compute_monthly_from_total_ttc(1200.0, 0)

        assert monthly_ht == 0.0
        assert monthly_ttc == 0.0

    def test_compute_monthly_from_total_ttc_uses_direct_division(self):
        monthly_ht, monthly_ttc = compute_monthly_from_total_ttc(1100.0, 36)

        assert monthly_ttc == 1100.0 / 36
        assert monthly_ht == 1100.0 / (1.2 * 36)
