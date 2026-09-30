"""Add human-in-the-loop outreach drafts."""

from alembic import op
import sqlalchemy as sa

revision = "20260929_01"
down_revision = "20260928_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outreach_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_profile_id", sa.Integer(), sa.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("channel", sa.String(length=40), nullable=False),
        sa.Column("tone", sa.String(length=30), nullable=False),
        sa.Column("subject", sa.String(length=240)),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("user_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("copied_at", sa.DateTime(timezone=True)),
        sa.Column("sent_manually_at", sa.DateTime(timezone=True)),
        sa.Column("replied_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_outreach_drafts_status", "outreach_drafts", ["status"])
    op.create_index("ix_outreach_drafts_contact_id", "outreach_drafts", ["contact_id"])
    op.create_index("ix_outreach_drafts_student_profile_id", "outreach_drafts", ["student_profile_id"])


def downgrade() -> None:
    op.drop_table("outreach_drafts")
