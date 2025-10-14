"""add news model

Revision ID: 457dfefe41ba
Revises: a26dbd0f69aa
Create Date: 2025-10-14 15:59:55.449737

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '457dfefe41ba'
down_revision = 'a26dbd0f69aa'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if 'news' not in existing_tables:
        op.create_table(
            'news',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    if 'news' in set(inspector.get_table_names()):
        existing_indexes = {ix.get('name') for ix in inspector.get_indexes('news')}
        if 'ix_news_created_by' not in existing_indexes:
            op.create_index('ix_news_created_by', 'news', ['created_by'], unique=False)

    # Note: Removed unintended batch_alter on 'document' table to avoid SQLite default issues

    # ### end Alembic commands ###


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'news' in inspector.get_table_names():
        existing_indexes = {ix.get('name') for ix in inspector.get_indexes('news')}
        if 'ix_news_created_by' in existing_indexes:
            op.drop_index('ix_news_created_by', table_name='news')
        op.drop_table('news')
    # ### end Alembic commands ###
