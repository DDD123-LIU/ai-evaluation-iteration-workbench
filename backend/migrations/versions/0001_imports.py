"""三类CSV和资料版本初始结构，不建立后续任务表。"""
from alembic import op
import sqlalchemy as sa

revision = "0001_imports"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    for name, extra in (("dialogue_upload", []), ("material_version", [sa.Column("kind", sa.String(4), nullable=False)])):
        op.create_table(name,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("raw_csv", sa.LargeBinary(), nullable=False),
            sa.Column("filename", sa.Text(), nullable=False),
            sa.Column("uploaded_at", sa.String(40), nullable=False),
            sa.Column("row_count", sa.Integer(), nullable=False), *extra,
            sa.CheckConstraint("row_count BETWEEN 1 AND 100" if name == "dialogue_upload" else "row_count >= 1"),
            *([sa.CheckConstraint("kind IN ('rule', 'kb')")] if extra else []))
    op.create_table("case_record",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("upload_id", sa.String(36), sa.ForeignKey("dialogue_upload.id"), nullable=False),
        sa.Column("csv_case_id", sa.Text(), nullable=False),
        sa.Column("row_ordinal", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("original_reply", sa.Text(), nullable=False),
        sa.Column("chat_history", sa.Text(), nullable=False),
        sa.Column("H_json", sa.Text(), nullable=False),
        sa.UniqueConstraint("upload_id", "csv_case_id"),
        sa.UniqueConstraint("upload_id", "row_ordinal"), sa.CheckConstraint("row_ordinal >= 1"))
    for name in ("rule_row", "kb_row"):
        op.create_table(name,
            sa.Column("version_id", sa.String(36), sa.ForeignKey("material_version.id"), primary_key=True),
            sa.Column("source_id", sa.Text(), primary_key=True),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("row_ordinal", sa.Integer(), nullable=False),
            sa.UniqueConstraint("version_id", "row_ordinal"), sa.CheckConstraint("row_ordinal >= 1"))
    op.create_table("operation_commit",
        sa.Column("operation_id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("result_type", sa.String(20), nullable=False),
        sa.Column("result_id", sa.String(36), nullable=False),
        sa.Column("committed_at", sa.String(40), nullable=False))


def downgrade():
    for name in ("operation_commit", "kb_row", "rule_row", "case_record", "material_version", "dialogue_upload"):
        op.drop_table(name)
