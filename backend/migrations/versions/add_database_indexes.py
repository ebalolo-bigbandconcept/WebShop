"""Add database indexes for frequently queried columns

Revision ID: add_database_indexes
Revises: b132ac0e32d5
Create Date: 2025-01-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_database_indexes'
down_revision = 'b132ac0e32d5'
branch_labels = None
depends_on = None


def upgrade():
    # Add index on user email for fast lookups during login/registration
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index('ix_user_email', ['email'])
    
    # Add index on Devis client_id for fast filtering by client
    with op.batch_alter_table('devis', schema=None) as batch_op:
        batch_op.create_index('ix_devis_client_id', ['client_id'])
    
    # Add index on DevisArticles devis_id for fast filtering by devis
    with op.batch_alter_table('devis_articles', schema=None) as batch_op:
        batch_op.create_index('ix_devis_articles_devis_id', ['devis_id'])
    
    # Add index on Client email for fast lookups
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.create_index('ix_client_email', ['email'])


def downgrade():
    # Remove indexes
    with op.batch_alter_table('devis_articles', schema=None) as batch_op:
        batch_op.drop_index('ix_devis_articles_devis_id')
    
    with op.batch_alter_table('devis', schema=None) as batch_op:
        batch_op.drop_index('ix_devis_client_id')
    
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.drop_index('ix_client_email')
    
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_user_email')
