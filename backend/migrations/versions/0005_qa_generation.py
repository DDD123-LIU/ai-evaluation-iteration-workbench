"""013 Q成功草稿增量迁移，旧评测/指标/尝试表不改。"""
from alembic import op
revision='0005_qa_generation'
down_revision='0004_batch_metrics'
branch_labels=None
depends_on=None


def upgrade():
    op.execute('''CREATE TABLE qa (id VARCHAR(36) PRIMARY KEY, q_item_id VARCHAR(36) NOT NULL UNIQUE REFERENCES execution_item(id) ON DELETE CASCADE,
    gap_id VARCHAR(36) NOT NULL UNIQUE REFERENCES gap(id), original_question TEXT NOT NULL, question TEXT NOT NULL,
    answer TEXT NOT NULL, category TEXT NOT NULL, review_state VARCHAR(20) NOT NULL CHECK(review_state IN ('pending_review','approved')),
    revision INTEGER NOT NULL CHECK(revision>=0))''')


def downgrade():
    op.drop_table('qa')
