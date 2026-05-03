"""faz9_itad_external_price_history

Revision ID: a7b8c9d0e1f2
Revises: 99785c1fd000
Create Date: 2026-05-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a7b8c9d0e1f2'
down_revision = '99785c1fd000'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'external_price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('shop', sa.String(length=50), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('regular_price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('cut', sa.Integer(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_external_price_history_product_id', 'external_price_history', ['product_id'])


def downgrade():
    op.drop_index('ix_external_price_history_product_id', table_name='external_price_history')
    op.drop_table('external_price_history')
