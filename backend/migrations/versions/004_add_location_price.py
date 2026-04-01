"""Add location_price subscription field to articles

Revision ID: 004_add_location_price
Revises: a4f1c2d3e5b6
Create Date: 2026-04-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "004_add_location_price"
down_revision = "a4f1c2d3e5b6"
branch_labels = None
depends_on = None


def upgrade():
    # Add the location_price column to articles table
    # Use simple ALTER TABLE which works directly with PostgreSQL
    conn = op.get_bind()

    # Check if column already exists (for idempotency)
    result = conn.execute(sa.text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='articles' AND column_name='location_price'
        """))

    if not result.fetchone():
        # Column doesn't exist, add it
        op.execute(sa.text("ALTER TABLE articles ADD COLUMN location_price FLOAT"))

        # Backfill existing articles: set location_price to prix_vente_HT
        op.execute(
            sa.text(
                'UPDATE articles SET location_price = "prix_vente_HT" WHERE location_price IS NULL'
            )
        )


def downgrade():
    # Remove the location_price column
    conn = op.get_bind()

    # Check if column exists before dropping
    result = conn.execute(sa.text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='articles' AND column_name='location_price'
        """))

    if result.fetchone():
        op.execute(sa.text("ALTER TABLE articles DROP COLUMN location_price"))
