"""Recalculate devis totals server-side after migration to backend calculations

Revision ID: 001_recalc_devis
Revises: bee70c0965a6
Create Date: 2025-12-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from decimal import Decimal

# revision identifiers, used by Alembic.
revision = '001_recalc_devis'
down_revision = 'bee70c0965a6'
branch_labels = None
depends_on = None


def upgrade():
    """Recalculate totals for all unsigned devis using new server-side calculation logic"""
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Get all unsigned devis
        unsigned_devis = session.execute(
            sa.text("SELECT id FROM devis WHERE statut IN ('En attente', 'Accepté') OR statut NOT IN ('Signé', 'Annulé')")
        ).fetchall()
        
        for (devis_id,) in unsigned_devis:
            recalculate_devis_totals(session, devis_id)
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        session.close()


def recalculate_devis_totals(session, devis_id):
    """Recalculate montant_HT, montant_TVA, montant_TTC for a devis"""
    
    # Get all articles for this devis
    articles = session.execute(
        sa.text("""
            SELECT da.id, da.quantite, da.taux_tva, da.montant_HT, a.prix_vente_HT
            FROM devis_articles da
            JOIN articles a ON da.article_id = a.id
            WHERE da.devis_id = :devis_id
        """),
        {"devis_id": devis_id}
    ).fetchall()
    
    total_ht = Decimal('0.0')
    total_tva = Decimal('0.0')
    total_ttc = Decimal('0.0')
    
    for article_id, quantite, taux_tva, montant_ht, prix_vente_ht in articles:
        if prix_vente_ht is None:
            continue
        
        # Get TAX rate (default to 0.20 if not specified)
        taux = Decimal(taux_tva or '0.20')
        
        # Calculate line amounts
        qty = Decimal(str(quantite or 0))
        price = Decimal(str(prix_vente_ht))
        
        line_ht = price * qty
        line_tva = line_ht * taux
        line_ttc = line_ht + line_tva
        
        # Update article line amounts
        session.execute(
            sa.text("""
                UPDATE devis_articles
                SET montant_HT = :montant_ht, montant_TVA = :montant_tva, montant_TTC = :montant_ttc
                WHERE id = :article_id
            """),
            {
                "montant_ht": float(line_ht),
                "montant_tva": float(line_tva),
                "montant_ttc": float(line_ttc),
                "article_id": article_id
            }
        )
        
        total_ht += line_ht
        total_tva += line_tva
        total_ttc += line_ttc
    
    # Update devis totals
    session.execute(
        sa.text("""
            UPDATE devis
            SET montant_HT = :total_ht, montant_TVA = :total_tva, montant_TTC = :total_ttc
            WHERE id = :devis_id
        """),
        {
            "total_ht": float(total_ht),
            "total_tva": float(total_tva),
            "total_ttc": float(total_ttc),
            "devis_id": devis_id
        }
    )


def downgrade():
    """Downgrade - no action needed as we're recalculating from stored data"""
    pass
