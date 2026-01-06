"""add remise field to devis

Revision ID: c4b04e2d5f21
Revises: 59f7b4e441da
Create Date: 2026-01-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4b04e2d5f21'
down_revision = '59f7b4e441da'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('devis', sa.Column('remise', sa.Float(), nullable=False, server_default='0'))
    op.alter_column('devis', 'remise', server_default=None)


def downgrade():
    op.drop_column('devis', 'remise')
