"""faz8_fashion_gender

Revision ID: e5f6a7b8c9d0
Revises: d44ca6ad98ee
Create Date: 2026-05-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e5f6a7b8c9d0'
down_revision = 'd44ca6ad98ee'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gender', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('gender')
