"""012普通评测终态汇总增量迁移，不改旧表及评分字段。"""
from alembic import op
revision='0004_batch_metrics'
down_revision='0003_evaluation'
branch_labels=None
depends_on=None


def upgrade():
    op.execute('CREATE TABLE batch_summary (task_id VARCHAR(36) PRIMARY KEY REFERENCES task(id) ON DELETE CASCADE, payload_json TEXT NOT NULL)')


def downgrade():
    op.drop_table('batch_summary')
