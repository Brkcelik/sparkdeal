"""add currency field to products

Revision ID: a1b2c3d4e5f6
Revises: 596c80bd6f18
Create Date: 2026-05-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '596c80bd6f18'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(10), nullable=True, server_default='TRY'))


def downgrade():
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_column('currency')
