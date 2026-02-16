import io
import logging
import os
from datetime import datetime

from flask import Blueprint, jsonify, make_response, render_template, request, session
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from weasyprint import HTML

from models import (
    Devis,
    DevisArticles,
    DevisSchema,
    EnvelopeTracking,
    Parameters,
    TauxTVA,
    db,
)
from services.calculations import (
    LOCATION_VAT_RATE,
    build_article_map,
    compute_article_lines,
    compute_location_display_totals,
    compute_location_totals,
    resolve_article_vat,
)
from utils import require_login

# Create a Blueprint for authentication-related routes
devis_bp = Blueprint("devis_bp", __name__, url_prefix="/api/devis")


# Public endpoint to list all VAT rates
@devis_bp.route("/tva", methods=["GET"])
@require_login({"Administrateur", "Utilisateur"})
def list_vat_public():
    vats = TauxTVA.query.order_by(TauxTVA.id.asc()).all()
    return jsonify({"data": [{"id": v.id, "taux": v.taux} for v in vats]})


# Get every devis of every devis route
@devis_bp.route("/all", methods=["GET"])
@require_login({"Administrateur", "Utilisateur"})
def get_every_devis():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # Ensure reasonable pagination values
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Max 100 items per page

    paginated = Devis.query.order_by(Devis.id.desc()).paginate(
        page=page, per_page=per_page
    )

    if paginated.total == 0:
        return jsonify({"error": "Aucuns devis trouvé"}), 404

    devis_schema = DevisSchema(many=True)
    devis_data = devis_schema.dump(paginated.items)

    return jsonify(
        {
            "data": devis_data,
            "pagination": {
                "current_page": page,
                "total_pages": paginated.pages,
                "total_items": paginated.total,
                "per_page": per_page,
                "has_next": paginated.has_next,
                "has_prev": paginated.has_prev,
            },
        }
    )


# Get every devis of a client route
@devis_bp.route("/client/<client_id>", methods=["GET"])
@require_login({"Administrateur", "Utilisateur"})
def get_client_devis(client_id):
    devis = Devis.query.filter_by(client_id=client_id).order_by(Devis.id.asc()).all()
    if not devis:
        return jsonify({"error": "Aucuns devis trouvé"}), 404

    devis_schema = DevisSchema(many=True)
    devis_data = devis_schema.dump(devis)
    return jsonify(data=devis_data)


# Get specific devis info route
@devis_bp.route("/info/<devis_id>", methods=["GET"])
@require_login({"Administrateur", "Utilisateur"})
def get_devis_info(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404

    # For signed devis with snapshot data, use the snapshot
    if devis.statut == "Signé" and devis.signed_data:
        snapshot = devis.signed_data

        # Reconstruct articles from snapshot
        articles_data = []
        for line in snapshot.get("lines", []):
            has_designation = "designation" in line
            designation_value = (
                line.get("designation") if has_designation else line.get("reference")
            )
            reference_value = line.get("reference") if has_designation else ""
            articles_data.append(
                {
                    "id": line.get("article_id"),
                    "article": {
                        "id": line.get("article_id"),
                        "nom": line.get("nom"),
                        "designation": designation_value,
                        "reference": reference_value,
                    },
                    "quantite": line.get("quantite"),
                    "taux_tva": {"taux": line.get("taux_tva")},
                    "montant_HT": line.get("montant_ht"),
                    "montant_TVA": line.get("montant_tva"),
                    "montant_TTC": line.get("montant_ttc"),
                    "commentaire": line.get("commentaire", ""),
                }
            )

        # Build response from snapshot
        devis_schema = DevisSchema()
        devis_data = devis_schema.dump(devis)
        devis_data["articles"] = articles_data

        return jsonify(devis_data)

    # For unsigned devis, use normal serialization
    devis_schema = DevisSchema()
    return devis_schema.jsonify(devis)


# Get new devis id route (for display in front only)
@devis_bp.route("/new-id", methods=["GET"])
@require_login({"Administrateur", "Utilisateur"})
def get_new_devis_id():
    new_devis_id = Devis.query.order_by(Devis.id.desc()).first()
    if new_devis_id is None:
        return jsonify({"id": 1})

    return jsonify({"id": new_devis_id.id + 1})


# Create new devis route
@devis_bp.route("/create", methods=["POST"])
@require_login({"Administrateur", "Utilisateur"})
def create_devis():
    body = request.get_json(force=True) if request.data else {}
    titre = body.get("titre") if body.get("titre") is not None else body.get("title")
    description = body.get("description")
    date = datetime.strptime(body.get("date"), "%Y-%m-%d").date()
    remise = float(body.get("remise", 0.0) or 0.0)
    statut = body.get("statut")
    client_id = body.get("client_id")
    articles_data = body.get("articles") or []
    is_location = body.get("is_location", False)
    selected_scenario = body.get("selected_scenario")
    first_contribution_amount = float(
        (
            body.get("location_apport")
            if body.get("location_apport") is not None
            else body.get("first_contribution_amount", 0.0)
        )
        or 0.0
    )
    location_subscription_cost = float(
        body.get("location_subscription_cost", 0.0) or 0.0
    )
    location_interests_cost = float(body.get("location_interests_cost", 0.0) or 0.0)
    location_time = int(body.get("location_time", 12) or 12)

    # Compute article line amounts server-side
    articles_map = build_article_map(articles_data)
    lines, total_ht, total_tva, total_ttc = compute_article_lines(
        articles_data, articles_map, is_location
    )

    # Compute location totals if applicable
    location_total_ht = 0.0
    location_total_ttc = 0.0
    location_monthly_ht = 0.0
    location_monthly_ttc = 0.0
    if is_location:
        (
            location_total_ht,
            location_total_ttc,
            location_monthly_ht,
            location_monthly_ttc,
        ) = compute_location_totals(
            total_ttc,
            first_contribution_amount,
            location_subscription_cost,
            location_interests_cost,
            location_time,
        )

    new_devis = Devis(
        client_id=client_id,
        titre=titre,
        description=description,
        date=date,
        montant_HT=total_ht,  # Use computed value
        montant_TVA=total_tva,  # Use computed value
        montant_TTC=total_ttc,  # Use computed value
        remise=remise,
        statut=statut,
        is_location=is_location,
        selected_scenario=selected_scenario,
        first_contribution_amount=first_contribution_amount,
        location_monthly_total=location_monthly_ttc,
        location_monthly_total_ht=location_monthly_ht,
        location_total=location_total_ttc,
        location_total_ht=location_total_ht,
    )
    db.session.add(new_devis)
    db.session.flush()

    # Create DevisArticles records
    for article_payload in articles_data:
        article_obj = articles_map.get(article_payload.get("article_id"))
        if not article_obj:
            continue

        taux_val, tva_id = resolve_article_vat(
            article_payload, article_obj, articles_map, is_location
        )

        # Calculate line amounts
        unit_price = float(article_obj.prix_vente_HT or 0.0)
        qty = float(article_payload.get("quantite") or 1)
        line_ht = round(unit_price * qty, 2)
        line_tva = round(line_ht * taux_val, 2)
        line_ttc = round(line_ht + line_tva, 2)

        devis_article = DevisArticles(
            devis_id=new_devis.id,
            article_id=article_obj.id,
            quantite=qty,
            taux_tva_id=tva_id,
            commentaire=article_payload.get("commentaire"),
            montant_HT=line_ht,
            montant_TVA=line_tva,
            montant_TTC=line_ttc,
        )
        db.session.add(devis_article)

    db.session.commit()
    logging.info(
        f"Nouveau devis créé: {new_devis.titre} (id: {new_devis.id}) par l'utilisateur {session.get('user_id')}"
    )

    # Return computed structure
    devis_schema = DevisSchema()
    devis_data = devis_schema.dump(new_devis)

    return (
        jsonify(
            {
                "id": new_devis.id,
                "computed": {
                    "montant_ht": total_ht,
                    "montant_tva": total_tva,
                    "montant_ttc": total_ttc,
                    "location_total_ht": location_total_ht,
                    "location_total_ttc": location_total_ttc,
                    "location_monthly_ht": location_monthly_ht,
                    "location_monthly_ttc": location_monthly_ttc,
                },
            }
        ),
        201,
    )


# Update devis route
@devis_bp.route("/update/<devis_id>", methods=["PUT"])
@require_login({"Administrateur", "Utilisateur"})
def update_devis(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404

    if devis.statut == "Signé":
        return jsonify({"error": "Devis signé: modification interdite"}), 409

    # Check if status is changing to "Signé" BEFORE updating the status
    to_sign = devis.statut != "Signé" and request.json.get("statut") == "Signé"

    body = request.get_json(force=True) if request.data else {}
    titre = body.get("titre") if body.get("titre") is not None else body.get("title")
    description = body.get("description")
    date = datetime.strptime(body.get("date"), "%Y-%m-%d").date()
    remise = float(body.get("remise", 0.0) or 0.0)
    statut = body.get("statut")
    articles_data = body.get("articles") or []
    is_location = body.get("is_location", False)
    selected_scenario = body.get("selected_scenario")
    first_contribution_amount = float(
        (
            body.get("location_apport")
            if body.get("location_apport") is not None
            else body.get("first_contribution_amount", 0.0)
        )
        or 0.0
    )
    location_subscription_cost = float(
        body.get("location_subscription_cost", 0.0) or 0.0
    )
    location_interests_cost = float(body.get("location_interests_cost", 0.0) or 0.0)
    location_time = int(body.get("location_time", 12) or 12)

    # Compute article line amounts server-side
    articles_map = build_article_map(articles_data)
    lines, total_ht, total_tva, total_ttc = compute_article_lines(
        articles_data, articles_map, is_location
    )

    # Compute location totals if applicable
    location_total_ht = 0.0
    location_total_ttc = 0.0
    location_monthly_ht = 0.0
    location_monthly_ttc = 0.0
    if is_location:
        (
            location_total_ht,
            location_total_ttc,
            location_monthly_ht,
            location_monthly_ttc,
        ) = compute_location_totals(
            total_ttc,
            first_contribution_amount,
            location_subscription_cost,
            location_interests_cost,
            location_time,
        )

    params = Parameters.query.first()

    try:
        # Update devis main fields
        devis.titre = titre
        devis.description = description
        devis.date = date
        devis.montant_HT = total_ht
        devis.montant_TVA = total_tva
        devis.montant_TTC = total_ttc
        devis.remise = remise
        devis.statut = statut
        devis.is_location = is_location
        devis.selected_scenario = selected_scenario
        devis.first_contribution_amount = first_contribution_amount
        devis.location_monthly_total = location_monthly_ttc
        devis.location_monthly_total_ht = location_monthly_ht
        devis.location_total = location_total_ttc
        devis.location_total_ht = location_total_ht

        # Delete old articles
        DevisArticles.query.filter_by(devis_id=devis.id).delete()

        # Create new DevisArticles records
        snapshot_lines = []
        for article_payload in articles_data:
            article_obj = articles_map.get(article_payload.get("article_id"))
            if not article_obj:
                continue

            taux_val, tva_id = resolve_article_vat(
                article_payload, article_obj, articles_map, is_location
            )

            # Get unit price and line amounts from pre-computed lines
            unit_price = float(article_obj.prix_vente_HT or 0.0)
            qty = float(article_payload.get("quantite") or 1)
            line_ht = round(unit_price * qty, 2)
            line_tva = round(line_ht * taux_val, 2)
            line_ttc = round(line_ht + line_tva, 2)

            devis_article = DevisArticles(
                devis_id=devis.id,
                article_id=article_obj.id,
                quantite=qty,
                taux_tva_id=tva_id,
                commentaire=article_payload.get("commentaire"),
                montant_HT=line_ht,
                montant_TVA=line_tva,
                montant_TTC=line_ttc,
            )

            if to_sign:
                devis_article.prix_unitaire_ht_snapshot = unit_price
                devis_article.taux_tva_snapshot = taux_val
                devis_article.montant_ht_snapshot = line_ht
                devis_article.montant_tva_snapshot = line_tva
                devis_article.montant_ttc_snapshot = line_ttc

                snapshot_lines.append(
                    {
                        "article_id": article_obj.id,
                        "nom": article_obj.nom,
                        "designation": article_obj.designation,
                        "reference": article_obj.reference,
                        "quantite": qty,
                        "taux_tva": taux_val,
                        "prix_unitaire_ht": unit_price,
                        "montant_ht": line_ht,
                        "montant_tva": line_tva,
                        "montant_ttc": line_ttc,
                        "commentaire": article_payload.get("commentaire") or "",
                    }
                )

            db.session.add(devis_article)

        # Create snapshot if signing
        if to_sign:
            devis.signed_at = datetime.utcnow()
            devis.signed_data = {
                "lines": snapshot_lines,
                "totals": {
                    "ht": total_ht,
                    "tva": total_tva,
                    "ttc": total_ttc,
                    "ttc_after_remise": round(max(total_ttc - remise, 0.0), 2),
                },
                "remise": round(remise, 2),
                "params": {
                    "margin_rate": params.margin_rate if params else 0.0,
                    "margin_rate_location": (
                        params.margin_rate_location if params else 0.0
                    ),
                    "location_subscription_cost": (
                        params.location_subscription_cost if params else 0.0
                    ),
                    "location_interests_cost": (
                        params.location_interests_cost if params else 0.0
                    ),
                    "location_time": params.location_time if params else 0,
                    "general_conditions_sales": (
                        params.general_conditions_sales if params else ""
                    ),
                },
                "company": {
                    "name": params.company_name if params else "",
                    "address_line1": params.company_address_line1 if params else "",
                    "address_line2": params.company_address_line2 if params else "",
                    "zip": params.company_zip if params else "",
                    "city": params.company_city if params else "",
                    "phone": params.company_phone if params else "",
                    "email": params.company_email if params else "",
                    "iban": params.company_iban if params else "",
                    "tva": params.company_tva if params else "",
                    "siret": params.company_siret if params else "",
                    "aprm": params.company_aprm if params else "",
                },
                "location": {
                    "is_location": is_location,
                    "first_contribution_amount": first_contribution_amount,
                    "location_monthly_total": location_monthly_ttc,
                    "location_monthly_total_ht": location_monthly_ht,
                    "location_total": location_total_ttc,
                    "location_total_ht": location_total_ht,
                },
            }

        db.session.commit()
        logging.info(
            f"Devis modifié: {devis.titre} (id: {devis.id}) par l'utilisateur {session.get('user_id')}"
        )

        devis_schema = DevisSchema()
        devis_data = devis_schema.dump(devis)

        return jsonify({"message": "Devis mis à jour avec succès"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Delete devis route
@devis_bp.route("/delete/<devis_id>", methods=["DELETE"])
@require_login({"Administrateur", "Utilisateur"})
def delete_devis(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404

    if devis.statut == "Signé":
        return jsonify({"error": "Devis signé: suppression interdite"}), 409

    devis_nom = devis.titre
    DevisArticles.query.filter_by(devis_id=devis.id).delete()
    EnvelopeTracking.query.filter_by(devis_id=devis.id).delete()
    Devis.query.filter_by(id=devis_id).delete()
    db.session.commit()
    logging.info(
        f"Devis supprimé: {devis_nom} (id: {devis_id}) par l'utilisateur {session.get('user_id')}"
    )

    return jsonify({"message": "Devis supprimé avec succès"})


# Create PDF of the devis
@devis_bp.route("/pdf/<devis_id>", methods=["GET"])
@require_login({"Administrateur", "Utilisateur"})
def get_devis_pdf(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404

    # Scenario selection for PDF rendering
    selected_scenario = request.args.get("scenario") or "direct"
    if selected_scenario not in {
        "direct",
        "location_without_apport",
        "location_with_apport",
    }:
        selected_scenario = "direct"

    # Convert Devis object to dict including articles
    devis_schema = DevisSchema()
    devis_data = devis_schema.dump(devis)

    snapshot = (
        devis.signed_data
        if devis.statut == "Signé" and getattr(devis, "signed_data", None)
        else None
    )

    # Fetch parameters early for general conditions, location duration and fees
    params = Parameters.query.first()

    # Remise should always be considered (even if no scenario selected)
    try:
        remise_value = (
            float(snapshot.get("remise"))
            if snapshot and snapshot.get("remise") is not None
            else float(devis_data.get("remise") or 0.0)
        )
    except Exception:
        remise_value = 0.0
    direct_base_ttc = float(devis_data.get("montant_TTC") or devis.montant_TTC or 0.0)
    direct_ttc_after_remise = max(direct_base_ttc - remise_value, 0.0)

    # Compute totals by VAT rate from per-line or article default
    vat_totals_map = {}

    if snapshot and snapshot.get("lines"):
        for line in snapshot.get("lines", []):
            try:
                taux = float(line.get("taux_tva") or 0.0)
                line_ht = float(line.get("montant_ht") or 0.0)
                line_tva = float(line.get("montant_tva") or 0.0)
                line_ttc = float(line.get("montant_ttc") or (line_ht + line_tva))
                bucket = vat_totals_map.setdefault(
                    taux, {"total_ht": 0.0, "total_tva": 0.0, "total_ttc": 0.0}
                )
                bucket["total_ht"] += line_ht
                bucket["total_tva"] += line_tva
                bucket["total_ttc"] += line_ttc
            except Exception:
                continue
    else:
        # Determine if we should use location pricing
        use_location_pricing = selected_scenario in {
            "location_without_apport",
            "location_with_apport",
        }

        for item in devis_data.get("articles", []):
            try:
                taux = None
                if item.get("taux_tva") and item["taux_tva"].get("taux") is not None:
                    taux = float(item["taux_tva"]["taux"])
                else:
                    taux = float(item["article"]["taux_tva"]["taux"])

                # For location scenarios: always enforce VAT 20% for articles
                if use_location_pricing:
                    taux = 0.20

                qty = float(item.get("quantite") or 0)

                # Use location pricing for location scenarios
                if use_location_pricing:
                    prix_achat = float(
                        item.get("article", {}).get("prix_achat_HT") or 0
                    )
                    margin_rate_location = (
                        params.margin_rate_location if params else 0.0
                    ) or 0.0
                    unit_ht = (
                        prix_achat * margin_rate_location
                        if prix_achat > 0 and margin_rate_location > 0
                        else float(item.get("article", {}).get("prix_vente_HT") or 0)
                    )
                else:
                    unit_ht = float(item.get("article", {}).get("prix_vente_HT") or 0)

                line_ht = qty * unit_ht
                line_tva = line_ht * (taux or 0.0)
                line_ttc = line_ht + line_tva

                bucket = vat_totals_map.setdefault(
                    taux, {"total_ht": 0.0, "total_tva": 0.0, "total_ttc": 0.0}
                )
                bucket["total_ht"] += line_ht
                bucket["total_tva"] += line_tva
                bucket["total_ttc"] += line_ttc
            except Exception:
                # Skip malformed items silently for PDF rendering
                continue

    # Additional parameter fetching for conditions, location duration and fees
    if snapshot:
        params_block = snapshot.get("params", {})
        company_block = snapshot.get("company", {})
        general_conditions = params_block.get("general_conditions_sales", "")
        location_time = params_block.get("location_time", 0)
        subscription_ttc = params_block.get("location_subscription_cost", 0.0)
        maintenance_ttc = params_block.get("location_interests_cost", 0.0)
        company_info = {
            "name": company_block.get("name", ""),
            "address_line1": company_block.get("address_line1", ""),
            "address_line2": company_block.get("address_line2", ""),
            "zip": company_block.get("zip", ""),
            "city": company_block.get("city", ""),
            "phone": company_block.get("phone", ""),
            "email": company_block.get("email", ""),
            "iban": company_block.get("iban", ""),
            "tva": company_block.get("tva", ""),
            "siret": company_block.get("siret", ""),
            "aprm": company_block.get("aprm", ""),
        }
    else:
        general_conditions = params.general_conditions_sales if params else ""
        location_time = params.location_time if params else 0
        subscription_ttc = params.location_subscription_cost if params else 0.0
        maintenance_ttc = params.location_interests_cost if params else 0.0
        company_info = {
            "name": params.company_name if params else "",
            "address_line1": params.company_address_line1 if params else "",
            "address_line2": params.company_address_line2 if params else "",
            "zip": params.company_zip if params else "",
            "city": params.company_city if params else "",
            "phone": params.company_phone if params else "",
            "email": params.company_email if params else "",
            "iban": params.company_iban if params else "",
            "tva": params.company_tva if params else "",
            "siret": params.company_siret if params else "",
            "aprm": params.company_aprm if params else "",
        }

    # Build a minimal map for 20% and 10% showing only total TVA
    # For location scenarios, preserve article VAT breakdown and add subscription/maintenance VAT
    vat_tva_totals = {}
    payment_options = {}

    logging.info(f"Before scenario check - vat_totals_map: {vat_totals_map}")
    logging.info(f"Selected scenario: {selected_scenario}")

    articles_ttc = sum(bucket["total_ttc"] for bucket in vat_totals_map.values())
    subscription_ttc_value = float(subscription_ttc or 0.0)
    maintenance_ttc_value = float(maintenance_ttc or 0.0)

    # For location scenarios, recalculate article prices with location pricing
    articles_to_display = devis_data.get("articles", [])
    if selected_scenario in {"location_without_apport", "location_with_apport"}:
        # Create a copy of articles with location pricing
        articles_to_display = []
        for item in devis_data.get("articles", []):
            try:
                prix_achat = float(item.get("article", {}).get("prix_achat_HT") or 0)
                margin_rate_location = (
                    params.margin_rate_location if params else 0.0
                ) or 0.0
                unit_ht_location = (
                    prix_achat * margin_rate_location
                    if prix_achat > 0 and margin_rate_location > 0
                    else float(item.get("article", {}).get("prix_vente_HT") or 0)
                )

                # Create modified article with location pricing
                modified_item = item.copy()
                if "article" in modified_item:
                    modified_item["article"] = modified_item["article"].copy()
                    modified_item["article"]["prix_vente_HT"] = unit_ht_location
                articles_to_display.append(modified_item)
            except Exception:
                articles_to_display.append(item)

    if selected_scenario in {"location_without_apport", "location_with_apport"}:
        # Calculate location totals first
        location_without = compute_location_display_totals(
            articles_ttc,
            subscription_ttc_value,
            maintenance_ttc_value,
            0.0,
            location_time,
            LOCATION_VAT_RATE,
        )
        location_with = compute_location_display_totals(
            articles_ttc,
            subscription_ttc_value,
            maintenance_ttc_value,
            devis_data.get("first_contribution_amount"),
            location_time,
            LOCATION_VAT_RATE,
        )

        # Build VAT recap based on articles only
        # For location scenarios, we show all VAT rates from articles (without location VAT)
        vat_tva_totals = {}

        # Copy article-level VAT breakdown (from location pricing)
        for taux, bucket in vat_totals_map.items():
            vat_tva_totals[taux] = round(bucket["total_tva"], 2)

        payment_options = {
            "direct": {"total_ttc": round(direct_ttc_after_remise, 2)},
            "location_without_apport": location_without,
            "location_with_apport": location_with,
        }
    else:
        # For direct purchase, use the article-level VAT breakdown
        for taux, bucket in vat_totals_map.items():
            vat_tva_totals[taux] = round(bucket["total_tva"], 2)

        payment_options = {
            "direct": {"total_ttc": round(direct_ttc_after_remise, 2)},
            "location_without_apport": compute_location_display_totals(
                articles_ttc,
                subscription_ttc_value,
                maintenance_ttc_value,
                0.0,
                location_time,
                LOCATION_VAT_RATE,
            ),
            "location_with_apport": compute_location_display_totals(
                articles_ttc,
                subscription_ttc_value,
                maintenance_ttc_value,
                devis_data.get("first_contribution_amount"),
                location_time,
                LOCATION_VAT_RATE,
            ),
        }

    # Create a copy of devis_data with modified articles for location scenarios
    devis_display = devis_data.copy()
    devis_display["articles"] = articles_to_display

    # For location scenarios, update the article totals to match location pricing
    if selected_scenario in {"location_without_apport", "location_with_apport"}:
        articles_ht_total = sum(
            bucket["total_ht"] for bucket in vat_totals_map.values()
        )
        articles_tva_total = sum(
            bucket["total_tva"] for bucket in vat_totals_map.values()
        )
        articles_ttc_total = articles_ht_total + articles_tva_total

        devis_display["montant_HT"] = round(articles_ht_total, 2)
        devis_display["montant_TVA"] = round(articles_tva_total, 2)
        devis_display["montant_TTC"] = round(articles_ttc_total, 2)

    effective_remise = remise_value
    ttc_after_remise_display = max(
        float(devis_display.get("montant_TTC") or 0.0) - effective_remise, 0.0
    )
    devis_display["remise"] = round(effective_remise, 2)
    devis_display["ttc_after_remise"] = round(ttc_after_remise_display, 2)

    # Determine devis title based on scenario
    if selected_scenario == "location_with_apport":
        devis_title = "Devis de location avec apport"
    elif selected_scenario == "location_without_apport":
        devis_title = "Devis de location sans apport"
    else:
        devis_title = "Devis"

    # Render HTML using Jinja2 template
    html_out = render_template(
        "pdf.html",
        devis=devis_display,
        vat_tva_totals=vat_tva_totals,
        general_conditions=general_conditions,
        location_time=location_time,
        company=company_info,
        selected_scenario=selected_scenario,
        payment_options=payment_options,
        remise=devis_display.get("remise", 0.0),
        ttc_after_remise=ttc_after_remise_display,
        devis_title=devis_title,
    )

    # Calculate the absolute path to the folder containing your template and static files
    base_path = "/app/pdf/"

    # Generate PDF
    pdf_bytes = HTML(string=html_out, base_url=base_path).write_pdf()

    # Append location contract only for location scenarios
    if devis.is_location and selected_scenario in {
        "location_without_apport",
        "location_with_apport",
    }:
        try:
            contract_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "..", "pdf", "location_contract.pdf"
                )
            )
            if os.path.isfile(contract_path):
                # Read both PDFs
                devis_pdf = PdfReader(io.BytesIO(pdf_bytes))
                contract_pdf = PdfReader(contract_path)

                # Get the number of pages in both documents
                devis_page_count = len(devis_pdf.pages)
                contract_page_count = len(contract_pdf.pages)
                total_page_count = devis_page_count + contract_page_count

                # Create a new PDF writer
                writer = PdfWriter()

                # Add page numbers to devis pages
                for i, page in enumerate(devis_pdf.pages):
                    page_num = i + 1

                    # Create a PDF with just the page number
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=A4)

                    can.setFont("Helvetica", 10)
                    can.setFillColorRGB(0.333, 0.333, 0.333)  # #555 color
                    can.drawRightString(
                        A4[0] - 40, 32, f"Page {page_num} / {total_page_count}"
                    )

                    can.save()
                    packet.seek(0)

                    # Merge the page number with the devis page
                    page_num_pdf = PdfReader(packet)
                    page.merge_page(page_num_pdf.pages[0])
                    writer.add_page(page)

                # Add page numbers to contract pages
                for i, page in enumerate(contract_pdf.pages):
                    page_num = devis_page_count + i + 1

                    # Create a PDF with just the page number
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=A4)

                    can.setFont("Helvetica", 10)
                    can.setFillColorRGB(0.333, 0.333, 0.333)  # #555 color
                    can.drawRightString(
                        A4[0] - 40, 32, f"Page {page_num} / {total_page_count}"
                    )

                    can.save()
                    packet.seek(0)

                    # Merge the page number with the contract page
                    page_num_pdf = PdfReader(packet)
                    page.merge_page(page_num_pdf.pages[0])
                    writer.add_page(page)

                # Write to buffer
                buffer = io.BytesIO()
                writer.write(buffer)
                pdf_bytes = buffer.getvalue()

                logging.info(
                    f"Merged devis ({devis_page_count} pages) with location contract ({contract_page_count} pages) - total {total_page_count} pages with continuous numbering"
                )
            else:
                logging.warning(
                    f"Location contract PDF not found at {contract_path}; returning devis PDF only."
                )
        except Exception as merge_err:
            logging.exception(f"Failed to append location contract PDF: {merge_err}")
    else:
        # For direct scenario, just update page numbers on devis
        try:
            devis_pdf = PdfReader(io.BytesIO(pdf_bytes))
            devis_page_count = len(devis_pdf.pages)

            writer = PdfWriter()

            # Add page numbers to devis pages
            for i, page in enumerate(devis_pdf.pages):
                page_num = i + 1

                # Create a PDF with just the page number
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=A4)

                can.setFont("Helvetica", 10)
                can.setFillColorRGB(0.333, 0.333, 0.333)  # #555 color
                can.drawRightString(
                    A4[0] - 40, 32, f"Page {page_num} / {devis_page_count}"
                )

                can.save()
                packet.seek(0)

                # Merge the page number with the devis page
                page_num_pdf = PdfReader(packet)
                page.merge_page(page_num_pdf.pages[0])
                writer.add_page(page)

            # Write to buffer
            buffer = io.BytesIO()
            writer.write(buffer)
            pdf_bytes = buffer.getvalue()
        except Exception as e:
            logging.exception(f"Failed to add page numbers to devis: {e}")
            # Continue with original pdf_bytes if numbering fails

    # Return PDF as response
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=devis_{devis_id}.pdf"
    return response


# Save the selected scenario to the devis
@devis_bp.route("/select-scenario/<devis_id>", methods=["POST"])
@require_login({"Administrateur", "Utilisateur"})
def select_scenario(devis_id):
    """
    Save the client's selected scenario for this devis.
    Prevents scenario from being changed once locked.
    """
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404

    data = request.get_json()
    scenario = data.get("scenario", "direct").strip()

    # Validate scenario
    valid_scenarios = {"direct", "location_without_apport", "location_with_apport"}
    if scenario not in valid_scenarios:
        return (
            jsonify({"error": f"Invalid scenario. Must be one of {valid_scenarios}"}),
            400,
        )

    # Prevent changing scenario if already signed
    if devis.statut == "Signé":
        return (
            jsonify(
                {
                    "error": "Cannot change scenario for a signed devis",
                    "current_scenario": devis.selected_scenario,
                }
            ),
            409,
        )

    # Prevent changing scenario if already selected (lock it)
    if devis.selected_scenario and devis.selected_scenario != scenario:
        return (
            jsonify(
                {
                    "error": "Scenario already locked. Cannot change after first selection",
                    "locked_scenario": devis.selected_scenario,
                    "attempted_scenario": scenario,
                }
            ),
            409,
        )

    # Save the selected scenario
    devis.selected_scenario = scenario
    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "message": "Scenario selected successfully",
                "devis_id": devis_id,
                "selected_scenario": scenario,
            }
        ),
        200,
    )
