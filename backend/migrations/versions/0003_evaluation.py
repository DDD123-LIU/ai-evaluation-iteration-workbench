"""011 E07/E08/E09增量快照；不重建既有008/009表。"""
from alembic import op

revision='0003_evaluation'
down_revision='0002_execution'
branch_labels=None
depends_on=None


def upgrade():
    op.execute('''CREATE TABLE evaluation_result (
        item_id VARCHAR(36) PRIMARY KEY REFERENCES execution_item(id) ON DELETE CASCADE,
        contract_json TEXT NOT NULL, accuracy INTEGER NOT NULL, intent INTEGER NOT NULL, service INTEGER NOT NULL,
        accuracy_reason TEXT NOT NULL, intent_reason TEXT NOT NULL, service_reason TEXT NOT NULL,
        primary_cause TEXT, secondary_json TEXT NOT NULL, has_material_conflict INTEGER NOT NULL,
        CHECK(accuracy BETWEEN 1 AND 5 AND intent BETWEEN 1 AND 5 AND service BETWEEN 1 AND 5),
        CHECK(has_material_conflict IN (0,1)))''')
    op.execute('''CREATE TABLE gap (
        id VARCHAR(36) PRIMARY KEY, result_item_id VARCHAR(36) NOT NULL REFERENCES evaluation_result(item_id) ON DELETE CASCADE,
        gap_ordinal INTEGER NOT NULL CHECK(gap_ordinal>=1), gap_text TEXT NOT NULL, snippet TEXT NOT NULL,
        reason TEXT NOT NULL, location_json TEXT NOT NULL, UNIQUE(result_item_id,gap_ordinal))''')
    op.execute('''CREATE TABLE final_error (
        item_id VARCHAR(36) PRIMARY KEY REFERENCES execution_item(id) ON DELETE CASCADE,
        category VARCHAR(24) NOT NULL CHECK(category IN ('CALL_ERROR','PARSE_ERROR','INCOMPLETE_RESULT')),
        last_attempt_id VARCHAR(36) REFERENCES attempt(id))''')


def downgrade():
    # Alembic显式降级只用于明确操作；本任务仅在空业务表的隔离测试库验证。
    op.drop_table('final_error')
    op.drop_table('gap')
    op.drop_table('evaluation_result')
