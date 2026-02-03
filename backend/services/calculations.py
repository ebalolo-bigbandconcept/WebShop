import math

from models import Articles, InterestRateRange, TauxTVA, db

LOCATION_VAT_RATE = 0.20


def build_article_map(articles_payload):
    article_ids = [
        article.get("article_id")
        for article in articles_payload
        if article.get("article_id")
    ]
    if not article_ids:
        return {}
    articles = Articles.query.filter(Articles.id.in_(article_ids)).all()
    return {article.id: article for article in articles}


def ensure_tva_rate_id(rate):
    rate_value = float(rate)
    existing_tva = TauxTVA.query.filter_by(taux=rate_value).first()
    if existing_tva:
        return existing_tva.id
    new_tva = TauxTVA(taux=rate_value)
    db.session.add(new_tva)
    db.session.flush()
    return new_tva.id


def resolve_tva_id(article_payload, articles_map):
    taux_tva_id = article_payload.get("taux_tva_id")
    if taux_tva_id:
        return taux_tva_id

    taux_value = article_payload.get("taux_tva")
    if taux_value is not None:
        # Handle case where taux_tva is a dict with "taux" key
        if isinstance(taux_value, dict):
            taux_value = taux_value.get("taux")

        if taux_value is not None:
            taux_value = float(taux_value)
            existing_tva = TauxTVA.query.filter_by(taux=taux_value).first()
            if existing_tva:
                return existing_tva.id
            new_tva = TauxTVA(taux=taux_value)
            db.session.add(new_tva)
            db.session.flush()
            return new_tva.id

    article = articles_map.get(article_payload.get("article_id"))
    return article.taux_tva_id if article else None


def resolve_article_vat(article_payload, article_obj, articles_map, is_location):
    if is_location:
        taux_val = LOCATION_VAT_RATE
        tva_id = ensure_tva_rate_id(LOCATION_VAT_RATE)
        return taux_val, tva_id

    tva_id = resolve_tva_id(article_payload, articles_map)
    taux_val = 0.0
    if tva_id:
        tva_obj = TauxTVA.query.get(tva_id)
        taux_val = float(tva_obj.taux) if tva_obj else 0.0
    elif article_obj and article_obj.taux_tva:
        taux_val = float(article_obj.taux_tva.taux)

    return taux_val, tva_id


def compute_article_lines(articles_data, articles_map, is_location=False):
    """
    Compute line amounts for each article: montant_HT, montant_TVA, montant_TTC
    Returns: list of dicts with computed values, and totals
    """
    lines = []
    total_ht = 0.0
    total_tva = 0.0
    total_ttc = 0.0

    for article_payload in articles_data:
        article_obj = articles_map.get(article_payload.get("article_id"))
        if not article_obj:
            continue

        # Get unit price (normal pricing, not location)
        unit_price = float(article_obj.prix_vente_HT or 0.0)
        qty = float(article_payload.get("quantite") or 1)

        taux_val, _ = resolve_article_vat(
            article_payload, article_obj, articles_map, is_location
        )

        # Compute line amounts
        line_ht = round(unit_price * qty, 2)
        line_tva = round(line_ht * taux_val, 2)
        line_ttc = round(line_ht + line_tva, 2)

        lines.append(
            {
                "article_id": article_obj.id,
                "nom": article_obj.nom,
                "reference": article_obj.reference,
                "quantite": qty,
                "unit_price_ht": unit_price,
                "taux_tva": taux_val,
                "montant_ht": line_ht,
                "montant_tva": line_tva,
                "montant_ttc": line_ttc,
                "commentaire": article_payload.get("commentaire") or "",
            }
        )

        total_ht += line_ht
        total_tva += line_tva
        total_ttc += line_ttc

    return lines, round(total_ht, 2), round(total_tva, 2), round(total_ttc, 2)


def compute_monthly_from_total_ttc(
    total_ttc_value, location_time, vat_rate=LOCATION_VAT_RATE
):
    location_time_int = int(location_time or 0)
    if location_time_int <= 0:
        return 0.0, 0.0

    monthly_ttc_raw = total_ttc_value / location_time_int
    monthly_ttc = math.ceil(monthly_ttc_raw)
    monthly_ht = round(monthly_ttc / (1 + vat_rate), 2)
    return monthly_ht, monthly_ttc


def compute_location_totals(
    total_ttc,
    first_contribution,
    location_subscription_cost,
    location_interests_cost,
    location_time,
):
    """
    Compute location payment plan totals
    Assumes 20% VAT for location costs (subscription + interests)
    The interest is now calculated based on interest_rate_ranges table
    """
    if location_time <= 0:
        return 0.0, 0.0, 0.0, 0.0

    subscription_ttc = float(location_subscription_cost or 0.0)
    articles_ttc = float(total_ttc or 0.0)
    apport = float(first_contribution or 0.0)

    # Calculate the base total before interests
    base_total_ttc = articles_ttc + subscription_ttc - apport
    
    # Calculate monthly TTC (not rounded) to determine the total for interest lookup
    monthly_ttc_raw = base_total_ttc / location_time
    total_for_interest_lookup = monthly_ttc_raw * location_time
    
    # Look up the interest rate from the database based on the total
    interest_amount = 0.0
    interest_range = InterestRateRange.query.filter(
        InterestRateRange.minimum <= total_for_interest_lookup,
        InterestRateRange.maximum > total_for_interest_lookup
    ).first()
    
    if interest_range:
        interest_amount = float(interest_range.interests)
    
    # Calculate final total with interest
    total_ttc_location = base_total_ttc + interest_amount
    total_ht_location = total_ttc_location / (1 + LOCATION_VAT_RATE)

    monthly_ht, monthly_ttc = compute_monthly_from_total_ttc(
        total_ttc_location, location_time, LOCATION_VAT_RATE
    )

    return (
        round(total_ht_location, 2),
        round(total_ttc_location, 2),
        monthly_ht,
        monthly_ttc,
    )


def compute_location_display_totals(
    articles_ttc,
    subscription_ttc,
    maintenance_ttc,
    apport,
    location_time,
    vat_rate=LOCATION_VAT_RATE,
):
    # Ensure apport is not None
    apport_value = float(apport or 0.0)
    total_ht_value = articles_ttc + subscription_ttc + maintenance_ttc - apport_value
    total_ht_value = max(total_ht_value, 0.0)

    total_ttc_value = total_ht_value * (1 + vat_rate)
    monthly_ht, monthly_ttc = compute_monthly_from_total_ttc(
        total_ttc_value, location_time, vat_rate
    )

    return {
        "monthly_ht": monthly_ht,
        "monthly_ttc": monthly_ttc,
        "total_ht": round(total_ht_value, 2),
        "total_ttc": round(total_ttc_value, 2),
        "total_tva": round(total_ttc_value - total_ht_value, 2),
        "apport": round(apport_value, 2),
    }
