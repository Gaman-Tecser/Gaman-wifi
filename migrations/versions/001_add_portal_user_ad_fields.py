"""Create gaman_ad_computer table.

Revision ID: 001_ad_computers
Revises:
Create Date: 2026-03-19
"""
from alembic import op
import sqlalchemy as sa

revision = '001_ad_computers'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'gaman_ad_computer',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sam_account_name', sa.String(255), unique=True, nullable=False),
        sa.Column('dns_hostname', sa.String(255), server_default=''),
        sa.Column('os', sa.String(255), server_default=''),
        sa.Column('ou', sa.String(500), server_default=''),
        sa.Column('description', sa.String(500), server_default=''),
        sa.Column('group_name', sa.String(80), sa.ForeignKey('gaman_wifi_group.group_name'), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('gaman_ad_computer')
