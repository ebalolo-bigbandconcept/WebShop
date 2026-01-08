from flask import Blueprint, request, jsonify, session, render_template, make_response
from models import db, Devis, DevisSchema, DevisArticles, Articles, TauxTVA, Parameters
from datetime import datetime
from weasyprint import HTML
from PyPDF2 import PdfMerger
import io
import logging
import os

# Create a Blueprint for authentication-related routes
devis_bp = Blueprint('devis_bp', __name__, url_prefix='/api/devis')

def _build_article_map(articles_payload):
    article_ids = [article.get("article_id") for article in articles_payload if article.get("article_id")]
    if not article_ids:
        return {}
    articles = Articles.query.filter(Articles.id.in_(article_ids)).all()
    return {article.id: article for article in articles}


def _resolve_tva_id(article_payload, articles_map):
    taux_tva_id = article_payload.get("taux_tva_id")
    if taux_tva_id:
        return taux_tva_id

    taux_value = article_payload.get("taux_tva")
    if taux_value is not None:
        existing_tva = TauxTVA.query.filter_by(taux=taux_value).first()
        if existing_tva:
            return existing_tva.id
        new_tva = TauxTVA(taux=taux_value)
        db.session.add(new_tva)
        db.session.flush()
        return new_tva.id

    article = articles_map.get(article_payload.get("article_id"))
    return article.taux_tva_id if article else None


def _compute_unit_price(article_obj, params, is_location):
    if not article_obj:
        return 0.0
    if is_location:
        rate = (params.margin_rate_location if params else 0.0) or 0.0
        return float(article_obj.prix_achat_HT or 0.0) * rate
    return float(article_obj.prix_vente_HT or 0.0)


# Public endpoint to list all VAT rates (no admin required)
@devis_bp.route('/tva', methods=['GET'])
def list_vat_public():
    vats = TauxTVA.query.order_by(TauxTVA.id.asc()).all()
    return jsonify({"data": [{"id": v.id, "taux": v.taux} for v in vats]})

# Get every devis of every devis route
@devis_bp.route('/all', methods=['GET'])
def get_every_devis():
    devis = Devis.query.order_by(Devis.id.asc()).all()
    if len(devis) == 0:
        return jsonify({"error": "Aucuns devis trouvé"}), 404
    
    devis_schema = DevisSchema(many=True)
    devis_data = devis_schema.dump(devis)
    return jsonify(data=devis_data)

# Get every devis of a client route
@devis_bp.route('/client/<client_id>', methods=['GET'])
def get_client_devis(client_id):
    devis = Devis.query.filter_by(client_id=client_id).order_by(Devis.id.asc()).all()
    if not devis:
        return jsonify({"error": "Aucuns devis trouvé"}), 404
    
    devis_schema = DevisSchema(many=True)
    devis_data = devis_schema.dump(devis)
    return jsonify(data=devis_data)

# Get specific devis info route
@devis_bp.route('/info/<devis_id>', methods=['GET'])
def get_devis_info(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404
    
    devis_schema = DevisSchema()
    return devis_schema.jsonify(devis)

# Get new devis id route (for display in front only)
@devis_bp.route('/new-id', methods=['GET'])
def get_new_devis_id():
    new_devis_id = Devis.query.order_by(Devis.id.desc()).first()
    if new_devis_id is None:
        return jsonify({
            "id": 1
        })
        
    return jsonify({
        "id": new_devis_id.id + 1
    })

# Create new devis route
@devis_bp.route('/create', methods=['POST'])
def create_devis():
    titre = request.json["title"]
    description = request.json["description"]
    date = datetime.strptime(request.json["date"],"%Y-%m-%d").date()
    montant_HT = request.json["montant_HT"]
    montant_TVA = request.json["montant_TVA"]
    montant_TTC = request.json["montant_TTC"]
    remise = float(request.json.get("remise", 0.0) or 0.0)
    statut = request.json["statut"]
    client_id = request.json["client_id"]
    articles_data = request.json["articles"]
    is_location = request.json.get("is_location", False)
    first_contribution_amount = request.json.get("first_contribution_amount")
    location_monthly_total = request.json.get("location_monthly_total")
    location_monthly_total_ht = request.json.get("location_monthly_total_ht")
    location_total = request.json.get("location_total")
    location_total_ht = request.json.get("location_total_ht")
    
    new_devis = Devis(
        client_id=client_id,
        titre=titre,
        description=description,
        date=date,
        montant_HT=montant_HT,
        montant_TVA=montant_TVA,
        montant_TTC=montant_TTC,
        remise=remise,
        statut=statut,
        is_location=is_location,
        first_contribution_amount=first_contribution_amount,
        location_monthly_total=location_monthly_total,
        location_monthly_total_ht=location_monthly_total_ht,
        location_total=location_total,
        location_total_ht=location_total_ht,
    )
    db.session.add(new_devis)
    db.session.flush()
    
    articles_map = _build_article_map(articles_data)
    for article in articles_data:
        tva_id = _resolve_tva_id(article, articles_map)
        devis_article = DevisArticles(
            devis_id=new_devis.id,
            article_id=article["article_id"],
            quantite=article['quantite'],
            taux_tva_id=tva_id,
            commentaire=article.get('commentaire')
        )
        db.session.add(devis_article)
        
    db.session.commit()
    logging.info(f"Nouveau devis créé: {new_devis.titre} (id: {new_devis.id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "id": new_devis.id
    })

# Update devis route
@devis_bp.route('/update/<devis_id>', methods=['PUT'])
def update_devis(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404

    if devis.statut == "Signé":
        return jsonify({"error": "Devis signé: modification interdite"}), 409
    
    # Check if status is changing to "Signé" BEFORE updating the status
    to_sign = devis.statut != "Signé" and request.json.get("statut") == "Signé"
    
    devis.titre = request.json["title"]
    devis.description = request.json["description"]
    devis.date = datetime.strptime(request.json["date"],"%Y-%m-%d").date()
    devis.montant_HT = request.json["montant_HT"]
    devis.montant_TVA = request.json["montant_TVA"]
    devis.montant_TTC = request.json["montant_TTC"]
    devis.remise = float(request.json.get("remise", devis.remise) or 0.0)
    devis.statut = request.json["statut"]
    devis.is_location = request.json.get("is_location", False)
    devis.first_contribution_amount = request.json.get("first_contribution_amount")
    devis.location_monthly_total = request.json.get("location_monthly_total")
    devis.location_monthly_total_ht = request.json.get("location_monthly_total_ht")
    devis.location_total = request.json.get("location_total")
    devis.location_total_ht = request.json.get("location_total_ht")
    articles_data = request.json["articles"]
    params = Parameters.query.first()
    remise_value = float(request.json.get("remise") or 0.0)
    
    try:
        DevisArticles.query.filter_by(devis_id=devis.id).delete()

        articles_map = _build_article_map(articles_data)
        snapshot_lines = []
        total_ht = 0.0
        total_tva = 0.0
        total_ttc = 0.0

        for article in articles_data:
            tva_id = _resolve_tva_id(article, articles_map)
            article_obj = articles_map.get(article["article_id"])
            unit_price = _compute_unit_price(article_obj, params, False)  # Always use normal pricing for devis storage
            taux_val = 0.0
            if tva_id:
                tva_obj = TauxTVA.query.get(tva_id)
                taux_val = float(tva_obj.taux) if tva_obj else 0.0
            elif article_obj and article_obj.taux_tva:
                taux_val = float(article_obj.taux_tva.taux)

            qty = float(article["quantite"])
            line_ht = unit_price * qty
            line_tva = line_ht * (taux_val or 0.0)
            line_ttc = line_ht + line_tva

            devis_article = DevisArticles(
                devis_id=devis.id,
                article_id=article["article_id"],
                quantite=article["quantite"],
                taux_tva_id=tva_id,
                commentaire=article.get('commentaire')
            )

            if to_sign:
                devis_article.prix_unitaire_ht_snapshot = unit_price
                devis_article.taux_tva_snapshot = taux_val
                devis_article.montant_ht_snapshot = line_ht
                devis_article.montant_tva_snapshot = line_tva
                devis_article.montant_ttc_snapshot = line_ttc

            db.session.add(devis_article)

            total_ht += line_ht
            total_tva += line_tva
            total_ttc += line_ttc

            if to_sign:
                snapshot_lines.append({
                    "article_id": article_obj.id if article_obj else article.get("article_id"),
                    "nom": getattr(article_obj, "nom", ""),
                    "reference": getattr(article_obj, "reference", ""),
                    "quantite": qty,
                    "taux_tva": taux_val,
                    "prix_unitaire_ht": unit_price,
                    "montant_ht": line_ht,
                    "montant_tva": line_tva,
                    "montant_ttc": line_ttc,
                    "commentaire": article.get('commentaire') or "",
                })

        if to_sign:
            devis.montant_HT = round(total_ht, 2)
            devis.montant_TVA = round(total_tva, 2)
            devis.montant_TTC = round(total_ttc, 2)
            devis.signed_at = datetime.utcnow()
            devis.signed_data = {
                "lines": snapshot_lines,
                "totals": {
                    "ht": round(total_ht, 2),
                    "tva": round(total_tva, 2),
                    "ttc": round(total_ttc, 2),
                    "ttc_after_remise": round(max(total_ttc - remise_value, 0.0), 2),
                },
                "remise": round(remise_value, 2),
                "params": {
                    "margin_rate": params.margin_rate if params else 0.0,
                    "margin_rate_location": params.margin_rate_location if params else 0.0,
                    "location_subscription_cost": params.location_subscription_cost if params else 0.0,
                    "location_interests_cost": params.location_interests_cost if params else 0.0,
                    "location_time": params.location_time if params else 0,
                    "general_conditions_sales": params.general_conditions_sales if params else "",
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
                    "is_location": devis.is_location,
                    "first_contribution_amount": devis.first_contribution_amount,
                    "location_monthly_total": devis.location_monthly_total,
                    "location_monthly_total_ht": devis.location_monthly_total_ht,
                    "location_total": devis.location_total,
                    "location_total_ht": devis.location_total_ht,
                },
            }

        db.session.commit()

        logging.info(f"Devis modifié: {devis.titre} (id: {devis.id}) par l'utilisateur {session.get('user_id')}")

        return jsonify({
            "id": devis.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Delete devis route
@devis_bp.route('/delete/<devis_id>', methods=['DELETE'])
def delete_devis(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Article non trouvé"}), 404

    if devis.statut == "Signé":
        return jsonify({"error": "Devis signé: suppression interdite"}), 409
    
    devis_nom = devis.titre
    # Delete devis articles first to avoid foreign key constraint violation
    DevisArticles.query.filter_by(devis_id=devis.id).delete()
    Devis.query.filter_by(id=devis_id).delete()
    db.session.commit()
    logging.info(f"Devis supprimé: {devis_nom} (id: {devis_id}) par l'utilisateur {session.get('user_id')}")
    
    return jsonify({
        "200": "Devis successfully deleted."
    })

# Create PDF of the devis
@devis_bp.route('/pdf/<devis_id>', methods=['GET'])
def get_devis_pdf(devis_id):
    devis = Devis.query.filter_by(id=devis_id).first()
    if not devis:
        return jsonify({"error": "Devis non trouvé"}), 404

    # Scenario selection for PDF rendering
    selected_scenario = request.args.get("scenario") or "direct"
    if selected_scenario not in {"direct", "location_without_apport", "location_with_apport"}:
        selected_scenario = "direct"
    
    # Convert Devis object to dict including articles
    devis_schema = DevisSchema()
    devis_data = devis_schema.dump(devis)

    snapshot = devis.signed_data if devis.statut == "Signé" and getattr(devis, "signed_data", None) else None

    # Fetch parameters early for general conditions, location duration and fees
    params = Parameters.query.first()

    # Remise should always be considered (even if no scenario selected)
    try:
        remise_value = float(snapshot.get("remise")) if snapshot and snapshot.get("remise") is not None else float(devis_data.get("remise") or 0.0)
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
                bucket = vat_totals_map.setdefault(taux, {"total_ht": 0.0, "total_tva": 0.0, "total_ttc": 0.0})
                bucket["total_ht"] += line_ht
                bucket["total_tva"] += line_tva
                bucket["total_ttc"] += line_ttc
            except Exception:
                continue
    else:
        # Determine if we should use location pricing
        use_location_pricing = selected_scenario in {"location_without_apport", "location_with_apport"}
        
        for item in devis_data.get('articles', []):
            try:
                taux = None
                if item.get('taux_tva') and item['taux_tva'].get('taux') is not None:
                    taux = float(item['taux_tva']['taux'])
                else:
                    taux = float(item['article']['taux_tva']['taux'])

                qty = float(item.get('quantite') or 0)
                
                # Use location pricing for location scenarios
                if use_location_pricing:
                    prix_achat = float(item.get('article', {}).get('prix_achat_HT') or 0)
                    margin_rate_location = (params.margin_rate_location if params else 0.0) or 0.0
                    unit_ht = prix_achat * margin_rate_location if prix_achat > 0 and margin_rate_location > 0 else float(item.get('article', {}).get('prix_vente_HT') or 0)
                else:
                    unit_ht = float(item.get('article', {}).get('prix_vente_HT') or 0)
                
                line_ht = qty * unit_ht
                line_tva = line_ht * (taux or 0.0)
                line_ttc = line_ht + line_tva

                bucket = vat_totals_map.setdefault(taux, {"total_ht": 0.0, "total_tva": 0.0, "total_ttc": 0.0})
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

    def _compute_location_totals(apport_value):
        apport = float(apport_value or 0.0)
        
        # Calculate articles total TTC from vat_totals_map (this includes location pricing adjustments)
        articles_ttc = sum(bucket["total_ttc"] for bucket in vat_totals_map.values())
        
        # Subscription and maintenance are already TTC
        subscription_ttc_value = float(subscription_ttc or 0.0)
        maintenance_ttc_value = float(maintenance_ttc or 0.0)
        
        # Total HT = articles TTC + subscription + maintenance - apport
        total_ht_value = articles_ttc + subscription_ttc_value + maintenance_ttc_value - apport
        total_ht_value = max(total_ht_value, 0.0)
        
        # Calculate TTC from HT (multiply by 1.20)
        total_ttc_value = total_ht_value * 1.20

        monthly_ht = (total_ht_value / location_time) if location_time else 0.0
        monthly_ttc = (total_ttc_value / location_time) if location_time else 0.0

        return {
            "monthly_ht": round(monthly_ht, 2),
            "monthly_ttc": round(monthly_ttc, 2),
            "total_ht": round(total_ht_value, 2),
            "total_ttc": round(total_ttc_value, 2),
            "total_tva": round(total_ttc_value - total_ht_value, 2),
            "apport": round(apport, 2),
        }

    # Build a minimal map for 20% and 10% showing only total TVA
    # For location scenarios, preserve article VAT breakdown and add subscription/maintenance VAT
    vat_tva_totals = {}
    payment_options = {}
    
    logging.info(f"Before scenario check - vat_totals_map: {vat_totals_map}")
    logging.info(f"Selected scenario: {selected_scenario}")
    
    # For location scenarios, recalculate article prices with location pricing
    articles_to_display = devis_data.get('articles', [])
    if selected_scenario in {"location_without_apport", "location_with_apport"}:
        # Create a copy of articles with location pricing
        articles_to_display = []
        for item in devis_data.get('articles', []):
            try:
                prix_achat = float(item.get('article', {}).get('prix_achat_HT') or 0)
                margin_rate_location = (params.margin_rate_location if params else 0.0) or 0.0
                unit_ht_location = prix_achat * margin_rate_location if prix_achat > 0 and margin_rate_location > 0 else float(item.get('article', {}).get('prix_vente_HT') or 0)
                
                # Create modified article with location pricing
                modified_item = item.copy()
                if 'article' in modified_item:
                    modified_item['article'] = modified_item['article'].copy()
                    modified_item['article']['prix_vente_HT'] = unit_ht_location
                articles_to_display.append(modified_item)
            except Exception:
                articles_to_display.append(item)
    
    if selected_scenario in {"location_without_apport", "location_with_apport"}:
        # Calculate location totals first
        location_without = _compute_location_totals(0.0)
        location_with = _compute_location_totals(devis_data.get("first_contribution_amount"))
        
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
            "location_without_apport": _compute_location_totals(0.0),
            "location_with_apport": _compute_location_totals(devis_data.get("first_contribution_amount")),
        }

    # Create a copy of devis_data with modified articles for location scenarios
    devis_display = devis_data.copy()
    devis_display['articles'] = articles_to_display
    
    # For location scenarios, update the article totals to match location pricing
    if selected_scenario in {"location_without_apport", "location_with_apport"}:
        articles_ht_total = sum(bucket["total_ht"] for bucket in vat_totals_map.values())
        articles_tva_total = sum(bucket["total_tva"] for bucket in vat_totals_map.values())
        articles_ttc_total = articles_ht_total + articles_tva_total
        
        devis_display['montant_HT'] = round(articles_ht_total, 2)
        devis_display['montant_TVA'] = round(articles_tva_total, 2)
        devis_display['montant_TTC'] = round(articles_ttc_total, 2)

    effective_remise = remise_value
    ttc_after_remise_display = max(float(devis_display.get('montant_TTC') or 0.0) - effective_remise, 0.0)
    devis_display['remise'] = round(effective_remise, 2)
    devis_display['ttc_after_remise'] = round(ttc_after_remise_display, 2)

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
    )
    
    # Calculate the absolute path to the folder containing your template and static files
    base_path = '/app/pdf/'

    # Generate PDF
    pdf_bytes = HTML(string=html_out, base_url=base_path).write_pdf()

    # Append location contract only for location scenarios
    if devis.is_location and selected_scenario in {"location_without_apport", "location_with_apport"}:
        try:
            contract_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pdf", "location_contract.pdf"))
            if os.path.isfile(contract_path):
                merged = PdfMerger()
                merged.append(io.BytesIO(pdf_bytes))
                merged.append(contract_path)
                buffer = io.BytesIO()
                merged.write(buffer)
                pdf_bytes = buffer.getvalue()
            else:
                logging.warning(f"Location contract PDF not found at {contract_path}; returning devis PDF only.")
        except Exception as merge_err:
            logging.exception(f"Failed to append location contract PDF: {merge_err}")

    # Return PDF as response
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=devis_{devis_id}.pdf"
    return response

# Save the selected scenario to the devis
@devis_bp.route('/select-scenario/<devis_id>', methods=['POST'])
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
        return jsonify({"error": f"Invalid scenario. Must be one of {valid_scenarios}"}), 400

    # Prevent changing scenario if already signed
    if devis.statut == "Signé":
        return jsonify({
            "error": "Cannot change scenario for a signed devis",
            "current_scenario": devis.selected_scenario
        }), 409

    # Prevent changing scenario if already selected (lock it)
    if devis.selected_scenario and devis.selected_scenario != scenario:
        return jsonify({
            "error": "Scenario already locked. Cannot change after first selection",
            "locked_scenario": devis.selected_scenario,
            "attempted_scenario": scenario
        }), 409

    # Save the selected scenario
    devis.selected_scenario = scenario
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Scenario '{scenario}' successfully selected and locked",
        "devis_id": devis_id,
        "selected_scenario": scenario
    }), 200
