"""Add the job application pipeline."""

import sqlalchemy as sa
from alembic import op

revision = "20261009_01"
down_revision = "20260930_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company", sa.String(160), nullable=False),
        sa.Column("role_title", sa.String(160), nullable=False),
        sa.Column("posting_url", sa.String(500)),
        sa.Column("location", sa.String(160)),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("resume_version", sa.String(60)),
        sa.Column(
            "referral_contact_id",
            sa.Integer(),
            sa.ForeignKey("contacts.id", ondelete="SET NULL"),
        ),
        sa.Column("deadline", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="saved"),
        sa.Column("applied_at", sa.DateTime(timezone=True)),
        sa.Column("online_assessment_at", sa.DateTime(timezone=True)),
        sa.Column("interview_at", sa.DateTime(timezone=True)),
        sa.Column("offer_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_applications_owner_id", "job_applications", ["owner_id"])
    op.create_index("ix_job_applications_status", "job_applications", ["status"])
    op.create_index("ix_job_applications_company", "job_applications", ["company"])
    op.create_index(
        "ix_job_applications_referral_contact_id", "job_applications", ["referral_contact_id"]
    )


def downgrade() -> None:
    op.drop_table("job_applications")
