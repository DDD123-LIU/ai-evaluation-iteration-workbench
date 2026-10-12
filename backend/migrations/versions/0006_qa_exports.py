"""014仅新增不可变导出与原操作回执，保留旧草稿/历史。"""
from alembic import op
revision = '0006_qa_exports'
down_revision = '0005_qa_generation'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''CREATE TABLE export_event (id VARCHAR(36) PRIMARY KEY, operation_id VARCHAR(36) NOT NULL UNIQUE,
    created_at VARCHAR(40) NOT NULL, csv_bytes BLOB NOT NULL, byte_length INTEGER NOT NULL CHECK(byte_length>0), content_hash VARCHAR(64) NOT NULL)''')
    op.execute('''CREATE TABLE export_item (id VARCHAR(36) PRIMARY KEY, event_id VARCHAR(36) NOT NULL REFERENCES export_event(id),
    ordinal INTEGER NOT NULL, qa_id VARCHAR(36) NOT NULL REFERENCES qa(id), qa_revision INTEGER NOT NULL,
    case_id VARCHAR(36) NOT NULL REFERENCES case_record(id), source_batch_id VARCHAR(36) NOT NULL REFERENCES task(id),
    question TEXT NOT NULL, answer TEXT NOT NULL, source_case_number TEXT NOT NULL, category TEXT NOT NULL,
    UNIQUE(event_id,ordinal), UNIQUE(event_id,qa_id), CHECK(ordinal>=1 AND qa_revision>=0))''')
    op.execute('''CREATE TABLE qa_write_receipt (operation_id VARCHAR(36) PRIMARY KEY REFERENCES operation_commit(operation_id), result_json TEXT NOT NULL)''')


def downgrade():
    op.drop_table('qa_write_receipt')
    op.drop_table('export_item')
    op.drop_table('export_event')
