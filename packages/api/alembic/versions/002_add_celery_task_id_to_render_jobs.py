"""Add celery_task_id to render_jobs.

Revision ID: 002
Revises: 001
Create Date: 2026-03-10
"""

import sqlalchemy as sa

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "render_jobs",
        sa.Column("celery_task_id", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("render_jobs", "celery_task_id")
