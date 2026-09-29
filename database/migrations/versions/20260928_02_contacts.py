"""Create compliant contact directory table."""

from alembic import op
import sqlalchemy as sa

revision = "20260928_02"
down_revision = "20260928_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("current_role", sa.String(length=160)),
        sa.Column("company", sa.String(length=160)),
        sa.Column("industry", sa.String(length=160)),
        sa.Column("location", sa.String(length=160)),
        sa.Column("school", sa.String(length=160)),
        sa.Column("skills_summary", sa.Text()),
        sa.Column("profile_url", sa.String(length=500)),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_name", sa.String(length=160), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for field in ("current_role", "company", "industry", "location", "school"):
        op.create_index(f"ix_contacts_{field}", "contacts", [field])


def downgrade() -> None:
    op.drop_table("contacts")
