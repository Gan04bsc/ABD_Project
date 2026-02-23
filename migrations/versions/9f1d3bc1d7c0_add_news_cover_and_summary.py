"""add news cover image and summary

Revision ID: 9f1d3bc1d7c0
Revises: 457dfefe41ba
Create Date: 2026-02-23 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "9f1d3bc1d7c0"
down_revision = "457dfefe41ba"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    tables = set(inspector.get_table_names())
    if "news" not in tables:
        return

    columns = {c["name"] for c in inspector.get_columns("news")}
    with op.batch_alter_table("news", schema=None) as batch_op:
        if "summary" not in columns:
            batch_op.add_column(sa.Column("summary", sa.Text(), nullable=False, server_default=""))
        if "cover_image" not in columns:
            batch_op.add_column(sa.Column("cover_image", sa.String(length=1024), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    tables = set(inspector.get_table_names())
    if "news" not in tables:
        return

    columns = {c["name"] for c in inspector.get_columns("news")}
    with op.batch_alter_table("news", schema=None) as batch_op:
        if "cover_image" in columns:
            batch_op.drop_column("cover_image")
        if "summary" in columns:
            batch_op.drop_column("summary")
